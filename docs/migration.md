# Migration, one namespace at a time

For a new migration, follow the [operator guide](operator-guide.md) for the
current release and export/import commands. The dated case study below records
what happened in 2026; its claim names and exceptions are not commands to rerun.

1. Inventory the existing namespace and responsible maintainers.
2. Record hostname, canonical URI behavior, Skosmos config, original RDF sources,
   graph names, Jena version and TDB engine, JenaText analyzer/index configuration,
   PVC usage, resource peaks, ACDH theme/plugin differences and proxy/redirect rules.
3. Build reviewed images and deploy the chart in parallel, using an isolated
   namespace/hostname and no production traffic. Verify external ConfigMaps point
   to the new Vinyl Cache service. Keep the original deployment intact.
4. Create a new candidate block-storage PVC using the environment's RBD class.
5. Import the original immutable RDF dump with the selected Jena tools version.
6. Build a fresh JenaText index with matching engine, graph and analyzer settings.
7. Run the compatibility checklist, compare counts and representative multilingual
   results to production, and test shutdown/startup, backup restore and rollback.
8. Coordinate a brief traffic cutover/maintenance window. Switch ingress/DNS after
   the new stack and cache are ready; preserve concept URI and redirect behavior.
9. Keep the previous deployment, configuration, images and data for rollback,
   with a documented retention window and a tested reverse traffic switch.
10. Migrate the next namespace only after the current one is stable.

For the downloads hostname, verify a representative existing dump path and
its content through the new Ingress before switching production DNS or
removing the old Ingress. Ensure only one active release owns the production
hostname and retain the old image and routing for rollback.

Do not copy an old TDB1 database into an incompatible TDB2 runtime. RDF is the
portable source of truth. Prefer fresh imports even for version upgrades unless
physical compatibility is explicitly established and tested. ACDH-specific theme
and plugin changes move into `branding/`; do not fork the full upstream source.

## Production vocabulary migration to `vocabs-platform-dev` (2026-09-23)

The first full production-data migration was performed from the legacy
`vocabs-prod` deployment into `vocabs-platform-dev`.

### Source inventory

The legacy production Fuseki deployment contained two TDB2 datasets:

- `vocabs-main`
- `vocabs-date-entities`

Only `vocabs-main` contained the active Skosmos vocabularies. The production
Skosmos configuration had the `date_entities` and `unit_of_time` vocabularies
commented out, so `vocabs-date-entities` was deliberately not part of this
migration.

The active `vocabs-main` dataset contained:

- 3,633,611 quads in named graphs
- 26 named graphs
- 0 triples in the default graph

The legacy database used TDB2, while the new platform profile uses TDB1.
Therefore the database directory was not copied between deployments. RDF was
used as the portable migration boundary.

### Production export

The production dataset was exported read-only through the Fuseki HTTP dataset
endpoint as N-Quads:

```sh
set -o pipefail
kubectl exec -n vocabs-prod <production-fuseki-pod> -- \
  curl -fsS -H 'Accept: application/n-quads' \
  http://127.0.0.1:3030/vocabs-main/ \
  | gzip -1 > "$HOME/vocabs-main-prod-2026-09-22.nq.gz"
```

The resulting export contained exactly 3,633,611 N-Quads lines. After
decompression its SHA-256 checksum was:

```text
80950d103593378b628ebe612a645a3c3cdc0960d5cb42428eae77204d3104ab
```

The decompressed N-Quads file was copied to the shared `vocabs-import` PVC and
the checksum was verified again inside the cluster before import.

### Legacy RDF validation exception

An initial fresh candidate (`r004`) used strict RIOT validation. Validation
failed before the TDB loader started because the legacy production RDF contains
invalid lexical forms for some `xsd:dateTime` literals, including values such
as a date without a time component and empty lexical values.

The failed candidate was not reused.

A new candidate PVC (`vocabs-data-r005`) was created and the same immutable
export was imported with `VALIDATE_RDF=false`. This was an explicit migration
exception for already-serving legacy data; the RDF was not silently normalized
or rewritten during migration.

### Candidate import and indexing

The production N-Quads export was loaded into the fresh TDB1 candidate with
Jena 5.4.0 using the repository's `vocabs-jena-tools` importer.

The importer reported:

- 3,633,611 quads loaded
- 3,633,611 quads indexed
- 517,340 JenaText properties indexed

A new Lucene/JenaText index was built from the same assembler configuration
used by the runtime.

### Candidate validation

Before activation, `vocabs-data-r005` was mounted by an isolated temporary
Fuseki 5.4.0 validator. The active `r003` deployment remained untouched.

Validation confirmed:

- 3,633,611 named-graph quads
- 26 named graphs
- the exact production graph URI set
- 0 triples in the default graph
- JenaText lookup inside named graphs

The named-graph detail is important: the integration fixture used at the time
stored data in the default graph, while the production dataset stores all
vocabulary data in named graphs.

### Skosmos configuration migration

The legacy production Skosmos configuration was adapted for Skosmos 3.3 rather
than copied unchanged.

The migrated configuration preserved the 26 active vocabulary definitions,
categories, languages, concept schemes, graph URIs and vocabulary-specific
settings. Runtime-specific settings were changed for the new platform,
including:

- the development `baseHref`
- the ACDH Vocabs service name and custom CSS
- JenaText as the SPARQL dialect
- the Vinyl Cache SPARQL endpoint
- the current template cache and interface languages

The resulting revisioned ConfigMap was
`vocabs-platform-dev-vocabs-skosmos-config-r005a`.

An isolated Skosmos 3.3 validator was connected directly to the candidate
Fuseki before activation. It successfully loaded all 26 active vocabularies.
Functional tests included:

- ISO 639-1 `English` lookup through `prefLabel`
- TaDiRAH `NLP` lookup through `altLabel`

### Cutover

Public gateway and REST API ingresses were temporarily disabled while the
Fuseki administrative ingress remained available.

The activation changed these values together:

```yaml
data:
  activeClaim: vocabs-data-r005
  revision: r005

skosmos:
  config:
    existingConfigMap: vocabs-platform-dev-vocabs-skosmos-config-r005a
    revision: r005a

vinyl:
  podAnnotations:
    vocabs.acdh.oeaw.ac.at/data-revision: vocabs-data-r005/r005
```

Imports remained disabled.

The Fuseki StatefulSet and Vinyl Cache Deployment completed their rollouts
successfully. Live validation then reconfirmed the 3,633,611/26 dataset
baseline and successful Skosmos `prefLabel` and `altLabel` searches.

Public ingress was re-enabled only after those checks passed. Final external
smoke tests returned HTTP 200 for the Skosmos UI and a successful TaDiRAH
`NLP` result through the public REST API.

The previous `vocabs-data-r003` PVC was retained as the rollback candidate.
