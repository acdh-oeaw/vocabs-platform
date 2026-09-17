#!/usr/bin/env bash
# Emits YAML only. Review then explicitly apply with kubectl in the correct namespace.
set -euo pipefail
if (( $# < 4 )); then echo "usage: $0 environment-values.yaml namespace configmap-name base.ttl [categories.ttl vocabulary.ttl ...]" >&2; exit 2; fi
values=$1; namespace=$2; name=$3; shift 3
: "${PYTHON:=python3}"
script_dir=$(cd "$(dirname "$0")" && pwd)
command -v riot >/dev/null || { echo "Apache Jena RIOT is required; config generation cannot skip RDF validation" >&2; exit 1; }
command -v kubectl >/dev/null
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
for file in "$@"; do cat -- "$file"; printf '\n'; done > "$work/config.ttl"
"$PYTHON" "$script_dir/skosmos-public-url.py" --values "$values" --config "$work/config.ttl" --add-missing
riot --validate "$work/config.ttl"
kubectl -n "$namespace" create configmap "$name" --from-file="config.ttl=$work/config.ttl" --dry-run=client -o yaml
