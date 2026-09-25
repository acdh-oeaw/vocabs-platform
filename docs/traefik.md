# Traefik Ingress migration

The development release uses Kubernetes `Ingress` resources with
`ingressClassName: traefik`. Traefik must run the Kubernetes Ingress provider and
watch the release namespace. The gateway still runs its own Nginx container for
application redirects; changing the cluster Ingress controller does not replace
that container.

## 1. Check the cluster (read-only)

Run from the repository root. Confirm the IngressClass is managed by Traefik,
that `acdh-prod` can renew certificates through the new controller, and that
the current release and TLS Secrets exist. If your IngressClass has another
name, update **all four** `className` entries in the environment file first.

```bash
export NS=vocabs-platform-dev
export RELEASE=vocabs-platform-dev
export VALUES=environments/vocabs-platform-dev.yaml
kubectl get ingressclass
kubectl get ingressclass traefik -o yaml
kubectl get clusterissuer acdh-prod -o yaml
kubectl -n "$NS" get ingress,certificate
kubectl -n "$NS" get secret vocabs-platform-dev-tls vocabsapi-vp-dev-tls \
  jena-vp-dev-tls vocabs-downloads-vp-dev-tls
helm list -n "$NS"
helm get values "$RELEASE" -n "$NS" -o yaml
```

Verify the issuer's HTTP-01 solver IngressClass and Traefik HTTP entrypoint
before relying on renewal. The existing `cert-manager.io/cluster-issuer`
annotations and TLS Secret names are retained. If Traefik uses nondefault
entrypoints, set the correct `traefik.ingress.kubernetes.io/router.entrypoints`
annotation in each enabled Ingress's `annotations` values; do not guess names.
For environments with NetworkPolicy enabled, replace
`networkPolicy.gatewayIngressPeers` with selectors for the **actual Traefik
Pods and namespace**. Swagger's Skosmos backend needs matching peers in
`networkPolicy.skosmosAdditionalPeers`; Fuseki administration needs them in
`networkPolicy.fusekiAdditionalPeers`. Inspect the actual controller and CNI
topology before enabling the policies.

## 2. Review the rendered change (read-only)

The API host has two Ingress objects. One serves Swagger and `/rest/v1/` API
calls; the second gives the exact `/rest/v1` and `/rest/v1/` gateway redirects
higher Traefik priority. Traefik does not guarantee an exact path outranks an
overlapping prefix without explicit priority. Only the first Ingress has the
cert-manager issuer annotation, avoiding competing Certificate ownership for
their shared TLS Secret. Both present the same TLS host and Secret.
The chart reserves `traefik.ingress.kubernetes.io/router.priority` on the
Swagger host so the exact redirects cannot silently lose precedence.

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

Expect five Ingress objects, all on `traefik`: gateway, downloads, Fuseki,
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
[Ingress annotations](https://doc.traefik.io/traefik/reference/routing-configuration/kubernetes/ingress/)
and [cert-manager Ingress annotations](https://cert-manager.io/docs/usage/ingress/).
