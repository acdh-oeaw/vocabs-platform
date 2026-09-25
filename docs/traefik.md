# RKE2 Traefik Ingress routing

The development release uses Kubernetes `Ingress` resources with
`ingressClassName: nginx`. In this cluster HAProxy forwards to RKE2 Traefik,
and the `nginx` class serves the development hosts; switching the same routes
to class `traefik` returned HTTP 404. RKE2 can configure Traefik with an
Ingress NGINX compatibility provider. Check the live IngressClass/controller
configuration before assuming which provider handles a class. The gateway's
Nginx container still handles application redirects inside its Pod.

## 1. Check the cluster (read-only)

Run from the repository root. Compare the class and host of a working Ingress
with these values. Confirm that `acdh-prod` can renew certificates, and that
the current release and TLS Secrets exist. Keep class `nginx` until another
class has been tested end to end through HAProxy.

```bash
export NS=vocabs-platform-dev
export RELEASE=vocabs-platform-dev
export VALUES=environments/vocabs-platform-dev.yaml
kubectl get ingressclass
kubectl get ingressclass nginx -o yaml
kubectl get ingress -A -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,CLASS:.spec.ingressClassName,HOST:.spec.rules[0].host'
kubectl get clusterissuer acdh-prod -o yaml
kubectl -n "$NS" get ingress,certificate
kubectl -n "$NS" get secret vocabs-platform-dev-tls vocabsapi-vp-dev-tls \
  jena-vp-dev-tls vocabs-downloads-vp-dev-tls
helm list -n "$NS"
helm get values "$RELEASE" -n "$NS" -o yaml
```

Verify the issuer's HTTP-01 solver class and the route to the correct Traefik
entrypoint before relying on renewal. The existing
`cert-manager.io/cluster-issuer` annotations and TLS Secret names are retained.
Do not add native Traefik routing annotations solely because Traefik runs in
the cluster: confirm which provider processes this IngressClass first.
For environments with NetworkPolicy enabled, replace
`networkPolicy.gatewayIngressPeers` with selectors for the **actual Traefik
Pods and namespace**. Swagger's Skosmos backend needs matching peers in
`networkPolicy.skosmosAdditionalPeers`; Fuseki administration needs them in
`networkPolicy.fusekiAdditionalPeers`. Inspect the actual controller and CNI
topology before enabling the policies.

## 2. Review the rendered change (read-only)

The API host has two Ingress objects. One serves Swagger and `/rest/v1/` API
calls; the second serves exact `/rest/v1` and `/rest/v1/` gateway redirects.
The extra Ingress carries a priority annotation for Traefik's native Ingress
provider; the NGINX compatibility provider may handle precedence differently,
so test both exact URLs and an API subpath. Only the first Ingress has the
cert-manager issuer annotation. Both use the same TLS host and Secret.

```bash
helm lint ./chart/vocabs -f "$VALUES"
helm template "$RELEASE" ./chart/vocabs -n "$NS" -f "$VALUES" \
  > /tmp/vocabs-traefik.yaml
python3 - /tmp/vocabs-traefik.yaml <<'PY'
import sys, yaml
for item in yaml.safe_load_all(open(sys.argv[1])):
    if item and item.get('kind') == 'Ingress':
        print(item['metadata']['name'], item['spec'].get('ingressClassName'),
              item['spec']['rules'][0]['host'],
              [(path['path'], path['pathType'])
               for path in item['spec']['rules'][0]['http']['paths']])
PY
```

Expect five Ingress objects, all on `nginx`: gateway, downloads, Fuseki,
Swagger and its exact redirect routes. Compare hosts, TLS Secrets and backend
Services against the current release. Keep the existing Redmine IDs.

## 3. Deploy after review (cluster changes)

Use the reviewed chart version when it has been published, or the local chart
from the checked-out commit. An Ingress change should not restart the
application Pods. After deployment, inspect the routes and Certificates:

```bash
helm upgrade "$RELEASE" ./chart/vocabs -n "$NS" -f "$VALUES" \
  --wait --timeout=10m
kubectl -n "$NS" get ingress -o wide
kubectl -n "$NS" get certificate
kubectl -n "$NS" get endpointslices
```

Check the gateway, Swagger UI, API prefix and exact redirect over HTTPS. For
downloads, supply a real known dump path: Apache may reject directory listing
at `/`. Anubis may challenge command-line clients on the main site; verify it
with a browser if the first request is challenged. Check the private Fuseki URL
only from an authorized network.

```bash
curl -sSI https://vocabs-platform-dev.acdh-dev.oeaw.ac.at/en/
curl -fsSL https://vocabsapi-vp-dev.acdh-dev.oeaw.ac.at/ -o /dev/null
curl -fsSL https://vocabsapi-vp-dev.acdh-dev.oeaw.ac.at/swagger.json -o /dev/null
curl -fsSI https://vocabsapi-vp-dev.acdh-dev.oeaw.ac.at/rest/v1
curl -fsSL https://vocabsapi-vp-dev.acdh-dev.oeaw.ac.at/rest/v1/vocabularies -o /dev/null
export DUMP_PATH=/REPLACE-WITH-KNOWN-DUMP-PATH
curl -fsSI "https://vocabs-downloads-vp-dev.acdh-dev.oeaw.ac.at${DUMP_PATH}"
```

The exact API redirect must land on the Swagger UI; `/rest/v1/vocabularies`
must reach Skosmos. If a host fails, inspect its Ingress, matching Service,
EndpointSlices, Traefik logs and the relevant Certificate. A working Pod alone
does not prove that the new IngressClass, DNS, TLS or routing is correct.

See the [Traefik Kubernetes Ingress provider](https://doc.traefik.io/traefik/reference/install-configuration/providers/kubernetes/kubernetes-ingress/),
[RKE2 migration guide](https://docs.rke2.io/reference/ingress_migration),
[Ingress NGINX compatibility provider](https://doc.traefik.io/traefik/reference/install-configuration/providers/kubernetes/kubernetes-ingress-nginx/)
and [cert-manager Ingress annotations](https://cert-manager.io/docs/usage/ingress/).
