# Gateway verification

`make test` runs the existing backend safety tests, gateway render/schema tests,
external Skosmos baseHref validation tests, and Node execution of the shipped
njs redirect functions. It requires Python dependencies and Node.js 18+. No
cluster, image pull, browser, or production credentials are needed.

`tests/gateway/smoke.py` is an optional Podman test using the exact chart images
and generated Nginx/Anubis configs against a **mock Skosmos HTTP backend**. With
Podman configured and the pinned images available, run:

```bash
.venv/bin/python tests/gateway/smoke.py
```

It requires available localhost ports 8080, 8081 and 9090, starts temporary
rootless containers with read-only filesystems and dropped capabilities, and
cleans them up. Test listeners are confined to localhost except Anubis' temporary
metrics listener (9090); run only on an isolated development/test machine.
It checks nginx -t, exec probes, redirect encoding, suffixes, forwarded headers,
CORS, machine/API/RDF passthrough, a browser challenge response and bbolt file
creation. It does not solve browser challenges, run Skosmos or emulate a CNI.

Before the first Kubernetes pilot, test the real chain and compare to the old
Nginx/Anubis deployment:

- GET `/` and representative Skosmos browser pages, including challenge solving.
- GET `/archecategory/<test-id>` and `/iso6393/<test-id>` through `/entity`.
- GET `/tadirah/<test-path>` and the other external redirects with suffixes/query strings.
- Skosmos REST API from existing automated clients, including Mozilla-like agents.
- Accept `text/turtle`, `application/rdf+xml`, and `application/ld+json` where supported.
- CORS OPTIONS requests and real cross-origin browser requests with the intended origin.
- Public HTTPS Host/baseHref and source IP attribution through the actual ingress controller.
- Percent escapes, Unicode, trailing slashes and query strings against old redirect results.
- NetworkPolicy enforcement: direct Skosmos, internal Nginx, Varnish and Fuseki blocked.
- Signing-key continuity, bbolt persistence, clean Recreate rollouts and traffic rollback.

Record actual results; passing the mock smoke test is not production acceptance.
