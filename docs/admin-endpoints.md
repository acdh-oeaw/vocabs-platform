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

Fuseki authentication uses Apache Shiro and an externally managed Kubernetes
Secret. The development deployment expects:

```text
Secret: vocabs-fuseki-shiro
Key: shiro.ini
Mount: /fuseki/shiro.ini
```
The published Fuseki image was inspected and uses `WORKDIR=/fuseki` without a
separate `FUSEKI_BASE` environment variable; Fuseki therefore uses `/fuseki`
as its runtime base directory here.

The chart never stores credentials, password hashes or `shiro.ini` content.
Create the Secret separately, for example:

```bash
kubectl -n vocabs-platform-dev create secret generic \
	vocabs-fuseki-shiro \
	--from-file=shiro.ini=./shiro.ini
```

Review the legacy Shiro configuration against the Jena/Fuseki 5.4.0 runtime
before migrating it unchanged. Prefer password hashes over plaintext passwords
where supported. The supplied policy must leave `/$/ping` anonymously usable
for Kubernetes startup/readiness/liveness probes while protecting the GUI and
administrative APIs according to the reviewed policy. Helm does not impose or
rewrite that policy.

The Secret is mounted read-only. Secret content changes require either bumping
`fuseki.auth.revision` in the release values or explicitly restarting the
Fuseki StatefulSet. The revision is a pod annotation only; Helm does not hash
the external Secret.

The live Skosmos 3.3 endpoint was verified at the public application host:
`GET /swagger.json` returned HTTP 200 with a Swagger 2.0 JSON document. The
document has `basePath: /rest/v1` and no `host` or `servers` field, so Swagger UI
uses its current origin for Try it out requests; the `/rest/v1` Ingress path
therefore sends those requests to Skosmos rather than the UI container. The
document itself is not rewritten, so its API base metadata remains unchanged.

NetworkPolicy remains disabled in the development pilot. If enabled later,
explicit policy must allow the NGINX ingress controller to reach Fuseki,
Swagger, and Skosmos for the `/swagger.json` and `/rest/v1` proxy paths.