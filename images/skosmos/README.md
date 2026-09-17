# Skosmos branding image

Build from the repository root using `scripts/build-images.py`, which reads the
stack profile. The Dockerfile inherits `quay.io/natlibfi/skosmos:3.3` and copies
only ACDH extension assets. `/var/www/html` and its extension/resource directories
were checked against `NatLibFi/Skosmos` v3.3 `dockerfiles/Dockerfile.ubuntu`.

The registry tag must still be verified against the published source and pinned
to a digest before production. No registry image has been built/published by this
scaffold. Test Apache startup, forwarded headers, /en/ probes, PHP/Twig writable
cache paths, plugin behavior and canonical URLs. Upstream starts Apache as root;
the chart does not invent an arbitrary runtime UID. A hardened non-root variant
requires explicit upstream image adaptation and testing. See `branding/README.md`.
