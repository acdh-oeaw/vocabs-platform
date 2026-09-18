# Helm-managed public gateway

```text
Internet → Ingress (TLS) → Gateway Service :80 → Anubis :8080
                                                 ↓ localhost
                                        nginx-unprivileged 127.0.0.1:8081
                                                 ↓
                                            Skosmos → Varnish → Fuseki
```

One namespaced Deployment contains both gateway containers. Only Anubis has a
Service port. Nginx binds loopback, so even direct access to the pod IP cannot
reach its internal port. No Anubis Operator, CRDs, cluster controller, Redis or
Valkey is installed. The existing Fuseki, import and retained-data PVC model is
unchanged. Chart 0.2.0-dev introduces the gateway; the RDF stack profile stays the
same.

## Enable and configure

Generic defaults keep the gateway and ingress disabled so a backend-only render
needs no public hostname. `environments/example.yaml` enables the gateway and
contains `global.publicUrl: "https://vocabs.example.org/"`. Replace infrastructure
placeholders and set the actual public URL in your own environment file; GitHub
variables are not required.

The URL must be absolute HTTP/HTTPS, have a DNS hostname, and end in `/`. Only a
root URL is supported initially, with an optional port; userinfo, query strings,
fragments and subpath deployments are rejected. Scheme, authority, ingress
hostname, Nginx redirects, Anubis PUBLIC_URL/cookie security and the generated
Skosmos baseHref all derive from it. The old `ingress.host` option is removed and
rejected by the schema. A URL with a port retains that authority in Host headers,
while Ingress rules use the hostname alone. Anubis REDIRECT_DOMAINS also uses
the authority: for `https://vocabs.example.org:8443/` it is
`vocabs.example.org:8443`, while the Ingress host remains `vocabs.example.org`.
TLS-enabled ingress requires HTTPS.

Select the ingress class, TLS Secret and gateway StorageClass for your cluster.
Configure the ingress-controller peers explicitly, for example using your own
namespace and pod labels:

```yaml
networkPolicy:
  gatewayIngressPeers:
    - namespaceSelector:
        matchLabels:
          YOUR-NAMESPACE-LABEL: YOUR-INGRESS-NAMESPACE-VALUE
      podSelector:
        matchLabels:
          YOUR-POD-LABEL: YOUR-INGRESS-CONTROLLER-VALUE
```

The two selectors in one peer are ANDed. Separate peers are ORed. An empty list
(default) denies gateway ingress when NetworkPolicies are enabled. This is an
explicit deployment prerequisite, not a label guess. A host-network ingress
controller may require a cluster-specific peer/ipBlock design. Skosmos admits
only same-release gateway pods plus explicitly configured additional peers;
Varnish and Fuseki retain their existing restrictions. Enforcement requires a
supporting CNI and additive policies elsewhere can broaden access.

## Configuration and URL compatibility

With the chart-generated Skosmos config, baseHref follows global.publicUrl
automatically. Keep vocabulary definitions modular for an external ConfigMap:

```bash
PYTHON=.venv/bin/python bash scripts/configmap.sh \
  environments/YOUR-ENVIRONMENT.yaml YOUR-NAMESPACE vocabs-skosmos-config \
  config/skosmos/base.ttl.example config/skosmos/categories.ttl.example \
  config/skosmos/vocabularies/*.ttl > configmap.yaml
```

The workflow adds a missing baseHref from the environment, rejects a conflicting
one, validates Turtle with RIOT, and emits YAML without applying it. It requires
Python dependencies, RIOT and kubectl. Prefer absolute configuration identifiers
as in the examples. Configuration generation resolves relative Turtle identifiers
against the canonical public URL; inspect the result when migrating old files.

For an existing external ConfigMap, export it to YAML and run:

```bash
.venv/bin/python scripts/skosmos-public-url.py \
  --values environments/YOUR-ENVIRONMENT.yaml \
  --config configmap.yaml --configmap
```

This validates exactly one Configuration subject and exactly one baseHref equal
to global.publicUrl. Helm cannot read an external ConfigMap's content at offline
render time: this check is a **required pre-deployment contract**, including on
public URL changes. Regenerate the ConfigMap and bump skosmos.config.revision;
subPath mounts do not hot reload. Complete inline configs have the same contract
and can be validated as combined Turtle with `--config config.ttl`.

## URI redirects

`gateway.conceptResolver.namespaces` holds the 21 supplied concept namespaces.
One generated location expression matches a namespace followed by a nonempty
identifier; a bare vocabulary namespace still reaches Skosmos. njs redirects to
`<publicUrl>entity?uri=<encoded-original-public-URI>` with status 302 by default.
The URI is constructed from the canonical URL and the **raw request URI**, then
encoded as one query value. Existing percent escapes, Unicode and query delimiters
are retained without turning them into extra `/entity` parameters. Request query
strings, when present, remain part of that encoded original URI. Confirm this
edge-case contract against the old deployment during the pilot; no original
production Nginx configuration was supplied for comparison.

The official full `1.30.5-alpine` image includes njs; `alpine-slim` does not. This
small JavaScript helper is needed because native Nginx rewrite variables do not
provide general URL encoding. `tests/gateway/redirects.mjs` exercises the shipped
code, including percent-encoded slashes, spaces, Unicode and query delimiters.

`gateway.externalRedirects` generates bounded-prefix locations for tadirah,
invocation-type and bbt. Each uses its declared target/status and preserves the
raw suffix, trailing slash and query string. `/tadirahfoo` is not a match. A
percent-encoded spelling of an external prefix is rejected rather than guessed.
Schema restrictions prevent regex/config injection and duplicate or conflicting
redirect prefixes fail rendering.

## Headers and CORS

Ingress must overwrite client-supplied forwarding headers with trusted values,
including X-Real-IP or a trustworthy X-Forwarded-For, and the external scheme.
Restrict ingress to the gateway using the NetworkPolicy peers. Anubis 1.27.0
normalizes X-Forwarded-For (including private-hop stripping/flattening), so the
application receives its normalized client information, not an untouched chain.
Nginx forwards that value and X-Real-IP without appending localhost. Test real
client attribution with your ingress controller; headers are not authentication.

Host and X-Forwarded-Host use the canonical authority. X-Forwarded-Proto preserves
an incoming single `http` or `https` token; absent/invalid values fall back to the
canonical URL scheme. It never uses the internal Nginx HTTP `$scheme`. Ensure
Apache/Skosmos trust the intended proxy chain and generated links remain HTTPS.

CORS defaults preserve the supplied methods (`POST, GET, OPTIONS, DELETE, PUT`),
max age 1000 and headers (`x-requested-with, Content-Type, origin, accept`). Nginx
adds them with `always` and answers OPTIONS with 204, including concept paths.
`allowOrigin` defaults empty because the supplied existing settings did not
specify an origin policy. Set it explicitly to `*` or a reviewed origin if actual
cross-origin clients need it; this chart does not invent a credentials policy.
Anubis-generated challenge pages do not pass through Nginx; preflight/API/RDF
requests are exempted first in the starter policy.

## Anubis policy and state

Anubis v1.27.0 was verified as the latest non-prerelease from the official release
API when implementing this change. The image's UID 1000 and `/ko-app/anubis`
entrypoint were inspected. The Nginx image is `nginxinc/nginx-unprivileged:1.30.5-alpine`,
verified in the upstream source and registry with UID/GID 101 and the njs module.
Both run non-root with capabilities dropped, no privilege escalation and a
read-only root filesystem. Nginx has a writable temporary volume; Anubis writes
only its separate `/data` volume. The chart rejects reusing an active, managed, source or candidate RDF claim for
gateway state.

The conservative starter policy allows REST, RDF Accept types and OPTIONS first,
challenges Mozilla-like GET requests accepting HTML, and allows remaining machine
clients. It deliberately favors compatibility over comprehensive bot blocking:
spoofing a machine Accept/User-Agent can bypass it. Review real client patterns
before tightening the policy. An external reviewed ConfigMap with `policy.yaml`
is supported; it must retain the selected store backend/path and metrics endpoint
contract. Helm cannot validate external policy content. Bump policy.revision to
roll out changes and validate the file with the pinned Anubis runtime.

bbolt is the default local backend and uses `/data/anubis.bdb` on a retained,
StorageClass-configurable PVC. Recreate updates prevent rolling-surge overlap
against its exclusive lock. Gateway replicas other than one fail rendering,
even with memory storage. If persistence is disabled, emptyDir stores ephemeral
bbolt data; memory requires persistence disabled. Neither permits horizontal
scaling. Future HA needs a separately designed shared backend; not this iteration.
Gateway updates have a short availability gap; do not promise zero downtime.

Set gateway.anubis.signingKey.existingSecret to an existing Secret with the
hex-encoded 32-byte Ed25519 seed under the configured key. This is separate from
bbolt persistence. When `ingress.enabled=true`, Helm rendering fails without
this Secret reference, even if compatibility.allowUnsupported is enabled or
Anubis persistence is disabled. There is no public-ingress development bypass.
The chart checks the reference, not the live Secret or its contents: provision
and verify it before installation. The example names a placeholder Secret and
does not create it or contain key material.

Backend-only/default rendering and an ingress-disabled development gateway may
omit the key. In that case upstream generates a random key and existing challenge
tokens become invalid after restart; this exception is not for public deployments.
A gateway exposed publicly by infrastructure outside this chart must also supply
the persistent key; Helm cannot detect external exposure.
Generate/manage secrets outside Git and restart the gateway after rotating one.

Anubis probes invoke its native `-healthcheck` command against the unexposed
metrics listener, and Nginx probes execute wget against loopback `/healthz`.
Neither creates a browser challenge. The Service and NetworkPolicy expose only
Anubis 8080, never metrics 9090 or Nginx 8081.

## Pilot and upgrade checklist

Run make deps, make lint, make test and make validate. Optionally run
`python tests/gateway/smoke.py` with Podman and local TCP access; it uses exact
images with a mock backend, not actual Skosmos. See tests/gateway/README.md.

Before switching from the external proxy, compare all namespace redirects,
Accept negotiation and query-string/escaped-identifier cases to production.
Test real browsers/challenge completion, machine clients, CORS, canonical HTTPS
links, source IP handling, signing-key continuity and bbolt restart on the actual
CSI driver. Configure ingress peers and keep the previous proxy available for
traffic rollback. Changing the ingress name/backend replaces the old direct
Skosmos route; plan the controller reconciliation interval.

Swagger remains separately configurable but a separate Swagger ingress bypasses
Anubis. It defaults off and rendering requires explicit
`swagger.ingress.allowAnubisBypass: true` to enable that path. This exception is
for Swagger UI only; it cannot create a direct Skosmos/Varnish ingress. The
development Swagger and Fuseki administrative hosts are private DNS names and
are restricted by the NGINX source CIDRs documented in
[admin-endpoints.md](admin-endpoints.md).
