#!/bin/sh
# Compatibility interface: load.sh destination RDF-file [RDF-file ...]
set -eu

fail() { echo "load.sh: $*" >&2; exit 1; }

[ "$#" -ge 2 ] || fail "usage: load.sh destination RDF-file [RDF-file ...]"

destination=$1
shift

: "${STORAGE_ENGINE:?Set STORAGE_ENGINE from the stack profile (TDB1 or TDB2)}"
[ -z "${EXPECTED_JENA_VERSION:-}" ] || [ "$EXPECTED_JENA_VERSION" = "${JENA_VERSION:-}" ] || fail "Jena image version does not match selected profile"

case "$STORAGE_ENGINE" in
  TDB1) loader=tdbloader ;;
  TDB2) loader=tdb2.tdbloader ;;
  *) fail "unsupported storage engine: $STORAGE_ENGINE" ;;
esac

case "${VALIDATE_RDF:-true}" in true|false) ;; *) fail "VALIDATE_RDF must be true or false" ;; esac
case "${BUILD_TEXT_INDEX:-true}" in true|false) ;; *) fail "BUILD_TEXT_INDEX must be true or false" ;; esac

[ -n "$destination" ] && [ "$destination" != / ] || fail "destination must not be empty or /"

for source in "$@"; do
  [ -f "$source" ] && [ -r "$source" ] || fail "RDF source is not a readable regular file: $source"
done

# Require a NEW child directory, not a PVC root. Even an empty existing directory
# is refused, as it could belong to another process. Atomic mkdir prevents races.
[ ! -e "$destination" ] && [ ! -L "$destination" ] || fail "destination already exists; use a new candidate, never overwrite"

command -v "$loader" >/dev/null || fail "missing Jena loader: $loader"

if [ "${BUILD_TEXT_INDEX:-true}" = true ]; then
  [ -r "${ASSEMBLER:-}" ] || fail "ASSEMBLER is required for JenaText indexing"
  [ -n "${TEXT_INDEX_DIR:-}" ] || fail "TEXT_INDEX_DIR is required"
  [ ! -e "$TEXT_INDEX_DIR" ] && [ ! -L "$TEXT_INDEX_DIR" ] || fail "text index already exists"
  : "${FUSEKI_JAR:=/opt/fuseki/fuseki-server.jar}"
  [ -r "$FUSEKI_JAR" ] || fail "missing same-version Fuseki JAR for JenaText"
fi

printf 'Storage engine: %s\nDestination: %s\n' "$STORAGE_ENGINE" "$destination"
for source in "$@"; do
  printf 'Source: %s\n' "$source"
done

if [ "${VALIDATE_RDF:-true}" = true ]; then
  for source in "$@"; do
    riot --validate "$source"
  done
fi

mkdir -- "$destination" # Do not clean up on failure: partial loads remain visibly unusable.
"$loader" --loc="$destination" "$@"

if [ "${BUILD_TEXT_INDEX:-true}" = true ]; then
  # Verified class in jena-cmds 5.4.0; no standalone textindexer shell command.
  java -cp "$FUSEKI_JAR" jena.textindexer --desc="$ASSEMBLER"
fi

printf 'Load complete. Validate counts, graphs and search before activation.\n'
