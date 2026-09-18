# Administrative endpoints

The development deployment has one normal public application endpoint:

`https://vocabs-platform-dev.acdh-dev.oeaw.ac.at/`

Fuseki and Swagger are **internal/private administrative endpoints**, not public
services:

| Use | URL | Backend | TLS Secret |
| --- | --- | --- | --- |
| Swagger/API UI | `https://vocabsapi-vp-dev.acdh-dev.oeaw.ac.at/` | Swagger ClusterIP Service | `acdh-prod` / `vocabsapi-vp-dev-tls` |
| Jena/Fuseki administration | `https://jena-vp-dev.acdh-cluster-2.arz.oeaw.ac.at/` | Fuseki ClusterIP Service | `acdh-prod` / `jena-vp-dev-tls` |

Swagger loads its specification same-origin from `/swagger.json`. The Swagger
Ingress routes that exact path to the Skosmos ClusterIP Service, and routes
`/rest/v1` to Skosmos as well so Swagger 2.0's relative `basePath` is not sent
to the Swagger UI container. The public application Ingress and its Anubis
gateway path are unchanged. No CORS headers were added or broadened.

Neither administrative Ingress uses an ingress IP whitelist. Fuseki uses
HTTPS because its administrative interface is authenticated. The intended
access control depends on Apache Shiro plus the actual internal DNS,
ingress-controller and load-balancer topology. An internal-looking hostname is
not proof of private network reachability. Helm does not create DNS records or
externally exposed Services, and Fuseki, Swagger and Varnish remain `ClusterIP`.

## Fuseki authentication

Fuseki authentication uses Apache Shiro. The development deployment enables
the chart-managed initial Secret and expects:

```text
Secret: vocabs-fuseki-shiro
Key: shiro.ini
Mount: /fuseki/shiro.ini
```
The StatefulSet explicitly sets `FUSEKI_BASE=/fuseki`. The database mount is
`/fuseki/databases`, and the read-only Shiro mount is `/fuseki/shiro.ini`.

The chart template [shiro.ini.tpl](../chart/vocabs/files/shiro.ini.tpl) contains
only the non-secret Shiro policy. On the first install, Helm generates a
cryptographically random 48-character alphanumeric password and creates
`Secret/vocabs-fuseki-shiro` with `shiro.ini`. The initial username defaults to
`admin` and is not secret. No generated password, password hash or Secret data
is stored in Git, values, ConfigMaps, images or NOTES.

The managed Secret uses `helm.sh/resource-policy: keep`, so uninstall leaves
the credential Secret behind. This prevents accidental credential loss and
allows a later install to preserve it. A later Helm upgrade uses `lookup` and
retains the existing `shiro.ini` data exactly; it does not generate a new
password. If a managed Secret exists without the configured key, rendering
fails instead of replacing it.

After installation, replace the generated credentials with a locally reviewed
Shiro file and restart Fuseki:

```bash
kubectl -n vocabs-platform-dev create secret generic vocabs-fuseki-shiro \
	--from-file=shiro.ini=./shiro.ini \
	--dry-run=client -o yaml | kubectl apply -f -
kubectl -n vocabs-platform-dev rollout restart \
	statefulset/vocabs-platform-dev-vocabs-fuseki
```

Do not edit `/fuseki/shiro.ini` inside a Pod. The read-only `subPath` mount is
not a durable credential-management mechanism. Secret `data` is base64 encoded;
`kubectl edit secret vocabs-fuseki-shiro` is possible, but a reviewed local file
and replacement command is preferred. To inspect the generated file, use a
secure administrative shell only because this reveals credential material:

```bash
kubectl -n vocabs-platform-dev get secret vocabs-fuseki-shiro \
	-o jsonpath='{.data.shiro\.ini}' | base64 --decode
```

The reusable chart also supports an external Secret: set
`fuseki.auth.secret.create: false` and provide
`fuseki.auth.secret.existingSecret`, leaving `secret.name` empty. Managed mode
requires `create: true` and an empty `existingSecret`; both modes reject
ambiguous configuration.

Review the legacy Shiro configuration against the Jena/Fuseki 5.4.0 runtime
before migrating it unchanged. Prefer password hashes over plaintext passwords
where supported. The supplied policy must leave `/$/ping` anonymously usable
for Kubernetes startup/readiness/liveness probes while protecting the GUI and
administrative APIs according to the reviewed policy. Helm does not impose or
rewrite that policy.

The Secret is mounted read-only. Secret content changes require either bumping
`fuseki.auth.revision` in the release values or explicitly restarting the
Fuseki StatefulSet. The revision is a pod annotation only; Helm does not hash
or hot-reload the Secret.

After deployment, operators can inspect the Fuseki startup logs without
printing Secret contents:

```bash
kubectl -n vocabs-platform-dev logs statefulset/<release>-vocabs-fuseki -c fuseki | grep -E 'FUSEKI_BASE|shiro\.ini|Fuseki base'
```

The output should indicate a Fuseki base equivalent to `/fuseki` and that Shiro
loaded `/fuseki/shiro.ini`. This repository does not claim that runtime check
has passed until the updated chart is deployed.

The live Skosmos 3.3 endpoint was verified at the public application host:
`GET /swagger.json` returned HTTP 200 with a Swagger 2.0 JSON document. The
document has `basePath: /rest/v1` and no `host` or `servers` field, so Swagger UI
uses its current origin for Try it out requests; the `/rest/v1` Ingress path
therefore sends those requests to Skosmos rather than the UI container. The
document itself is not rewritten, so its API base metadata remains unchanged.

NetworkPolicy remains disabled in the development pilot. If enabled later,
explicit policy must allow the NGINX ingress controller to reach Fuseki,
Swagger, and Skosmos for the `/swagger.json` and `/rest/v1` proxy paths.

## Anubis signing key

The development chart also creates `Secret/vocabs-platform-anubis-signing` on
first install. Its key is `ed25519-private-key-hex`; the generated value is a
32-byte Ed25519 seed represented by 64 lowercase hexadecimal characters. The
Anubis v1.27.0 source verifies this format by hex-decoding the value and
requiring `ed25519.SeedSize` before constructing the private key.

The chart generates the initial key with 32 bytes from Helm/Sprig `randBytes`
and hashes those random bytes with `sha256sum`, yielding a 256-bit, 64-character
lowercase hexadecimal seed. The private key is never stored in Git, values,
ConfigMaps, NOTES, labels, annotations or Pod literals.

The signing Secret supports the same managed/external model as Fuseki Shiro:
`create: true` creates and preserves it; `create: false` requires
`existingSecret` and leaves Secret creation to the operator. On a live Helm
upgrade, `lookup` reuses existing Secret data exactly. A managed Secret missing
the configured key causes rendering to fail rather than silently rotating it.
The managed Secret has `helm.sh/resource-policy: keep`, so uninstall leaves it
in place; deleting the namespace deletes it, and a new namespace gets a new
key.

Anubis uses this Ed25519 key for authentication JWT/cookie signing. An explicit
rotation requires replacing the Secret and restarting the Gateway; existing
Anubis tokens will then be invalid. Ordinary upgrades and Pod restarts do not
rotate the key.