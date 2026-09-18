# Administrative endpoints

The development deployment has one normal public application endpoint:

`https://vocabs-platform-dev.acdh-dev.oeaw.ac.at/`

Fuseki and Swagger are **internal/private administrative endpoints**, not public
services:

| Use | URL | Backend | TLS Secret |
| --- | --- | --- | --- |
| Swagger/API UI | `https://vocabsapi-vp-dev.acdh-dev.oeaw.ac.at/` | Swagger ClusterIP Service | `acdh-prod` / `vocabsapi-vp-dev-tls` |
| Jena/Fuseki administration | `http://jena-vp-dev.acdh-cluster-2.arz.oeaw.ac.at/` | Fuseki ClusterIP Service | None; HTTP-only |

Swagger loads its specification same-origin from `/swagger.json`. The Swagger
Ingress routes that exact path to the Skosmos ClusterIP Service, and routes
`/rest/v1` to Skosmos as well so Swagger 2.0's relative `basePath` is not sent
to the Swagger UI container. The public application Ingress and its Anubis
gateway path are unchanged. No CORS headers were added or broadened.

Neither administrative Ingress uses an ingress IP whitelist. Fuseki has no
cert-manager certificate and no TLS configuration. The intended access control
now depends on the actual internal DNS, ingress-controller and load-balancer
topology. An internal-looking hostname is not proof of private network
reachability; operators must ensure that DNS and the selected `nginx` ingress
load balancer expose it only as intended. Helm does not create DNS records or
externally exposed Services, and Fuseki, Swagger and Varnish remain `ClusterIP`.

The live Skosmos 3.3 endpoint was verified at the public application host:
`GET /swagger.json` returned HTTP 200 with a Swagger 2.0 JSON document. The
document has `basePath: /rest/v1` and no `host` or `servers` field, so Swagger UI
uses its current origin for Try it out requests; the `/rest/v1` Ingress path
therefore sends those requests to Skosmos rather than the UI container. The
document itself is not rewritten, so its API base metadata remains unchanged.

NetworkPolicy remains disabled in the development pilot. If enabled later,
explicit policy must allow the NGINX ingress controller to reach Fuseki,
Swagger, and Skosmos for the `/swagger.json` and `/rest/v1` proxy paths.