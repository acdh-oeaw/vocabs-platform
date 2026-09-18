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

bbolt persistence does not preserve the signing key automatically. In the
development profile the chart creates and preserves the signing Secret; the
initial value is a 64-character lowercase hex Ed25519 seed generated from
cryptographically random bytes. The chart also supports an external Secret via
`gateway.anubis.signingKey.secret.existingSecret` when `create: false`.
An existing managed Secret is preserved by Helm lookup, and a missing key fails
rendering rather than rotating credentials. No Secret material belongs in
policy examples or Git. See docs/gateway.md for state and rollout requirements.
