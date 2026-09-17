# Tests

`make test` runs semantic Helm render/negative tests with strict duplicate-key
YAML parsing and shell-loader safety tests with fake executables. These cover
namespace selectors, private services, ingress scope, retained PVCs, explicit
active/candidate mounts, absent default import Jobs, matching Jena versions,
profile rejection, candidate safety and configuration/cache rollout annotations.
Mock loader tests check command ordering and error propagation, not Jena behavior.

`make validate` adds Helm lint, RDFLib Turtle syntax checks, four rendered
configurations and strict kubeconform Kubernetes 1.31 schemas. Jena RIOT and actual
container/cluster integration are separate; no tool absence is silently ignored.
Run `make deps` first. Python dependencies are in scripts/requirements.txt.
Future runtime acceptance is documented under integration/.

An optional real Jena integration smoke test is provided in
`tests/integration/smoke.py`; see its README for prerequisites and invocation.

Gateway checks are included in `make test`/`make validate`: the two-container
path, ingress scope, public URL and baseHref contracts, local-store replica
restrictions, declarative redirects, CORS, proxy headers, and njs escaping.
Node.js 18+ is required. `tests/gateway/smoke.py` optionally exercises the exact
container images with a mock backend; see its README for scope and prerequisites.
