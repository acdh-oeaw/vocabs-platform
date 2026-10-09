# Development Ingress on Traefik

The dev values select `ingressClassName: traefik` for the gateway, Fuseki admin,
Swagger and downloads. Each has the Traefik TLS router annotation and keeps its
existing certificate Secret and cert-manager issuer. Each certificate-producing
Ingress requests `traefik` for the cert-manager HTTP-01 solver. The public gateway
Ingress also uses `kube-system-global-error-pages@kubernetescrd`, matching the
existing GitLab Helm overrides. The Nginx container inside the gateway Pod remains
responsible for application redirects and headers.

## Check the cluster before upgrading

Run from a workstation with access to the dev Kubernetes context. The class
must be watched by the native Traefik Kubernetes Ingress provider, and DNS and
the external load balancer must reach that Traefik instance. Check the
`acdh-prod` HTTP-01 solver class before relying on certificate renewal.

```bash
kubectl get ingressclass -o custom-columns=NAME:.metadata.name,CONTROLLER:.spec.controller
kubectl get ingressclass traefik -o yaml
kubectl get clusterissuer acdh-prod -o yaml
kubectl -n kube-system get middleware global-error-pages
kubectl get validatingwebhookconfigurations -o name
kubectl -n vocabs-platform-dev get ingress,certificate
helm get values vocabs-platform-dev -n vocabs-platform-dev -o yaml \
  > /tmp/vocabs-values-before-traefik.yaml
helm history vocabs-platform-dev -n vocabs-platform-dev --max 3
```

Confirm Traefik permits the gateway Ingress in `vocabs-platform-dev` to use the
`global-error-pages` Middleware from `kube-system`; a cross-namespace middleware
reference depends on the installed Traefik provider configuration. An old NGINX
admission webhook can still reject overlapping host/path routes
even after its controller is replaced. Remove or reconfigure that webhook at
the cluster level before this chart is applied. Preserve any live values not
represented in `environments/vocabs-platform-dev.yaml`; imports must remain off.
If the actual class has another name, update all four dev `className` values.
If Traefik uses nondefault HTTPS entrypoints, set the appropriate
`traefik.ingress.kubernetes.io/router.entrypoints` on all four Ingresses after
checking the controller configuration.

The cert-manager issuer and HTTP-01 solver class annotations remain only on the
main Swagger Ingress; the second Ingress shares its TLS Secret without requesting
another Certificate. The global error-pages middleware is applied to the public
gateway Ingress only.
If NetworkPolicy is enabled later, set peer selectors for the actual Traefik
Pods in `networkPolicy.gatewayIngressPeers`, `skosmosAdditionalPeers` and
`fusekiAdditionalPeers` as appropriate.

## Inspect and test the manifests

```bash
umask 077
helm lint ./chart/vocabs -f environments/vocabs-platform-dev.yaml
helm template vocabs-platform-dev ./chart/vocabs -n vocabs-platform-dev \
  -f environments/vocabs-platform-dev.yaml > /tmp/vocabs-traefik.yaml
python3 - <<'PY' > /tmp/vocabs-traefik-ingresses.yaml
import yaml
with open('/tmp/vocabs-traefik.yaml') as rendered:
    for item in yaml.safe_load_all(rendered):
        if item and item.get('kind') == 'Ingress':
            print('---')
            print(yaml.safe_dump(item), end='')
PY
kubectl -n vocabs-platform-dev apply --dry-run=server \
  -f /tmp/vocabs-traefik-ingresses.yaml
```

Expect five Ingress resources: gateway, Fuseki admin, downloads and two for
Swagger. The main Swagger Ingress routes `/swagger.json` and the `/rest/v1/`
prefix to Skosmos. The second routes exact `/rest/v1` and `/rest/v1/` to the
gateway with Traefik priority 1000, so redirects outrank the API prefix.
Traefik does not guarantee that an Exact path wins over an overlapping Prefix
route by default. The split is used only for class `traefik`; other classes
keep the original single Swagger Ingress and route list.

The server-side dry run checks cluster admission, including any remaining
NGINX validation webhook. If it fails, review its message before upgrading.
The complete rendered manifest may contain generated Secret data; keep it
private and delete it when the inspection is complete.

## Try the dev release

Use the reviewed live values if they differ from the tracked dev file. The
following command assumes that the tracked values are complete and current:

```bash
helm upgrade vocabs-platform-dev ./chart/vocabs -n vocabs-platform-dev \
  -f environments/vocabs-platform-dev.yaml --atomic --wait --timeout 10m
kubectl -n vocabs-platform-dev get ingress -o wide
kubectl -n vocabs-platform-dev get certificate
```

Check the public page with a browser if Anubis challenges `curl`, and inspect
both exact API redirects and a real API subpath. Use a known dump file for the
downloads host; the root path may not list files. Test the Fuseki host only
from an authorized network.

```bash
curl -sS -D - -o /dev/null https://vocabsapi-vp-dev.acdh-dev.oeaw.ac.at/rest/v1
curl -sS -D - -o /dev/null https://vocabsapi-vp-dev.acdh-dev.oeaw.ac.at/rest/v1/
curl -sS -D - -o /dev/null https://vocabsapi-vp-dev.acdh-dev.oeaw.ac.at/rest/v1/vocabularies
curl -sS -D - -o /dev/null https://vocabsapi-vp-dev.acdh-dev.oeaw.ac.at/swagger.json
```

If routing is wrong after an otherwise successful Helm upgrade, use the
previous revision number from `helm history` to roll back:

```bash
helm rollback vocabs-platform-dev PREVIOUS_REVISION -n vocabs-platform-dev \
  --wait --timeout 10m
```

See [Traefik Kubernetes Ingress routes](https://doc.traefik.io/traefik/reference/routing-configuration/kubernetes/ingress/)
and [cert-manager Ingress annotations](https://cert-manager.io/docs/usage/ingress/).
