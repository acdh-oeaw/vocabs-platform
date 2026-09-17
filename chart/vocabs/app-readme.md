# ACDH Vocabs

Development pilot: Anubis/Nginx gateway, Skosmos, Varnish and single-writer Fuseki.
This chart is not yet production certified.

Configure installation through the values YAML editor. `values.yaml` and
`values.schema.json` are authoritative; no Rancher-specific configuration is
required. Varnish is bundled in the package.

Before enabling public ingress, prepare the public URL, ingress class, TLS
Secret, persistent Anubis signing Secret, Skosmos ConfigMap, and storage claims.
Configure NetworkPolicy peers for the actual ingress controller. Keep imports
disabled during installation; use the documented candidate import workflow.

See the [Rancher pilot guide](https://github.com/acdh-oeaw/vocabs-platform/blob/main/docs/rancher.md)
for installation values, prerequisites and operational runbooks.
