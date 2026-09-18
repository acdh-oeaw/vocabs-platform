# Architecture

The public path is Ingress (TLS) → Gateway Service → Anubis :8080 → localhost
nginx-unprivileged :8081 → Skosmos → Varnish → Fuseki. Ingress is the external
entry point; Anubis filters requests; Nginx handles routing, concept/DARIAH
redirects, CORS and proxy headers; Skosmos serves vocabularies; Varnish caches
SPARQL; Fuseki is the internal RDF database. Only Anubis has a public gateway
Service port. There are no direct Skosmos or Varnish public ingresses; the
optional Fuseki administrative Ingress is separately whitelisted. See
[the administrative endpoint runbook](admin-endpoints.md).

The gateway is one namespaced Deployment with two non-root containers and a
single local bbolt backend on a separate optional retained PVC. Replicas above
one are rejected, and Recreate updates prevent overlapping bbolt writers. Future
HA requires a shared state design; this iteration deploys no Redis/Valkey,
operator, CRDs or cluster controllers. See [the gateway runbook](gateway.md).

`global.publicUrl` is the single public URL input, stored in environment values,
not GitHub variables. It derives ingress hostname, gateway public scheme/host,
redirect targets and generated Skosmos baseHref. External Skosmos ConfigMaps must
be generated/validated against that value using scripts/configmap.sh or
scripts/skosmos-public-url.py; offline Helm cannot inspect their contents.
Ingress must set trusted forwarded headers. Nginx preserves the public scheme
with a canonical fallback, never its internal HTTP scheme. The declarative
namespace and external-redirect lists preserve the requested legacy URI routing;
compare edge cases to the actual old proxy in the pilot.

Swagger's separate ingress is an explicit, documented exception that bypasses
Anubis and requires swagger.ingress.allowAnubisBypass=true. It remains disabled
by default. It does not provide another path to Skosmos or the database.

Skosmos can run two or more replicas. Its configuration is read-only and its Twig
cache is local. Check any migrated plugins for shared/session state before
scaling. Upstream Apache starts as root before dropping worker privileges, so
arbitrary UIDs and dropping all capabilities are not imposed on that image.
Fuseki and importer use UID/GID 1000, filesystem group 1000 and restricted Linux
capabilities. Swagger follows its upstream Nginx startup requirements. No RBAC
permissions are granted; parent workloads disable service account token mounts.
The upstream Varnish chart creates its own service account and uses its default
token mounting behavior; assess this upstream limitation before production.

NetworkPolicies permit configured ingress-controller peers → Gateway, same-release
Gateway → Skosmos, Skosmos → Varnish and Varnish → Fuseki. Empty gateway peers
deny incoming gateway traffic until operators provide actual controller selectors.
Offline imports use PVCs and receive no network exception. Additional peers are
explicit Kubernetes pod/namespace selectors. NetworkPolicies are additive: other
policies can broaden access. Egress is not restricted here; DNS remains usable.
A cluster without an enforcing CNI can install the chart but does not receive
network isolation. There is no assumed ingress-controller namespace.

Fuseki exposes a read-only `skosmos` dataset query service. There are no update,
upload or graph-write endpoints in the supplied assembler. Varnish additionally
allows only query paths and GET/HEAD/POST; POST queries bypass the cache. A custom
VCL supplied through `varnish.server.vclConfig` must preserve the intended read-only
boundary. It is Helm-templated, so values must be trusted deployment configuration.

The official dependency has its own values context. `global.vocabsFusekiHost`
(empty means `<release>-vocabs-fuseki`) and `global.vocabsFusekiPort` are checked
against the parent service. Varnish's data-revision pod annotation must equal
`<activeClaim>/<data.revision>`, enforced during rendering. The profile pins the
Varnish and Swagger image defaults; new profiles must update those dependency
values too, and mismatches fail unless explicitly in unsupported testing mode.

Fuseki's headless service provides StatefulSet identity; its normal ClusterIP
service is the Varnish backend. The database volume is a regular retained PVC,
not a volumeClaimTemplate, so changing `activeClaim` changes the pod template.
A StatefulSet maintains ordering for its one pod, but cannot protect against
operators mounting that claim in a second unrelated workload.
