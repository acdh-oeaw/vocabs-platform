# Anubis policy

`policy.yaml.example` is the generated default for pinned Anubis v1.27.0. The
chart-packaged template is `chart/vocabs/files/anubis-policy.yaml`; tests ensure
this example agrees with its default rendering. The full versioned upstream
policy format is documented at:
https://github.com/TecharoHQ/anubis/blob/v1.27.0/docs/docs/admin/policies.mdx

The default allows REST/preflight and RDF Accept types before challenging
Mozilla-like GET requests for HTML. Other machine clients pass through. This
compatibility-first choice does not stop bots which emulate allowed clients;
review actual ACDH traffic and policies before tightening it. Test REST API,
Turtle, RDF/XML, JSON-LD where supported, CORS and existing automation as well as
human challenge completion. A successful render is not a policy acceptance test.

To supply a reviewed full policy, create a ConfigMap with a `policy.yaml` key and
select gateway.anubis.policy.existingConfigMap. Change policy.revision when its
contents change. Validate with the pinned Anubis runtime: Helm cannot parse a
ConfigMap it does not own. Keep the selected store contract (`bbolt`, path
`/data/anubis.bdb`, or `memory`) and metrics listener `:9090`; the native health
probe relies on it. Do not add an HA backend or allow more than one replica in
this iteration.

bbolt persistence does not preserve the signing key automatically. Supply an
existing Secret via gateway.anubis.signingKey for tokens to survive restarts;
public ingress rendering fails without this reference. In ingress-disabled
development only, omission permits a random key which invalidates tokens after
restart. Provision and verify the referenced Secret before installation; Helm
rendering cannot verify its existence or key contents. No Secret material
belongs in policy examples or Git. See docs/gateway.md for state and rollout
requirements. No Anubis Operator or cluster-scoped resources are deployed.
