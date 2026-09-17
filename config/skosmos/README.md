# Modular Skosmos configuration

Copy `base.ttl.example` to your environment's base.ttl, add categories.ttl and
`vocabularies/*.ttl`. Use stable absolute configuration identifiers, consistent
prefix declarations and vocabulary URIs; concatenation of contradictory @base
or prefix declarations can silently change meaning even when Turtle is valid.
The examples use `urn:acdh:vocabs:config:` to avoid relative-base ambiguity.

Set `global.publicUrl` in the environment values. The ConfigMap workflow adds a
missing baseHref from it and rejects any conflicting value; do not maintain an
independent URL. Edit the Skosmos → Varnish SPARQL endpoint, language
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
