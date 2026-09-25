# Helm publishing and Rancher installation

For vocabulary imports, migration, routine checks and rollback after the
installation, use the [operator guide](operator-guide.md). This document is for
initial Helm/Rancher setup and chart publication.

The public HTTP Helm repository for both Helm and Rancher is:

```text
https://acdh-oeaw.github.io/vocabs-platform/
```

It becomes available after the first successful release and GitHub Pages
publication. A standard `index.yaml` repository works with native Helm charts;
no special Rancher Operator or custom catalog server is required. See
[Rancher's chart documentation](https://ranchermanager.docs.rancher.com/how-to-guides/new-user-guides/helm-charts-in-rancher/create-apps).
The packaged `app-readme.md` adds brief installation guidance. We intentionally
use the YAML editor rather than duplicate configuration in `questions.yaml`;
`values.yaml` and `values.schema.json` remain authoritative.

## Publishing and versions

Pushes to `main` run `.github/workflows/helm-release.yml`. Its read-only validation
job reuses the existing Helm CI: locked dependency build, lint, rendering and
safety tests, Turtle validation, and strict Kubernetes schema validation.
Only after success does the publishing job receive `contents: write`.
Both jobs use the same checksum-pinned Helm 3.17.3/kubeconform 0.6.7 installer.

The publishing job packages `chart/vocabs`, validates the parent-managed Vinyl
Cache resources, and renders the package with the example values. The official
[chart-releaser-action v1.7.0](https://github.com/helm/chart-releaser-action/tree/cae68fefc6b5f367a0275617c9f83181ba54714f)
is pinned to commit `cae68fefc6b5f367a0275617c9f83181ba54714f` and uses
chart-releaser CLI v1.7.0. `charts_dir: chart` preserves the chart location.
Explicit packaging with `skip_packaging: true` also handles the first release
without depending on changes since an earlier Git tag.

Packages go to GitHub Release assets; `gh-pages/index.yaml` references those
assets. Generated packages and the index are never committed to `main`.
Vinyl Cache is managed directly by the chart, so installers do not need a
separate Helm dependency build. Concurrent releases are serialized.

- `Chart.yaml` **version changes → new Helm/Rancher release**, named
  `vocabs-<version>`. Bump this for every chart change intended for distribution.
- **appVersion changes → software stack version** metadata; select the runtime
  profile using the existing `stack.version` configuration. Changing appVersion
  alone does not publish another package under an existing chart version.
- Version bumps are explicit reviewed Git changes; CI never edits versions.
  `skip_existing: true` preserves existing releases instead of replacing assets.
  The current version `0.2.0-dev.22` remains a prerelease.

The publishing step uses only `secrets.GITHUB_TOKEN`, with no PAT, package-write,
Actions-write, or OIDC permissions. Checkout credentials are not persisted.

## One-time GitHub setup

1. Initialize an independent `gh-pages` branch if it does not exist. It needs an
   initial commit; create it in a disposable clone, not by clearing your working
   checkout. For example, maintainers can run the following in a fresh clone:

   ```bash
   git switch --orphan gh-pages
   touch .nojekyll
   git add .nojekyll
   git commit -m "Initialize Helm repository Pages branch"
   git push origin gh-pages
   ```

   Do not run this initialization over an existing `gh-pages` branch. The
   releaser expects that branch to exist and maintains its index afterwards.
2. Open **Settings → Pages**, select **Deploy from a branch**, then **gh-pages**
   and **/ (root)**. Save. Ensure organization policy permits Pages and Actions,
   and repository rules allow the release job to create `vocabs-*` tags/releases
   and update `gh-pages` with its `contents: write` token.
3. Push the reviewed publishing workflow/chart changes to `main`. Confirm the
   validation and publishing jobs succeed and the release has its `.tgz` asset.
4. Confirm Pages has published the updated index:

   ```bash
   curl -fsSL https://acdh-oeaw.github.io/vocabs-platform/index.yaml
   helm repo add acdh-vocabs https://acdh-oeaw.github.io/vocabs-platform/
   helm repo update
   helm search repo acdh-vocabs
   helm search repo acdh-vocabs --devel
   ```

   `--devel` includes the current prerelease; a plain search may show no charts
   until a stable chart version is released. GitHub documents that commits made
   by `GITHUB_TOKEN` do not trigger a Pages build. If the index on Pages remains
   stale, a maintainer must trigger/re-run the Pages deployment for the updated
   `gh-pages` branch and verify the URL before Rancher synchronization. See
   [GitHub Pages publishing sources](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).
   This workflow does not add broader permissions or a PAT to bypass that limit.

## Downloads

The chart always starts a downloads Deployment and ClusterIP Service from
`ghcr.io/acdh-oeaw/vocabs-dumps@<digest>`. Set the reviewed image index
digest in `downloads.image.digest` for each release. To expose it, configure
`downloads.ingress` with an environment-specific hostname, Redmine ID,
Ingress class and TLS Secret. The dev release uses its own hostname; keep
the existing production hostname and file paths during production cutover.
The downloads endpoint serves Apache directly, without an Anubis challenge.
A new dumps build requires a digest update and Helm upgrade; the legacy
Rancher redeploy step must be retired once Helm owns the production service.
See the [architecture](architecture.md) and [environment values](../environments/README.md).

## Add the repository in Rancher

In the target **Cluster → Apps → Repositories → Create**, choose an **HTTP(S)
Helm repository**, name it `acdh-vocabs`, and enter the URL above. After repository
synchronization, open **Apps → Charts → vocabs → Install**. Enable prerelease
versions if the Rancher version selector filters out `0.2.0-dev`.
Select namespace `vocabs-platform-dev` and use the values YAML editor.

## Development pilot values

Start with `environments/example.yaml` and apply the following overrides to your
installation values. These development settings are not chart defaults.

```yaml
global:
  publicUrl: https://vocabs-platform-dev.acdh-dev.oeaw.ac.at/
ingress:
  enabled: true
  className: nginx
  tls:
    enabled: true
    secretName: CHANGE-ME-TLS-SECRET
gateway:
  enabled: true
  anubis:
    signingKey:
      secret:
        create: true
        name: vocabs-platform-anubis-signing
        existingSecret: ""
        key: ed25519-private-key-hex
    persistence:
      storageClassName: ""
data:
  activeClaim: vocabs-data-r001
  revision: r001
  managedClaims:
    - name: vocabs-data-r001
      storageClassName: ""
      size: 30Gi
      accessModes: [ReadWriteMany]
      retain: true
    - name: vocabs-data-r002
      storageClassName: ""
      size: 30Gi
      accessModes: [ReadWriteMany]
      retain: true
imports:
  job:
    enabled: false
  targetClaim: vocabs-data-r002
  source:
    type: pvc
    pvc:
      existingClaim: vocabs-import
      files:
        - /data/example.ttl
```

Provision the separate shared RDF source PVC `vocabs-import` in namespace
`vocabs-platform-dev` with the cluster default StorageClass, appropriate
capacity and access modes. The chart references this existing source claim;
it does not create it or choose its StorageClass. Database and Anubis storage
use the cluster default StorageClass as shown above.

Replace Secret placeholders with existing namespace-local TLS/signing Secrets.
Generate the Skosmos ConfigMap for this exact public URL, supply verified
platform images, and set `networkPolicy.gatewayIngressPeers` for the actual
ingress-controller pods/namespaces. Empty peers deny ingress; do not guess cluster labels.
The GHCR images for `vocabs-skosmos`, `vocabs-fuseki`, `vocabs-jena-tools`
and `vocabs-dumps` must be publicly readable or pulled with an existing
Kubernetes Secret referenced by `imagePullSecrets`. Keep registry credentials
out of Git.
See [gateway prerequisites](gateway.md), [Skosmos configuration](../config/skosmos/README.md),
[storage](storage.md), and [candidate imports](imports.md). Install does not load
RDF automatically. Keep the active/candidate workflow and revision safeguards.

After reviewing values, a CLI equivalent is:

```bash
helm upgrade --install vocabs-platform-dev acdh-vocabs/vocabs \
  --version 0.2.0-dev.22 --namespace vocabs-platform-dev \
  -f environments/vocabs-platform-dev.yaml
```

The command targets the existing `vocabs-platform-dev` release. The pilot
values above illustrate the required settings; the tracked
`environments/vocabs-platform-dev.yaml` contains the current dev configuration.
Publishing does not certify the runtime stack or replace the Kubernetes pilot
acceptance tests in the existing runbooks.
