# Candidate imports and activation

The active JVM owns one PVC. An offline Job mounts another, empty candidate while
production continues serving. The chart rejects active-target equality and source
aliasing, but it cannot observe Jobs created by other releases or previous
renders. Serialize operations per namespace and inventory ALL running workloads
before importing or activating. Retain the environment values and assembler used
for each data revision.

1. Add a candidate to `data.managedClaims`, preserving existing entries, and run
   a normal Helm upgrade with `imports.job.enabled: false`. Or provision it
   separately. Ensure the immutable RDF source dump is available on the source
   PVC. Do not expose an empty initial database publicly before first acceptance.
2. Configure the same environment and overlay an explicit candidate Job. Prefer
   generating only that resource, then creating it outside Helm:

   ```bash
   helm template vocabs ./chart/vocabs --namespace YOUR-NAMESPACE \
     -f environments/YOUR-ENVIRONMENT.yaml \
     -f chart/vocabs/examples/candidate-import.yaml \
     --show-only templates/import-job.yaml > candidate-job.yaml
   # Review claim names, image version, source, assembler and resources.
   kubectl -n YOUR-NAMESPACE create -f candidate-job.yaml
   ```

   `--show-only` still validates the chart. Use the SAME release name and values
   as the live release, not a separate Helm release with stale activeClaim.
3. Follow logs and Job status. `load.sh destination RDF-file` checks arguments,
   versions, tools and fresh paths, runs `riot --validate`, loads with TDB1
   `tdbloader` or TDB2 `tdb2.tdbloader`, then builds JenaText. Disabling syntax
   validation or indexing requires an explicit value. Do not activate an unindexed
   candidate when Skosmos uses JenaText.
4. A failed load leaves its partial directory intact and is not resumable by this
   wrapper. Default backoffLimit is zero. Use a fresh candidate and a unique Job
   name for each attempt; never delete active files to make a retry work. `mkdir`
   atomically reserves a new destination; existing paths and symlinks are refused.
5. After the Job exits, inspect RDF graph/triple counts, languages, representative
   concepts and search results using a separately controlled validation workload
   or staging release against the candidate. Only one JVM may mount/open it at
   any time. Stop that validation workload before activation. See the acceptance
   checklist in `tests/integration/README.md`.
6. Quiesce public traffic at your ingress/maintenance layer. Confirm the importer
   and any candidate validator have terminated, then change `data.activeClaim`,
   `data.revision` and `varnish.server.podAnnotations` together; the latter's
   `vocabs.acdh.oeaw.ac.at/data-revision` must be `<claim>/<revision>`. See
   `chart/vocabs/examples/activate-r002.yaml`. Keep imports disabled.
7. Upgrade and wait for Fuseki's StatefulSet and Varnish's Deployment rollouts.
   Old Fuseki exits normally before its successor mounts the new claim. Never
   force-delete a stuck pod or remove lock files: investigate first. Test queries
   and Skosmos search, then resume traffic.
8. Keep the previous PVC. To roll back, quiesce traffic, switch claim/revision/cache
   annotation back and wait for both rollouts. Keep the compatible stack profile
   and configuration with each revision; do not point a different storage engine
   at its database files.

Cache invalidation is a process restart with a revision annotation. **Helm does
not order the Fuseki and Varnish rollouts atomically**: a new Varnish could query
old Fuseki before activation finishes. Therefore quiesce traffic for cutover and
restart Varnish once more after Fuseki is ready if any request could have entered
during transition. The new JVM and cache require a short maintenance window;
this design does not promise zero downtime. Maximum default cache TTL is 120s,
with no stale grace; cache invalidation is still required for correct activation.

No Job is a Helm hook. If you choose to enable it in an installed release, disable
it after completion. Leaving it enabled can recreate it after TTL cleanup on a
later upgrade. The recommended render-and-create flow keeps that risk out of
normal release values. Never use a persistent import-enabled overlay for ordinary
upgrades. Helm cannot prevent an operator from explicitly re-enabling imports.

## Resource profiles

Imports have separate JVM and pod resources. For a medium vocabulary:

```yaml
imports:
  java: {xms: 1g, xmx: 10g}
  resources:
    requests: {memory: 8Gi}
    limits: {memory: 12Gi}
```

For a larger vocabulary use `xms: 4g`, `xmx: 20g`, request `18Gi`, limit `24Gi`
and adequate CPU (see the environment example). These are starting points, not
production sizing. The pod limit must exceed Xmx for native memory, mmap pages,
thread stacks and Lucene overhead. Import sizing does not resize the live Fuseki
runtime. Plan enough space for the candidate DB, index, loader temporary files,
old revisions and original dump. Never place a live TDB dataset on a shared import
source just because the backend technically permits concurrent mounts.

TDB1 → TDB2 means RDF → new empty candidate → matching loader → new DB → new text
index → acceptance tests. It is not a copy of TDB1 data files. For named graphs,
use a dataset syntax such as TriG/N-Quads preserving graph names; a single RDF/XML
or Turtle dump loads into the default graph. Align each vocabulary's sparqlGraph
with how the dump was exported; do not invent graph placement during import.
