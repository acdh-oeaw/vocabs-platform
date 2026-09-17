# Future stack acceptance suite

`vocabulary.ttl` is a small starter fixture, not a complete compatibility suite.
Add stable expected results and representative ACDH data before promoting a
profile. Cover broader/narrower, preferred/alternative/hidden labels, notation,
collections, mapping relations, English/German and multi-word examples.

For each candidate profile, build images, validate/import the fixture into a
fresh PVC and build JenaText. Exercise Skosmos homepage, vocabulary page, concept
page, hierarchy, REST API, single-word and multi-word search, alternative/hidden
label search, notation search, direct JenaText queries, concept URI resolution
and HTTP content negotiation. Compare expected URI sets, counts and language
selection with the accepted baseline, not just HTTP 200 responses.

Also test process SIGTERM, DB reopen, no concurrent writers, candidate switch,
cache invalidation, rollback, real PVC attachment behavior and Velero restore.
Repeat with representative large production vocabulary dumps. Store evidence
with the profile. CI currently validates manifests/syntax/safety only; it does
not claim these acceptance checks pass.

## Optional executable Jena smoke test

With Java 21 on PATH, JAVA_HOME set, and the verified Jena 5.4.0 core/Fuseki
archives extracted locally, run:

```bash
.venv/bin/python tests/integration/smoke.py \
  --jena-home /path/to/apache-jena-5.4.0 \
  --fuseki-jar /path/to/apache-jena-fuseki-5.4.0/fuseki-server.jar
```

It imports and indexes both TDB1 and TDB2 in temporary directories, opens a
localhost Fuseki server, checks 22 triples and multi-word text search, then sends
SIGTERM and waits for shutdown. It requires local TCP permission and is separate
from Helm CI. It exercises the actual load.sh wrapper and generated assembler;
it does not build containers or test Skosmos, CSI storage or production data.

## Public gateway acceptance

Also follow `tests/gateway/README.md`: GET / and browser pages; archecategory and
iso6393 concept redirects; tadirah suffix redirects; REST API; Turtle, RDF/XML
and supported JSON-LD Accept negotiation; CORS OPTIONS; completed Anubis browser
challenges; and real machine/API clients. Run against the full Ingress → Anubis
→ Nginx → Skosmos path before promoting an environment.
