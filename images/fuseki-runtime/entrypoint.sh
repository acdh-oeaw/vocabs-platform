#!/bin/sh
set -eu
[ -z "${EXPECTED_JENA_VERSION:-}" ] || [ "$EXPECTED_JENA_VERSION" = "$JENA_VERSION" ] || { echo "Jena runtime version does not match profile" >&2; exit 1; }
# Java is PID 1; never remove database lock files.
exec java -jar /opt/jena/fuseki-server.jar "$@"
