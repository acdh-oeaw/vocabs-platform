# Environment values

`example.yaml` is renderable, explicitly non-production configuration. Replace
CHANGE-ME storage/ingress/TLS values, global.publicUrl, and source paths before
installation. No credentials belong here. Supply existing Kubernetes Secret names
for image pulls (`imagePullSecrets`, and upstream `global.imagePullSecrets`) and
TLS. Varnish management credentials, if needed, use the upstream
`varnish.server.secretFrom: {name: ..., key: ...}`; never set a literal secret.
Fuseki's supplied query-only assembler needs no public administration credentials.

Use one environment file and one Helm release per namespace. Choose distinct
PVC names if running more than one release in a namespace. Keep the active claim,
revision and Varnish revision annotation synchronized; activation examples show
all three. Never persist an import-enabled overlay as normal release values.
Commit safe configuration metadata; keep private local values in ignored
`environments/local*.yaml` or your deployment secret/config system.

The example enables the gateway; generic values keep it disabled. Set the actual
controller peer selectors under networkPolicy.gatewayIngressPeers or gateway
traffic will be denied by an enforcing CNI. The URL must end in `/` and use the
root path; ingress.host is no longer supported. Validate external Skosmos
baseHref against global.publicUrl before applying the ConfigMap. Public ingress
requires an existing Anubis signing-key Secret separately from
the state PVC. Replace the example Secret name and provision its key before
installation; backend-only rendering may omit it. See docs/gateway.md for the
key format and trust requirements.
