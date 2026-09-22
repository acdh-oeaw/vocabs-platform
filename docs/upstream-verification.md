# Upstream verification record

Inspected on 2026-09-17; Vinyl Cache verification refreshed on 2026-09-22. Source verification does not imply production acceptance.

- Vinyl Cache upstream: https://vinyl-cache.org/ . The former Varnish Cache FOSS
  project is now Vinyl Cache; version **9.1.0** was released on 2026-09-16.
  The ACDH runtime is built directly from the official source tarball
  `https://vinyl-cache.org/downloads/vinyl-cache-9.1.0.tgz`, not from a Helm
  dependency chart. `chart/vocabs/compatibility.yaml` pins source SHA256
  `3840a06dd0cd212fd1e3beeb8b086dbd7c35ca31cfe1962fe2586363a63410aa`.
  `images/vinyl/Dockerfile` verifies that checksum before building, installs
  Vinyl under `/usr/local`, and uses `/usr/local/sbin/vinyld` as the runtime
  entrypoint. The parent Helm chart manages the internal ClusterIP Deployment,
  Service and VCL ConfigMap directly.
- Skosmos source revision: https://github.com/NatLibFi/Skosmos/tree/44eb8756ffcacf84a625dc974c42d8df70dacfc1
  (`v3.3`). Inspected dockerfiles/Dockerfile.ubuntu, docker-compose.yml,
  config.ttl.dist, dockerfiles/config/config-docker-compose.ttl and skosmos.ttl.
  Verified web root, extension directories, Jena 5.4.0 reference and **TDB2**
  upstream assembler. Our requested TDB1 candidate remains unvalidated against
  production. Verified upstream container reference: `quay.io/natlibfi/skosmos:v3.3`.
  The non-tagged form `quay.io/natlibfi/skosmos:3.3` does not exist in the registry;
  the Git tag is `v3.3` while the ACDH image tag is `ghcr.io/acdh-oeaw/vocabs-skosmos:3.3-r2`.
  Quay image tag/digest and runnable ACDH overlays remain release gates.
- Apache Jena source: https://github.com/apache/jena/tree/jena-5.4.0
  Inspected loader scripts and `jena-text/src/main/java/org/apache/jena/query/text/cmd/textindexer.java`.
  The indexer accepts `--desc=assemblerFile`. Both official distributions were
  downloaded from https://archive.apache.org/dist/jena/binaries/ and verified
  against their SHA512 files; hashes are recorded in compatibility.yaml.
  Core archive contains RIOT, tdbloader, tdb1.xloader, tdb2.tdbloader,
  tdb2.xloader, but **not** jena-text. The same-version Fuseki server JAR contains
  `jena.textindexer`, `org.apache.jena.query.text.cmd.textindexer` and text dataset
  classes. The importer includes that JAR explicitly.
- Swagger UI v5.17.14: https://github.com/swagger-api/swagger-ui/tree/v5.17.14
  Tag and Dockerfile verified. Official swaggerapi/swagger-ui image uses port
  8080 and configurable specification URL. No community chart is used.
- Java runtime base image selected for Fuseki/Jena tooling: `docker.io/library/eclipse-temurin:21-jdk-jammy@sha256:4cfc63a7118da9267c17e2c988e1599d83d5d64a3832a760f0e77c7e8f6b29f7`.
  Verified from Docker's registry manifest on 2026-09-18. The image is Ubuntu 22.04
  (Jammy) based, Java 21, and pinned by immutable digest for the build workflow.
- CI checkout v4.2.2 commit verified through GitHub's tag API. Helm 3.17.3 and
  kubeconform 0.6.7 archives have fixed SHA256 checksums in CI. Kubernetes schemas
  use version 1.31.0; validation requires network access to the schema registry.

Initial misses (Skosmos root Dockerfile and alternate version tag spellings)
returned 404; the paths above were then found in the actual tagged source tree.
No upstream chart version was guessed or left unresolved.

## Local runtime evidence

The optional smoke test passed on a temporary Temurin Java 21.0.7+6 runtime:
TDB1 and TDB2 each loaded 22 fixture triples, indexed nine label/notation values,
answered a SPARQL count and JenaText multi-word query, passed /$/ping, and exited
on SIGTERM. The test found and corrected union-default-graph behavior which hid
physical default-graph imports. Lucene emitted optional native/vector performance
warnings; these were not errors. This is a small local test, not ACDH production
certification, a Docker build, or a Kubernetes storage test.

## Gateway verification (2026-09-17)

- Anubis latest non-prerelease: **v1.27.0**, published 2026-08-08, verified with
  https://api.github.com/repos/TecharoHQ/anubis/releases/latest . Tagged source:
  https://github.com/TecharoHQ/anubis/tree/v1.27.0 . Inspected cmd/anubis/main.go,
  internal/headers.go, lib/policy/expressions/environment.go, policies.mdx and
  .ko.yaml. Verified bbolt store parameters, environment names, healthcheck flag,
  forwarding normalization and policy expressions. Registry image configuration
  confirms UID 1000 and /ko-app/anubis entrypoint.
- Nginx upstream source:
  https://github.com/nginx/docker-nginx-unprivileged/tree/bf9eed6de9a7ff412f1e37d604ee491f2cf78528/stable/alpine
  specifies **1.30.5-alpine**, UID/GID 101 and packaged nginx-module-njs 1.0.1.
  Registry tag verified at
  https://hub.docker.com/v2/repositories/nginxinc/nginx-unprivileged/tags/1.30.5-alpine .
  Observed manifest digest:
  `sha256:daa17b944bac2b578e962da4c61ad72a59233b3c63abea17113acaf4e6b9aea4`.
  The pulled image confirms Nginx 1.30.5, /usr/lib/nginx/modules, and accepts the
  generated njs-enabled configuration under the restricted container settings.

The gateway versions are pinned in chart values and released with chart 0.2.0-dev;
the existing Skosmos/Jena compatibility profile was not redesigned.
