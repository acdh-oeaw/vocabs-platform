# Vinyl Cache runtime

Builds Vinyl Cache from the official source tarball using the version and
SHA256 pinned in `chart/vocabs/compatibility.yaml`. The Debian base image is
supplied by digest at build time so the runtime base is reproducible.

The image runs as UID/GID 10001 and starts `/usr/local/sbin/vinyld`. A C compiler
is intentionally retained in the runtime image because Vinyl compiles VCL at
startup. Kubernetes mounts the generated VCL at
`/etc/vinyl-cache/default.vcl` and uses `/var/lib/vinyl-cache` for runtime
state.

The image exposes port 6081 only. The Helm chart keeps the Vinyl Service
internal as `ClusterIP`; Skosmos reaches Fuseki through Vinyl Cache, while
management interfaces are not exposed.
