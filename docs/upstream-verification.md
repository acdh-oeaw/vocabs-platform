# Upstream verification record

Inspected on 2026-09-17. Source verification does not imply production acceptance.

- Official Varnish repository links its chart project: https://github.com/varnish/varnish
- Chart source: https://github.com/varnish/helm-varnish/tree/c0e504d3f41c858715de314a75dbff830a709439/varnish-cache
  Inspected Chart.yaml, values.yaml, metadata/pod helpers, VCL templating and service
  defaults. Verified public OCI `varnish/varnish-cache:0.1.3` with `helm show chart`
  and dependency build. Published manifest digest:
  `sha256:408ec23f315f0f050559ec1fe5a5a3d86bfe18acf2f21c712debcb8ff0ac5bb6`.
  Upstream NodePort default is explicitly overridden to ClusterIP. Upstream chart
  appVersion is 9.0.0. The actual downloaded chart archive was inspected too.
- Skosmos source revision: https://github.com/NatLibFi/Skosmos/tree/44eb8756ffcacf84a625dc974c42d8df70dacfc1
  (`v3.3`). Inspected dockerfiles/Dockerfile.ubuntu, docker-compose.yml,
  config.ttl.dist, dockerfiles/config/config-docker-compose.ttl and skosmos.ttl.
  Verified web root, extension directories, Jena 5.4.0 reference and **TDB2**
  upstream assembler. Our requested TDB1 candidate remains unvalidated against
  production. Quay image tag/digest and runnable ACDH overlays remain release gates.
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
