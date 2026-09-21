# ACDH Vocabs platform

A Kubernetes/Helm foundation for namespace-specific ACDH vocabulary services.
**Development scaffold, not yet production certified.** Validate images, TDB1,
JenaText and real ACDH vocabularies before routing production traffic. The MIT
license is preserved. No production infrastructure or credentials are included.

```text
Internet → Ingress → Anubis → nginx-unprivileged → Skosmos → Varnish → Fuseki
                                                               (one JVM)
                                                                  ↓
                                                        active revision PVC
Shared RDF source PVC → explicit offline import Job → separate candidate PVC
```

Varnish uses the [official Varnish Cache chart](https://github.com/varnish/helm-varnish/tree/main/varnish-cache),
pinned to 0.1.3 in Chart.yaml and Chart.lock. Fuseki and Varnish are ClusterIP only;
only the gateway receives the application ingress. Separate Swagger ingress
requires an explicit Anubis-bypass acknowledgement. NetworkPolicies default to
restricting backend ingress. A CNI must enforce them; without enforcement they
have no effect. This chart does not assume ingress-controller labels or install a CNI.

## Versioned stack

Select `stack.version: "2026.09.0-dev"`. The compatibility registry resolves
Skosmos 3.3 and Jena 5.4.0 with a shared image revision. It rejects unknown profiles,
independent runtime/importer tags, and unsupported overrides. The initial TDB1
profile is a candidate: upstream Skosmos 3.3 uses the same Jena version but a TDB2
assembler. There is **no ACDH-tested production profile yet**. See
[stack versioning](docs/stack-versioning.md) and [upstream evidence](docs/upstream-verification.md).

## Layout

- `chart/vocabs`: chart, compatibility profiles, validation schema, examples.
- `images`: thin Skosmos branding image, separate Fuseki and Jena tools images.
- `branding`: ACDH-owned templates, plugins, CSS and images; no fork of Skosmos.
- `config`: modular vocabulary, assembler and Anubis policy examples.
- `environments`: per-namespace values, with clearly marked placeholders.
- `scripts`, `tests`: rendering, safety, Turtle and Kubernetes schema validation.
- `docs`: import, storage, migration, versioning and backup procedures.

## Prerequisites and local validation

Use Helm 3.17.3+ (also validated with Helm 4.3.0), Python 3.11+, Node.js 18+, Bash, and
kubeconform 0.6.7. Install the official Helm release for your OS from
[Helm releases](https://github.com/helm/helm/releases); install kubeconform from
[its release](https://github.com/yannh/kubeconform/releases/tag/v0.6.7), verify
CHECKSUMS, and place the executable on PATH. This also works in Codespaces.
CI installs Helm, kubeconform and Python dependencies, uses the runner’s Node.js,
and never connects to a Kubernetes cluster.

```bash
python3 -m venv .venv
.venv/bin/pip install -r scripts/requirements.txt
make deps
make lint
make template
make test PYTHON=.venv/bin/python
make validate PYTHON=.venv/bin/python
```

`make validate` requires kubeconform and network access to its Kubernetes schema
repository; missing tools or errors fail validation. RDFLib checks Turtle syntax
separately from Kubernetes manifests. Real imports and configuration generation
use Jena RIOT; missing RIOT is an error, not a silently skipped step.

Public OCI dependency pulls normally require no login. Docker Hub rate limits may
require `helm registry login registry-1.docker.io` using credentials supplied
outside Git. Do not replace the pinned chart with an unverified chart mirror.

## Environment setup

Copy `environments/example.yaml` to a namespace-specific values file. Set
`global.publicUrl` (absolute HTTP/HTTPS root URL with trailing `/`), the data and
gateway StorageClasses, ingress class if needed, existing TLS Secret, RDF source
PVC, active/candidate claims, resources and validated Skosmos ConfigMap. Supply
`networkPolicy.gatewayIngressPeers`
matching your ingress controller; empty peers deny gateway access. Empty
StorageClass uses the cluster default; see [storage](docs/storage.md).

Build and publish all three ACDH images before installing: the chart's `*-r1`
tags are **build targets, not a claim that registry images already exist**.
Select a verified Debian/Ubuntu Java 21 JDK base pinned by digest, then:

```bash
make images PYTHON=.venv/bin/python JAVA_BASE_IMAGE='YOUR-JAVA21-IMAGE@sha256:YOUR-DIGEST'
# Review/scan and explicitly push the built tags to your registry.
helm upgrade --install vocabs ./chart/vocabs \
  --namespace YOUR-NAMESPACE --create-namespace \
  -f environments/YOUR-ENVIRONMENT.yaml
```

Each namespace has an independent public URL, config, data revisions, claims and
resources. The default release produces `vocabs-vocabs-fuseki` and
`vocabs-varnish` service names. Name overrides require setting
`global.vocabsFusekiHost` to the generated Fuseki name. External Skosmos TTL must
point to that release's **Varnish** service, not directly to Fuseki.

## Public gateway

The chart owns Ingress → Anubis → localhost nginx-unprivileged → Skosmos → Varnish
→ Fuseki. It uses one gateway Deployment with two containers; only Anubis is
exposed by the Gateway Service. No Anubis Operator, CRDs, Redis or Valkey is
installed. Anubis handles request filtering; Nginx handles concept URI/DARIAH
redirects, CORS, routing and proxy headers. TLS stays at Ingress.

`global.publicUrl` supplies the ingress host, canonical redirects, public scheme,
Anubis URL and generated Skosmos baseHref. External ConfigMaps must pass the
provided URL validator before deployment. Public ingress requires
`gateway.anubis.signingKey.secret`; the development profile creates the
persistent signing Secret automatically, while external installations can use
`create: false` with `existingSecret`. Backend-only rendering requires no key.
Anubis redirect domains retain any public URL port; Ingress hosts do not.
Generic defaults disable the gateway
so URL-free backend rendering still works; the environment example enables it.

Anubis **v1.27.0** uses local bbolt storage on its own retained PVC by default.
The gateway is restricted to **one replica**, with Recreate updates and a short
availability gap. Nginx **1.30.5-alpine** includes njs for correct URI encoding.
The initial policy preserves machine/API/RDF access before browser challenges;
it requires application-specific acceptance testing before production.
See [the gateway runbook](docs/gateway.md) for redirects, CORS, proxy trust,
external policies, signing-key Secret references and pilot requirements.

## Operations

Fuseki uses a StatefulSet with one replica and an explicit active PVC. Jena/TDB
must have one JVM owning its database; RWO storage alone does not enforce this.
Updates wait for the old pod to exit normally before starting its replacement.
The Java entrypoint uses `exec`, with a 120-second shutdown grace period. Never
remove TDB lock files or force-delete a pod whose JVM may still be writing.

Prefer RBD block storage for active and candidate databases, and CephFS for an
optional shared, read-only RDF import source. Actual StorageClass names come
from each environment. [Storage documentation](docs/storage.md) explains retention.

Add a vocabulary by adding a modular Turtle fragment, validating the combined
configuration, and creating a ConfigMap with `scripts/configmap.sh` using the
environment values as its first argument. It adds baseHref from `global.publicUrl`
and rejects conflicts. Update
`skosmos.config.revision` when changing an external ConfigMap. See
[configuration](config/skosmos/README.md).

Update RDF by importing into a new candidate PVC while the active service runs.
Validate the candidate, stop public traffic briefly, activate it through the
StatefulSet rollout, and invalidate Varnish through its revision annotation.
Keep the previous PVC for rollback. Follow [the import runbook](docs/imports.md):
**imports are disabled by default and are never Helm hooks**. Use an explicitly
rendered Job with `kubectl create` so later Helm upgrades cannot recreate it.

Upgrade Skosmos by choosing a new reviewed stack profile, rebuilding the thin
branding image, testing in staging, and then changing `stack.version`. Jena
changes additionally require a fresh import, index and compatibility tests; do
not assume arbitrary Skosmos/Jena combinations work. See
[the compatibility test checklist](tests/integration/README.md).

Velero remains the cluster backup/DR system; blue/green PVCs provide operational
rollback and RDF dumps provide portable rebuilds. See [backup and restore](docs/backup-and-restore.md).
Migrate [one namespace at a time](docs/migration.md).

## Remaining production gates

Build/run/scan the images; verify the upstream Skosmos registry tag against its
source and pin its digest; supply a verified Java base; migrate ACDH themes and
plugins; validate TDB1 and JenaText results on actual vocabularies; tune probes,
heap and memory; test the real gateway/Skosmos path, browser challenges, RDF negotiation,
CORS and client IP attribution; test termination, candidate activation, rollback and Velero
restore on real storage. This foundation does not claim those tests have passed.

## Secret scanning

CI scans all fetched Git history on every push and pull request with Gitleaks
8.30.1, a checksum-verified binary, and a commit-pinned checkout action. It uses
only `contents: read`, does not persist checkout credentials, redacts detected
values, and does not upload reports. Findings fail the job.

For local scanning, install Gitleaks 8.21 or newer (the minimum for this config's
rule allowlist syntax), then run from the repository root:

```bash
gitleaks git --redact --log-opts="--all" --config .gitleaks.toml .
python3 tests/test_gitleaks.py
```

The equivalent legacy command remains supported by compatible versions:

```bash
gitleaks detect --source . --redact --log-opts="--all" --config .gitleaks.toml
```

History scanning covers locally available refs; fetch full history first when
using a shallow clone. To check uncommitted files too, use
`gitleaks dir --redact --config .gitleaks.toml .`.

The config extends all default rules. Its only added exception applies to
`generic-api-key` when the extracted value is exactly `ed25519-private-key-hex`
**and** the path is exactly `chart/vocabs/values.yaml` or
`tests/gateway/test_gateway.py`. This is a Kubernetes Secret field name, not key
material. Tests generate temporary synthetic secrets and remove them on exit.
The repository `.gitignore` excludes local environment secrets, private keys,
certificates and kubeconfig files, while retaining `.env.example`; ignore rules
do not protect secrets already tracked by Git.

## Helm repository and Rancher Apps

The chart publishes to `https://acdh-oeaw.github.io/vocabs-platform/` after the
one-time GitHub Pages setup. See [Helm publishing and Rancher installation](docs/rancher.md)
for release versioning, GitHub settings, repository registration and development
pilot values. Chart packages include the pinned Varnish dependency.

Navigation destinations and environment-aware Swagger links are documented in
[the navigation guide](docs/navigation.md). Configure external destinations with
`skosmos.navigation`; Help and language switching reuse native Skosmos content.
