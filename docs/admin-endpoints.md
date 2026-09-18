# Administrative endpoints

The development deployment has one normal public application endpoint:

`https://vocabs-platform-dev.acdh-dev.oeaw.ac.at/`

Fuseki and Swagger are **internal/private administrative endpoints**, not public
services:

| Use | URL | Backend | TLS Secret |
| --- | --- | --- | --- |
| Fuseki administration | `https://jena-vp-dev.acdh-dev.oeaw.ac.at/` | Fuseki ClusterIP Service | `jena-vp-dev-tls` |
| Swagger/API documentation | `https://vocabsapi-vp-dev.acdh-dev.oeaw.ac.at/` | Swagger ClusterIP Service | `vocabsapi-vp-dev-tls` |

Both administrative Ingress resources use the `nginx` IngressClass and the exact
NGINX whitelist `10.4.24.0/24,10.4.245.0/24`. Fuseki is not routed through
Anubis or the public Gateway. Fuseki, Swagger and Varnish remain `ClusterIP`;
Helm does not create DNS records or externally exposed Services.

The two administrative names must be supplied by the organization's
internal/private DNS only. DNS privacy is not by itself network isolation. This
repository cannot inspect the cluster's NGINX Service or load balancer, so the
deployment team must verify whether the selected `nginx` controller uses an
internal/private load balancer. If it is publicly reachable, the names remain
intentionally absent from public DNS and NGINX CIDR filtering is an additional
control, but the load balancer may still be reachable from outside those DNS
zones. Network-level private exposure would require an internal controller or
load balancer and is outside this chart.

The whitelist is trustworthy only when ingress-nginx receives the real client
source address. Verify on the cluster whether source preservation is direct,
via trusted `X-Forwarded-For`, PROXY protocol, or another trusted proxy setup;
this repository cannot verify that controller/load-balancer configuration and
does not change it.

The `acdh-prod` ClusterIssuer owns the three TLS Secrets. The issuer's HTTP-01
or DNS-01 solver mode must be checked in the cluster. If it uses HTTP-01, the
certificate solver must remain reachable without weakening either administrative
whitelist or public application ingress to `0.0.0.0/0`. Provision the two
private DNS names and validate issuance before relying on these endpoints.

NetworkPolicy remains disabled in the development pilot. If enabled later,
explicit policy must allow the NGINX ingress controller to reach both Fuseki and
Swagger; this chart does not infer controller identity or add those peers.