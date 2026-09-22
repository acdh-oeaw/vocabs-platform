{{- define "vocabs.fullname" -}}
{{- default (printf "%s-%s" .Release.Name (default .Chart.Name .Values.nameOverride)) .Values.fullnameOverride | trunc 46 | trimSuffix "-" -}}
{{- end -}}
{{- define "vocabs.labels" -}}
{{- with .Values.commonLabels }}{{ toYaml . }}{{ end }}
app.kubernetes.io/name: vocabs
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/version: {{ .Values.stack.version | quote }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | quote }}
{{- end -}}
{{- define "vocabs.selector" -}}
app.kubernetes.io/name: vocabs
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
{{- define "vocabs.sa" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "vocabs.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}
{{- define "vocabs.fusekiAuthSecretName" -}}
{{- if .Values.fuseki.auth.secret.create -}}
{{- default (printf "%s-fuseki-shiro" (include "vocabs.fullname" .)) .Values.fuseki.auth.secret.name -}}
{{- else -}}
{{- .Values.fuseki.auth.secret.existingSecret -}}
{{- end -}}
{{- end -}}
{{- define "vocabs.anubisSigningSecretName" -}}
{{- if .Values.gateway.anubis.signingKey.secret.create -}}
{{- default (printf "%s-anubis-signing" (include "vocabs.fullname" .)) .Values.gateway.anubis.signingKey.secret.name -}}
{{- else -}}
{{- .Values.gateway.anubis.signingKey.secret.existingSecret -}}
{{- end -}}
{{- end -}}
{{- define "vocabs.profile" -}}
{{- $profiles := (.Files.Get "compatibility.yaml" | fromYaml).profiles -}}
{{- $version := required "stack.version is required" .Values.stack.version -}}
{{- if not (hasKey $profiles $version) }}{{ fail (printf "Unknown stack profile: %s" $version) }}{{ end -}}
{{- $p := deepCopy (index $profiles $version) -}}
{{- if ne $p.jena.version $p.importer.jenaVersion }}{{ fail "Profile runtime and importer Jena versions must match" }}{{ end -}}
{{- $o := .Values.compatibility.overrides -}}
{{- if and (not .Values.compatibility.allowUnsupported) (or $o.skosmosVersion $o.jenaVersion $o.storageEngine $o.imageRevision .Values.skosmos.image.tag .Values.fuseki.image.tag .Values.imports.image.tag) -}}
{{- fail "Manual overrides require compatibility.allowUnsupported=true (testing only)" -}}
{{- end -}}
{{- if $o.jenaVersion }}{{ $_ := set $p.jena "version" $o.jenaVersion }}{{ $_ := set $p.importer "jenaVersion" $o.jenaVersion }}{{ end -}}
{{- if $o.skosmosVersion }}{{ $_ := set $p.skosmos "version" $o.skosmosVersion }}{{ end -}}
{{- if $o.storageEngine }}{{ $_ := set $p.storage "engine" $o.storageEngine }}{{ end -}}
{{- if $o.imageRevision }}{{ $_ := set $p "imageRevision" $o.imageRevision }}{{ end -}}
{{- toYaml $p -}}
{{- end -}}
{{- define "vocabs.image" -}}
{{- $p := include "vocabs.profile" .root | fromYaml -}}
{{- $v := $p.jena.version -}}
{{- $revision := $p.imageRevision -}}
{{- if eq .component "skosmos" }}{{ $v = $p.skosmos.version }}{{ $revision = default $p.imageRevision $p.skosmos.imageRevision }}{{ end -}}
{{- if eq .component "imports" }}{{ $v = $p.importer.jenaVersion }}{{ $revision = default $p.imageRevision $p.importer.imageRevision }}{{ end -}}
{{- $tag := default (printf "%s-%s" $v $revision) .image.tag -}}
{{- if not (regexMatch "^[0-9]+[.][0-9]+.*" $tag) }}{{ fail "Image tags must start with an explicit version" }}{{ end -}}
{{- printf "%s:%s" .image.repository $tag -}}
{{- end -}}
{{/* Vinyl VCL uses explicit global Fuseki backend values, checked against the parent service. */}}
{{- define "vocabs.vcl" -}}
vcl 4.1;
backend default {
  .host = "{{ default (printf "%s-vocabs-fuseki" .Release.Name) .Values.global.vocabsFusekiHost }}";
  .port = "{{ .Values.global.vocabsFusekiPort }}";
}
sub vcl_recv {
  if (req.url == "/healthz") { return (synth(200, "OK")); }
  # Only expose the read-only SPARQL query endpoint through this proxy.
  if (req.url !~ "^/skosmos/(sparql|query)([?]|$)") { return (synth(403)); }
  if (req.method != "GET" && req.method != "HEAD" && req.method != "POST") { return (synth(405)); }
  if (req.method == "POST" || req.http.Authorization || req.http.Cookie) { return (pass); }
}
sub vcl_backend_response {
  if (beresp.status != 200 || beresp.http.Set-Cookie) { set beresp.uncacheable = true; return (deliver); }
  set beresp.ttl = 120s;
  set beresp.grace = 0s;
}
{{- end -}}

{{/* Root-only public URL: no userinfo/query/fragment, DNS host, optional port, trailing /. */}}
{{- define "vocabs.public" -}}
{{- $raw := .Values.global.publicUrl -}}
{{- if not (regexMatch "^https?://[a-z0-9]([a-z0-9.-]*[a-z0-9])?(:[0-9]{1,5})?/$" $raw) -}}
{{- fail "global.publicUrl must be an absolute http(s) root URL with a DNS hostname and trailing / (no userinfo, query or fragment)" -}}
{{- end -}}
{{- $u := urlParse $raw -}}
{{- $parts := splitList ":" $u.host -}}
{{- $host := first $parts -}}
{{- if gt (len $host) 253 }}{{ fail "global.publicUrl hostname is too long" }}{{ end -}}
{{- range splitList "." $host -}}
{{- if or (gt (len .) 63) (not (regexMatch "^[a-z0-9]([a-z0-9-]*[a-z0-9])?$" .)) }}{{ fail "global.publicUrl has an invalid DNS hostname" }}{{ end -}}
{{- end -}}
{{- if eq (len $parts) 2 -}}
{{- if or (lt (int (last $parts)) 1) (gt (int (last $parts)) 65535) }}{{ fail "global.publicUrl port must be between 1 and 65535" }}{{ end -}}
{{- end -}}
{{- toYaml (dict "url" $raw "scheme" $u.scheme "host" $host "authority" $u.host) -}}
{{- end -}}
