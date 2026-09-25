# Environment values

Operators should use the [step-by-step guide](../docs/operator-guide.md) to
generate local values for an import instead of hand-editing multiple YAML files.

`example.yaml` is renderable, explicitly non-production configuration. Replace
CHANGE-ME storage/ingress/TLS values, global.publicUrl, and source paths before
installation. No credentials belong here. Supply existing Kubernetes Secret names
for image pulls (`imagePullSecrets`, and upstream `global.imagePullSecrets`) and
TLS. Vinyl Cache is managed directly by the parent chart and does not expose
management credentials through environment values.
The development file uses class `nginx` on all four Ingress settings: this is
the class that works through this cluster's HAProxy → Traefik setup. The class
name does not identify which controller handles it. See the
[routing checks](../docs/traefik.md) before changing the class.
Fuseki's supplied query-only assembler needs no public administration credentials.

Use one environment file and one Helm release per namespace. Choose distinct
PVC names if running more than one release in a namespace. Keep the active claim,
revision and Vinyl Cache revision annotation synchronized; activation examples show
all three. Never persist an import-enabled overlay as normal release values.
Commit safe configuration metadata; keep private local values in ignored
`environments/local*.yaml` or your deployment secret/config system.

Downloads Deployment and Service are always present. Configure
`downloads.ingress.enabled`, `host`, `className`, `redmineId` and TLS for
each public environment. Set a distinct dev hostname; keep
`vocabs-downloads.acdh.oeaw.ac.at` for production. Pin
`downloads.image.digest` to the published multi-platform image index.
When NetworkPolicy is enabled, `networkPolicy.gatewayIngressPeers` also
controls access to downloads.

The example enables the gateway; generic values keep it disabled. Set the actual
controller peer selectors under networkPolicy.gatewayIngressPeers or gateway
traffic will be denied by an enforcing CNI. The URL must end in `/` and use the
root path; ingress.host is no longer supported. Validate external Skosmos
baseHref against global.publicUrl before applying the ConfigMap. Public ingress
requires an existing Anubis signing-key Secret separately from
the state PVC. Replace the example Secret name and provision its key before
installation; backend-only rendering may omit it. See docs/gateway.md for the
key format and trust requirements.
