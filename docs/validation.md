# Initial validation record

Executed locally on 2026-09-17:

- `helm dependency build ./chart/vocabs`: passed; official OCI Varnish Cache 0.1.3.
- `helm lint ./chart/vocabs`: passed with Helm 4.3.0 and Helm 3.17.3.
- `helm template vocabs ./chart/vocabs -f environments/example.yaml`: passed.
- `make test`: 7 Helm test methods (including multiple negative cases) and 6
  loader safety test methods passed with Helm 3 and Helm 4.
- `scripts/validate-rdf.py`: example/fixture and generated TDB1/TDB2 Turtle syntax
  passed with RDFLib. This does not substitute for RIOT or application tests.
- `scripts/validate.sh`: strict kubeconform validated 66 resources in four
  configurations against Kubernetes 1.31.0, with zero invalid/error/skipped items.
- `tests/integration/smoke.py`: real Jena 5.4.0 RIOT validation, TDB1/TDB2 loads,
  text indexing, 22-triple count, multi-word text search, HTTP readiness and
  SIGTERM shutdown passed with Java 21.0.7+6.

Initial network-restricted attempts at dependency/schema downloads and localhost
socket tests failed; reruns with the necessary execution permissions passed.
An early smoke failure exposed union-default-graph exclusion of physical default
triples; the default assembler was fixed and both engine tests then passed.

Docker is unavailable in the workspace, so container builds/runs, Varnish VCL
compilation in the actual image, Skosmos HTTP behavior and actual Kubernetes
rollouts/storage/Velero restores were not executed. Complete these gates before
production. CI is authored but has not run on GitHub in this session.

Final Git status/diff checks could not complete: repository metadata was visible
at initial inspection, but later `.git` appeared empty and Git reported “not a
repository”, including outside the sandbox. No command modified `.git`, no
commits were made and LICENSE was not edited. Do not interpret the missing Git
check as confirmation of a clean Git working tree.

## Gateway iteration (2026-09-17)

- `helm dependency build ./chart/vocabs`: passed with the unchanged pinned Varnish
  dependency. Network-restricted initial attempt failed; authorized network retry passed.
- `helm lint ./chart/vocabs`: passed on Helm 4.3.0 and 3.17.3.
- `helm template vocabs ./chart/vocabs -f environments/example.yaml`: passed.
- `make test PYTHON=...`: all 20 Python test methods passed, including existing
  backend safeguards and seven new gateway/configuration tests with multiple
  negative cases. Exact shipped njs functions also passed Node execution tests
  for URI encoding, query isolation, Unicode and external redirect suffixes.
- `make validate PYTHON=...`: all tests and Turtle checks passed; kubeconform
  validated 80 resources across four renders against Kubernetes 1.31.0, with
  zero invalid/error/skipped resources.
- `scripts/configmap.sh` ran with the actual Jena 5.4.0 RIOT, Java 21 and kubectl
  client dry-run (`KUBECONFIG=/dev/null`); it added the canonical baseHref and
  emitted a ConfigMap which passed the external-configuration URL validator.
- `tests/gateway/smoke.py` passed using the exact Anubis v1.27.0 and Nginx
  1.30.5-alpine images with a mock Skosmos HTTP backend: nginx -t, both exec
  probes, concept/DARIAH redirects including escaped slashes/query strings,
  forwarded HTTPS/client headers, CORS OPTIONS, REST/RDF passthrough, browser
  challenge response and bbolt file creation. The test containers were removed.
  Initial test-harness errors (HTTPConnection context manager and repeat-run
  socket reuse) were corrected before the successful complete run.
- `git diff --check`, shell syntax and local documentation link checks passed.
  Git metadata is now available; original Fuseki/Job/data-PVC templates,
  compatibility.yaml and LICENSE have no changes in this iteration. No commits
  were made.

Remaining: actual Kubernetes pilot, CNI enforcement/ingress trust configuration,
real Skosmos/browser challenge completion, machine/RDF content negotiation,
comparison against original production rewrite rules, CSI-backed bbolt restarts,
key continuity, rollout availability and traffic rollback. CI is authored but
not executed on GitHub in this session. The container smoke test used a mock
backend and is not evidence that these production checks pass.

## Vinyl Cache and vocabulary pilot (2026-09-22)

- The stack no longer uses the Varnish Helm dependency. Vinyl Cache 9.1.0 is built from the pinned upstream source tarball and managed directly by the parent chart.
- `make validate PYTHON=.venv/bin/python` passed: 12 theme tests, 20 Helm tests, 7 loader tests, 10 gateway tests, njs redirect tests, Turtle checks and kubeconform validation of 80/80 resources.
- A real cumulative-import pilot created a fresh candidate PVC and loaded the selected RDF dump with Jena 5.4.0. Candidate validation confirmed RDF content and JenaText search before activation.
- The candidate revision was activated with Fuseki and Vinyl Cache rollouts, and Skosmos served the imported vocabulary successfully.
- Search was verified through the deployed Skosmos application.
- A revisioned external Skosmos ConfigMap initially omitted `skosmos:customCss`, which reset the ACDH branding to upstream defaults. The configuration was corrected by preserving the accepted environment settings, including `skosmos:customCss`, service name, JenaText settings, languages and template cache.
- After the corrected ConfigMap rollout, the ACDH design and search both worked as expected.
- The pilot vocabulary uses canonical concept URIs under `vocabs.sshopencloud.eu`; it therefore validates import, Skosmos and search behavior but is not the final test case for the public concept-URI resolver.
