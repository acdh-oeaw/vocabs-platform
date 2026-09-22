# Modular Skosmos configuration

For a new environment, start from `base.ttl.example`, add the required
categories and `vocabularies/*.ttl`, then adapt the environment-specific
settings before generating the external ConfigMap.

For an existing deployed environment, do **not** rebuild the configuration from
the minimal example alone. Preserve the currently accepted environment
configuration and extend it with the new vocabulary fragments. In particular,
retain environment-specific settings such as `skosmos:serviceName`,
`skosmos:customCss`, the SPARQL endpoint and dialect, languages, plugins and
template cache. Rebuilding an external ConfigMap from an incomplete base can
silently reset branding or runtime behavior.

Use consistent prefix declarations and vocabulary URIs; concatenation of
contradictory `@base` or prefix declarations can silently change meaning even
when Turtle is valid. Vocabulary resources that define Skosmos route IDs use
local fragments such as `<#example>`. Shared configuration and category
resources may use stable absolute identifiers such as
`urn:acdh:vocabs:config:`.

## Updating an existing deployed configuration

For an existing deployment, export the currently active `config.ttl` and extend
that accepted configuration with the new vocabulary fragment. This preserves
branding and environment-specific runtime settings.

```bash
kubectl get configmap YOUR-SKOSMOS-CONFIG \
  -n YOUR-NAMESPACE \
  -o jsonpath='{.data.config\.ttl}' \
  > /tmp/skosmos-current.ttl
```

Combine the accepted configuration with the new vocabulary fragment:

```bash
cat /tmp/skosmos-current.ttl \
  config/skosmos/vocabularies/YOUR-VOCABULARY.ttl \
  > /tmp/skosmos-next.ttl

riot --validate --syntax=TURTLE /tmp/skosmos-next.ttl
```

Validate the public URL contract with the environment values before creating the ConfigMap:

```bash
.venv/bin/python scripts/skosmos-public-url.py \
  --values environments/YOUR-ENVIRONMENT.yaml \
  --config /tmp/skosmos-next.ttl
```

Create a new revisioned ConfigMap rather than changing the active one in place:

```bash
kubectl create configmap YOUR-SKOSMOS-CONFIG-rNNN \
  -n YOUR-NAMESPACE \
  --from-file=config.ttl=/tmp/skosmos-next.ttl
```

Set `global.publicUrl` in the environment values. The ConfigMap workflow adds a
missing baseHref from it and rejects any conflicting value; do not maintain an
independent URL. Edit the Skosmos → Vinyl Cache SPARQL endpoint, language
settings, graph names and enabled plugins for each namespace. A default-graph
vocabulary example is supplied; use `skosmos:sparqlGraph` only when your dataset
was imported into that named graph. Keep this configuration out of a large Helm
template. Validate semantics in staging in addition to checking Turtle syntax.

```bash
PYTHON=.venv/bin/python bash scripts/configmap.sh \
  environments/example.yaml YOUR-NAMESPACE vocabs-skosmos-config \
  config/skosmos/base.ttl.example config/skosmos/categories.ttl.example \
  config/skosmos/vocabularies/*.ttl > configmap.yaml
# Review the generated YAML, then kubectl apply -f configmap.yaml in that namespace.
```

The script requires Python with scripts/requirements.txt, Jena RIOT and kubectl, combines files deterministically in
argument order, validates with `riot --validate`, and emits a ConfigMap without
applying it. Errors propagate. Select `skosmos.config.existingConfigMap` and bump
`skosmos.config.revision` on every external config change; subPath mounts do not
hot-reload changed data. Inline development config is supported with automatic
checksum rollout. Helm does not validate external ConfigMap contents.

For an existing externally supplied ConfigMap, validate its `config.ttl` with
`scripts/skosmos-public-url.py --values environments/YOUR-ENVIRONMENT.yaml
--config exported-configmap.yaml --configmap` before deploying it. There must be
exactly one Configuration and one baseHref matching global.publicUrl. The chart
cannot inspect external content. This is also required when the public URL
changes or a complete inline configuration is used. The generated default Helm
configuration includes baseHref automatically. See docs/gateway.md.
