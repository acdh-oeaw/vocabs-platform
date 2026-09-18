[main]
# Review this policy against the deployed Jena/Fuseki version before production use.

[users]
{{ .Values.fuseki.auth.initialUsername }} = {{ .authInitialPassword }}, admin

[roles]
admin = *

[urls]
/$/ping = anon
/$/** = authcBasic,roles[admin]
/** = anon
