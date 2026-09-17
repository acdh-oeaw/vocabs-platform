#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${PYTHON:=python3}"
command -v helm >/dev/null
command -v kubeconform >/dev/null || { echo 'Install kubeconform v0.6.7; see README. Validation cannot silently skip it.' >&2; exit 1; }
helm lint ./chart/vocabs
"$PYTHON" tests/helm/test_render.py
"$PYTHON" tests/test_load.py
"$PYTHON" tests/gateway/test_gateway.py
node tests/gateway/redirects.mjs
"$PYTHON" scripts/validate-rdf.py
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
helm template vocabs ./chart/vocabs > "$work/default.yaml"
helm template vocabs ./chart/vocabs -f environments/example.yaml > "$work/example.yaml"
helm template vocabs ./chart/vocabs -f environments/example.yaml -f chart/vocabs/examples/candidate-import.yaml > "$work/import.yaml"
helm template vocabs ./chart/vocabs --set swagger.enabled=true --set swagger.specUrl=https://vocabs.example.org/swagger.json --set swagger.ingress.enabled=true --set swagger.ingress.host=api.example.org --set swagger.ingress.allowAnubisBypass=true > "$work/swagger.yaml"
kubeconform -strict -summary -kubernetes-version 1.31.0 "$work/"*.yaml
