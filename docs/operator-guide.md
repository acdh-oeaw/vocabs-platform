# Operator guide: add or migrate a vocabulary

Run these commands from a current checkout of this repository. They target the
**development** release below. Use a separate, reviewed environment file and
release name for any other namespace. You need Helm, kubectl, Python with
`scripts/requirements.txt`, Apache Jena `riot`, and permission to create Pods,
Jobs, ConfigMaps and PVCs. An administrator must provision the shared RDF source
PVC and a maintainer must supply a **complete** accepted RDF baseline. The new
vocabulary definition is Turtle, not Kubernetes YAML; ask the vocabulary owner
for its reviewed URI, graph, languages and configuration fragment.

Run each command in order and stop on any error. Change the variables in the
first block to your reviewed values and local files. Commands that change the
cluster are called out explicitly. The generated YAML stays under
`operator-work/`, which Git ignores. Never run an activation merely because an
import Job reports `Complete`: a reviewer must check graph counts, search and
the new vocabulary before the maintenance window.

## 1. Select the release and check the current state (read-only)

Use a new revision and claim for every attempt. The example assumes `r006` is
currently active and a **complete** previous dataset is available as a local
N-Quads file. The new RDF file should be TriG or N-Quads when it has named graphs.

```bash
export NS=vocabs-platform-dev
export RELEASE=vocabs-platform-dev
export VALUES=environments/vocabs-platform-dev.yaml
export REV=r007
export CLAIM=vocabs-data-r007
export SOURCE_CLAIM=vocabs-import
export BASELINE=/absolute/path/all-accepted-r006.nq
export NEW_RDF=/absolute/path/new-vocabulary.trig
export VOCAB_TTL=/absolute/path/new-vocabulary.ttl
export CONFIGMAP="${RELEASE}-vocabs-skosmos-config-${REV}"
export WORK="operator-work/${REV}"

helm list -n "$NS"
helm get values "$RELEASE" -n "$NS" -o yaml
kubectl -n "$NS" get statefulset,deployments,pvc,jobs
test "$(kubectl -n "$NS" get "statefulset/${RELEASE}-vocabs-fuseki" -o jsonpath='{.spec.template.spec.volumes[?(@.name=="database")].persistentVolumeClaim.claimName}')" = "$(python3 -c 'import sys,yaml; print(yaml.safe_load(open(sys.argv[1]))["data"]["activeClaim"])' "$VALUES")"
test "$(kubectl -n "$NS" get "deployment/${RELEASE}-vocabs-skosmos" -o jsonpath='{.spec.template.spec.volumes[?(@.name=="config")].configMap.name}')" = "$(python3 -c 'import sys,yaml; print(yaml.safe_load(open(sys.argv[1]))["skosmos"]["config"]["existingConfigMap"])' "$VALUES")"
kubectl -n "$NS" get configmap "$(python3 -c 'import sys,yaml; print(yaml.safe_load(open(sys.argv[1]))["skosmos"]["config"]["existingConfigMap"])' "$VALUES")"
test -s "$BASELINE" && test -s "$NEW_RDF" && test -s "$VOCAB_TTL"
sha256sum "$BASELINE" "$NEW_RDF"
```

Compare the printed live Helm values and chart version with the checkout and
`$VALUES`; ask a maintainer to reconcile any other live overrides before an
upgrade. Stop if the live active claim, release or ConfigMap differs from `$VALUES`, if
the baseline omits a previously accepted vocabulary, or if the new fragment has
not been reviewed. For a first migration from another platform, follow the
[initial migration checks](#initial-migration-from-another-platform) to obtain
a complete baseline. Do not copy TDB database directories between engines.

## 2. Generate the plan locally (no cluster changes)

The helper copies the environment values, appends a retained candidate PVC,
and creates separate files for the import, maintenance window and activation.
It refuses to overwrite an existing plan. `--complete-source-set` is an explicit
acknowledgement that **both** source files together contain every vocabulary
that must remain available after activation.

```bash
python3 scripts/operator-plan.py prepare \
  --values "$VALUES" --revision "$REV" --claim "$CLAIM" \
  --source-claim "$SOURCE_CLAIM" \
  --source "/data/$(basename "$BASELINE")" \
  --source "/data/$(basename "$NEW_RDF")" \
  --complete-source-set --job-name "candidate-${REV}" \
  --config-map "$CONFIGMAP" --config-revision "$REV" \
  --output "$WORK"

ls -lh "$WORK"
python3 - "$WORK" <<'PY'
import pathlib, sys, yaml
p = pathlib.Path(sys.argv[1])
for name in sorted(p.glob('[0-9]*.yaml')):
    v = yaml.safe_load(name.read_text())
    print(name.name, 'active=', v.get('data', {}).get('activeClaim'),
          'candidate=', v.get('imports', {}).get('targetClaim'),
          'sources=', v.get('imports', {}).get('source', {}).get('pvc', {}).get('files'))
PY
```

Check that the `01` file still names the **old** active claim, the `04` and `05`
files name the **new** claim, and the import overlay lists every source file.
If the plan is wrong, use a fresh revision; do not reuse a partially imported
candidate or a completed Job name.

## 3. Copy RDF onto the shared source PVC (cluster changes)

The generated temporary staging Pod mounts only `$SOURCE_CLAIM`. Its image
must be pullable by the namespace. Compare hashes after each copy, then delete
the staging Pod before starting the import.

```bash
kubectl -n "$NS" get pvc "$SOURCE_CLAIM"
kubectl -n "$NS" create -f "$WORK/staging-pod.yaml"
kubectl -n "$NS" wait --for=condition=Ready "pod/rdf-stage-${REV}" --timeout=5m
kubectl -n "$NS" cp "$BASELINE" "rdf-stage-${REV}:/data/$(basename "$BASELINE")"
kubectl -n "$NS" cp "$NEW_RDF" "rdf-stage-${REV}:/data/$(basename "$NEW_RDF")"
kubectl -n "$NS" exec "rdf-stage-${REV}" -- sha256sum \
  "/data/$(basename "$BASELINE")" "/data/$(basename "$NEW_RDF")"
kubectl -n "$NS" delete "pod/rdf-stage-${REV}" --wait=true
```

The remote hashes must match those from step 1. `kubectl cp` can take a long
time for a large baseline; check available PVC capacity first. If the file is
already on the source PVC, inspect it with the staging Pod instead of copying it.

## 4. Create the candidate and run the offline import (cluster changes)

This upgrade creates the new PVC while keeping the old claim active. The Job
is rendered and created separately; **do not install the import overlay with
`helm upgrade`**.

```bash
helm lint ./chart/vocabs -f "$WORK/01-candidate-values.yaml"
helm upgrade "$RELEASE" ./chart/vocabs -n "$NS" \
  -f "$WORK/01-candidate-values.yaml" --wait --timeout=10m
kubectl -n "$NS" get pvc "$CLAIM"

helm template "$RELEASE" ./chart/vocabs -n "$NS" \
  -f "$WORK/01-candidate-values.yaml" -f "$WORK/02-import-overlay.yaml" \
  --show-only templates/import-job.yaml > "$WORK/import-job.yaml"
python3 - "$WORK/import-job.yaml" "$CLAIM" <<'PY'
import sys, yaml
j = yaml.safe_load(open(sys.argv[1]))
volumes = j['spec']['template']['spec']['volumes']
assert next(v for v in volumes if v['name'] == 'target')['persistentVolumeClaim']['claimName'] == sys.argv[2]
print('Job:', j['metadata']['name'], 'target:', sys.argv[2])
PY
kubectl -n "$NS" create -f "$WORK/import-job.yaml"
kubectl -n "$NS" logs -f "job/${RELEASE}-vocabs-candidate-${REV}" -c import
kubectl -n "$NS" wait --for=condition=complete \
  "job/${RELEASE}-vocabs-candidate-${REV}" --timeout=120m
```

If the Job fails, use [troubleshooting](#troubleshooting) and **prepare a new
claim and revision**. A partial TDB directory must never be reused.

## 5. Validate the candidate and create the new configuration

The validator is built from the chart's actual Fuseki StatefulSet template, but
mounts only the **candidate** claim. Its component label is changed so the live
Fuseki Service cannot select it. It must exit before activation.

```bash
helm template "$RELEASE" ./chart/vocabs -n "$NS" \
  -f "$WORK/01-candidate-values.yaml" \
  --show-only templates/fuseki-statefulset.yaml > "$WORK/fuseki.yaml"
python3 scripts/operator-plan.py validator \
  --rendered "$WORK/fuseki.yaml" --claim "$CLAIM" \
  --name "candidate-validator-${REV}" --output "$WORK/validator-pod.yaml"
kubectl -n "$NS" create -f "$WORK/validator-pod.yaml"
kubectl -n "$NS" wait --for=condition=Ready \
  "pod/candidate-validator-${REV}" --timeout=10m
kubectl -n "$NS" port-forward "pod/candidate-validator-${REV}" 13030:3030 \
  > "$WORK/validator-port-forward.log" 2>&1 &
export VALIDATOR_FORWARD_PID=$!
```

Run the next read-only queries in the same shell. Check the expected graph
count, named graph URIs and representative labels against the supplied baseline.
The physical default graph is queried separately. An empty result or only an
HTTP 200 response is not enough to accept the candidate.

```bash
curl --retry 10 --retry-delay 1 --retry-connrefused -fsSG \
  -H 'Accept: application/sparql-results+json' \
  --data-urlencode 'query=SELECT (COUNT(*) AS ?n) WHERE { GRAPH ?g { ?s ?p ?o } }' \
  http://127.0.0.1:13030/skosmos/sparql | python3 -m json.tool
curl -fsSG -H 'Accept: application/sparql-results+json' \
  --data-urlencode 'query=SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } } ORDER BY ?g' \
  http://127.0.0.1:13030/skosmos/sparql | python3 -m json.tool
curl -fsSG -H 'Accept: application/sparql-results+json' \
  --data-urlencode 'query=SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }' \
  http://127.0.0.1:13030/skosmos/sparql | python3 -m json.tool
kill "$VALIDATOR_FORWARD_PID"
kubectl -n "$NS" delete "pod/candidate-validator-${REV}" --wait=true
```

Create a new revisioned Skosmos ConfigMap by extending the **current** accepted
configuration with the reviewed vocabulary Turtle fragment. This is not a YAML
editing step. Check the fragment's `skosmos:sparqlGraph` against the graphs above
and preserve branding, languages, JenaText settings and the Vinyl Cache endpoint.

```bash
export CURRENT_CONFIG="$(python3 -c 'import sys,yaml; print(yaml.safe_load(open(sys.argv[1]))["skosmos"]["config"]["existingConfigMap"])' "$VALUES")"
kubectl -n "$NS" get configmap "$CURRENT_CONFIG" \
  -o jsonpath='{.data.config\.ttl}' > "$WORK/current-config.ttl"
{ cat "$WORK/current-config.ttl"; printf '\n'; cat "$VOCAB_TTL"; } \
  > "$WORK/next-config.ttl"
riot --validate --syntax=TURTLE "$WORK/next-config.ttl"
.venv/bin/python scripts/skosmos-public-url.py \
  --values "$VALUES" --config "$WORK/next-config.ttl"
kubectl -n "$NS" create configmap "$CONFIGMAP" \
  --from-file="config.ttl=$WORK/next-config.ttl" --dry-run=client \
  -o yaml > "$WORK/configmap.yaml"
kubectl -n "$NS" create -f "$WORK/configmap.yaml"
```

Stop here for a second person to review the graph results and the proposed
configuration. A new vocabulary needs application/search checks during the
maintenance window; initial migrations also need URI and redirect checks.

## 6. Activate during a planned maintenance window (cluster changes)

These three upgrades first close the public application and API ingresses, then
switch the active PVC and Skosmos ConfigMap, then reopen traffic **only after**
the internal checks pass. The downloads Ingress remains independent. The
administrative Fuseki Ingress remains available to authorized operators.

```bash
helm lint ./chart/vocabs -f "$WORK/03-pause-values.yaml"
helm lint ./chart/vocabs -f "$WORK/04-switch-values.yaml"
helm upgrade "$RELEASE" ./chart/vocabs -n "$NS" \
  -f "$WORK/03-pause-values.yaml" --wait --timeout=10m
kubectl -n "$NS" get ingress
kubectl -n "$NS" get pods -l app.kubernetes.io/component=import
kubectl -n "$NS" get pods -l app.kubernetes.io/component=candidate-validator
```

Stop if the last command lists a validator Pod, if the importer is still
running, or if the public gateway/API Ingress still exists. Only then switch:

```bash
helm upgrade "$RELEASE" ./chart/vocabs -n "$NS" \
  -f "$WORK/04-switch-values.yaml" --wait --timeout=10m
kubectl -n "$NS" rollout status "statefulset/${RELEASE}-vocabs-fuseki" --timeout=10m
kubectl -n "$NS" rollout status "deployment/${RELEASE}-vocabs-vinyl" --timeout=10m
kubectl -n "$NS" rollout restart "deployment/${RELEASE}-vocabs-vinyl"
kubectl -n "$NS" rollout status "deployment/${RELEASE}-vocabs-vinyl" --timeout=10m
kubectl -n "$NS" rollout status "deployment/${RELEASE}-vocabs-skosmos" --timeout=10m
kubectl -n "$NS" port-forward "service/${RELEASE}-vocabs-skosmos" 18080:80 \
  > "$WORK/skosmos-port-forward.log" 2>&1 &
export SKOSMOS_FORWARD_PID=$!
curl --retry 10 --retry-delay 1 --retry-connrefused -fsSL \
  http://127.0.0.1:18080/en/ > "$WORK/skosmos-page.html"
kill "$SKOSMOS_FORWARD_PID"
```

Confirm the new vocabulary page, a representative concept, search (including
alternative labels), and graph/query results with the reviewer while traffic
is still paused. If any check fails, follow [rollback](#rollback) **before**
reopening public traffic. If they pass:

```bash
helm upgrade "$RELEASE" ./chart/vocabs -n "$NS" \
  -f "$WORK/05-active-values.yaml" --wait --timeout=10m
curl -fsSL "$(python3 -c 'import sys,yaml; print(yaml.safe_load(open(sys.argv[1]))["global"]["publicUrl"])' "$VALUES")en/" \
  > "$WORK/public-page.html"
kubectl -n "$NS" get pvc "$CLAIM"
```

Ask a maintainer to copy the reviewed `05-active-values.yaml` into the tracked
environment configuration through a PR. Keep the old PVC, source checksums and
this plan for rollback. Do not delete any retained claims during activation.

## Rollback

Keep the public ingresses closed until the old claim and configuration are back.
The generated `03` file refers to the original claim. The tracked `$VALUES`
file must still be the previously accepted release values; if it has changed,
have a maintainer recover the exact previous values from the release history.

```bash
helm upgrade "$RELEASE" ./chart/vocabs -n "$NS" \
  -f "$WORK/03-pause-values.yaml" --wait --timeout=10m
kubectl -n "$NS" rollout status "statefulset/${RELEASE}-vocabs-fuseki" --timeout=10m
kubectl -n "$NS" rollout status "deployment/${RELEASE}-vocabs-vinyl" --timeout=10m
helm upgrade "$RELEASE" ./chart/vocabs -n "$NS" -f "$VALUES" --wait --timeout=10m
```

## Initial migration from another platform

An initial migration needs a **complete RDF export**, graph URI inventory, a
reviewed Skosmos configuration and a compatible stack profile. The old system's
dataset URL and credentials are environment-specific; a platform maintainer must
verify them. The historical `vocabs-main` export is recorded in
[migration.md](migration.md). This example reads from the old Fuseki Pod; replace
the two values after checking the old cluster and export format. The result
becomes `$BASELINE` for step 1. Do not mix this with database-directory copies.

```bash
export OLD_NS=vocabs-prod
export OLD_POD=REPLACE_WITH_OLD_FUSEKI_POD
export OLD_DATASET=vocabs-main
export BASELINE=/absolute/path/all-accepted-from-old.nq
kubectl -n "$OLD_NS" get pods
kubectl -n "$OLD_NS" exec "$OLD_POD" -- \
  curl -fsS -H 'Accept: application/n-quads' \
  "http://127.0.0.1:3030/${OLD_DATASET}/" > "$BASELINE"
test -s "$BASELINE"
riot --validate --syntax=NQUADS "$BASELINE"
wc -l "$BASELINE"
sha256sum "$BASELINE"
```

Compare graph URIs, counts, vocabulary definitions and known queries with the
source service. If the legacy RDF requires a validation exception or a different
TDB engine, stop and involve the maintainer; do not bypass validation in a
routine operator run. Follow steps 2–6 with a fresh candidate only after the
full source set and configuration have been reviewed.

## Troubleshooting (read-only)

Each command below only inspects state. Replace the variables from step 1.

| Symptom | Command | What to inspect |
| --- | --- | --- |
| Helm upgrade failed | `helm status "$RELEASE" -n "$NS"` | Release revision and status; do not start another activation blindly. |
| Pod not ready | `kubectl -n "$NS" get pods -o wide` | Pending, ImagePullBackOff, OOMKilled or restarts. |
| Why a Pod failed | `kubectl -n "$NS" describe pod POD_NAME` | Events at the bottom; replace `POD_NAME` from the previous command. |
| Import failed | `kubectl -n "$NS" logs "job/${RELEASE}-vocabs-candidate-${REV}" -c import` | Missing source, insufficient storage, RDF syntax, loader or index errors. Use a new claim/revision for retry. |
| PVC pending | `kubectl -n "$NS" describe pvc "$CLAIM"` | StorageClass, quota and CSI provisioning events. |
| Fuseki unavailable | `kubectl -n "$NS" logs "statefulset/${RELEASE}-vocabs-fuseki" -c fuseki --tail=100` | Startup/configuration errors; do not delete lock files or force-delete Pods. |
| Website unavailable | `kubectl -n "$NS" get ingress,services,endpoints` | Ingress host, TLS and backend endpoints. |
| Downloads unavailable | `kubectl -n "$NS" get deployment,service,ingress | grep downloads` | Pod availability, host and Service; test a real dump path, not `/`. |

For authentication and administrator endpoints see
[admin-endpoints.md](admin-endpoints.md). For retention and restore see
[storage.md](storage.md) and [backup-and-restore.md](backup-and-restore.md).
