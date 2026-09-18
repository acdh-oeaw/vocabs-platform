# Skosmos 3 ACDH branding

The ACDH theme is owned by this repository and is baked into the immutable
`vocabs-skosmos` image. The old `acdh-oeaw/vocabs-update-theme` repository is a
migration and reference source only; it is not a runtime dependency.

## Where files live

- `branding/css/acdh-vocabs.css` contains the ACDH CSS variables and the small
  amount of CSS needed for the v3.3 DOM.
- `branding/custom-templates/` contains Skosmos 3 content-slot templates.
- `branding/images/` contains ACDH-owned logo, favicon and About-page images.
- `branding/assets/fonts/` contains the selected Fira Sans webfonts.
- `images/skosmos/Dockerfile` copies the extension assets into the upstream
  v3.3 webroot. No runtime clone, download, postStart copy or writable shared
  webroot is used.

The default configuration enables the stylesheet with `skosmos:customCss`. No
plugin is currently enabled: the migrated behavior is static content and
styling, so a JavaScript plugin would add risk without a functional benefit.

## Migration matrix

| Legacy component | Legacy file | Purpose | Skosmos 2 mechanism | Skosmos 3.3 equivalent | Migration strategy | Requires plugin? | Risk/compatibility note |
|---|---|---|---|---|---|---|---|
| Global palette and typography | `resource/css/styles.css`, `resource/css/stylesheet.css`, `resource/css/fira.css` | ACDH colors, Fira Sans, page styling | Full stylesheet replacement | `skosmos:customCss`, CSS variables | Reimplemented only against v3.3 variables and DOM | No | Old Bootstrap selectors were not copied; visual review is still required |
| Legacy Fundament theme | `resource/fundament/fundament-vocabs.css`, `resource/fundament/fundament.min.css`, `resource/fundament/fundament.min.js` | Legacy site shell and Bootstrap-era theme | Bundled Fundament assets | v3.3 Bootstrap 5 theme and custom CSS | Not copied; only the relevant colors and typography were re-expressed | No | Fundament JavaScript would conflict with the v3 frontend |
| Logo | `resource/pics/vocabs-logo.svg`, `view/fundament_header.twig` | Header branding | Full header Twig override | `custom-templates/headerbar-top` | Add a small accessible logo fragment | No | Upstream header/navigation remains intact |
| Favicon | `favicon.ico`, `view/meta.twig` | Browser tab icon | Meta/template override | `custom-templates/html-head` | Add an ACDH favicon link without replacing upstream files | No | Verify path behind a non-root `baseHref` if deployed that way |
| Landing visual | `resource/pics/vocabs_intro_bg.jpg`, `view/fundament_header_hero.twig` | Intro background and service message | Full hero/header override | `landing-end` slot plus CSS | Preserve the image and concise intro within the v3.3 landing layout | No | Exact old hero geometry is intentionally not reproduced |
| Landing text | `view/vocabularylist.twig`, `view/fundament_about.inc` | Service introduction | Full page/template override | `landing-end` slot | Add a short link to the v3.3 About page | No | Vocabulary list remains upstream and accessible |
| About content | `view/about.twig`, `view/fundament_about.inc` | Services, editor, API information | Full About Twig override | `about` slot | Reuse reviewed text and selected images in a v3.3 section | No | Links and copy should be reviewed with service owners |
| Footer | `view/footer.inc.dist`, `view/fundament_footer.twig` | ACDH contact/helpdesk | Footer include/full Twig override | `footer` slot | Add semantic responsive footer content | No | Upstream footer wrapper and accessibility remain |
| Vocabulary/concept/search styling | `view/vocab*.twig`, `view/concept*.twig`, `view/search-result.twig`, `resource/css/styles.css` | Colors, links, tables and headings | Core Twig/CSS fork | v3.3 CSS variables | Theme shared v3.3 surfaces through variables | No | v3.3 layout and controls are intentionally preserved |
| Vocabulary/editor/visualize screenshots | `resource/pics/vocabseditor_01.png`, `resource/pics/vocabs-viz-02.png` | About-page illustrations | Static webroot assets | Dedicated image directory | Copy only the two assets referenced by the migrated About content | No | These are content assets, not application widgets |
| Legacy UI JavaScript | `resource/js/config.js`, `docready.js`, `groups.js`, `hierarchy.js`, `scripts.js` | Autocomplete, hierarchy, sidebar and AJAX behavior | Replaced core JavaScript | Upstream Vue 3/Bootstrap 5 frontend | Do not migrate; retain upstream behavior | No | Legacy selectors and jQuery APIs are incompatible with v3.3 |
| Matomo analytics | `plugins/matomo-common/*`, `plugins/matomo-vocabs/*`, `view/footer.inc.dist` | Site tracking | Skosmos 2 plugin and footer script | v3 plugin format plus `skosmos:globalPlugins` | Not enabled pending current site ID, consent and privacy decision | Yes, if approved later | Do not ship tracking by accident; document site-specific configuration first |
| Legacy translations | `resource/translations/*.po`, `*.mo` | Fork-specific wording | Replaced translation catalogues | Upstream v3.3 translations/custom content | Not copied; only new static English content is used | No | Revisit with v3-compatible message IDs if translations are required |
| Legacy Twig pages | `view/light.twig`, `view/topbar.twig`, `view/headerbar.twig`, `view/vocab.twig`, `view/concept*.twig`, `view/search-result.twig`, `view/about.twig` | Entire Skosmos 2 layout | Full template override | v3.3 templates and slots | Intentionally not migrated wholesale | No | Prevents an ACDH Skosmos fork and preserves API/frontend behavior |

## v3.3 mechanisms verified

Skosmos v3.3 includes `.twig` files under `custom-templates/<slot>/` in
alphabetical order. The available slots used here are `html-head`,
`headerbar-top`, `landing-end`, `about` and `footer`; v3.3 also provides
`headerbar-bottom`, `landing-start`, `landing-top`, `landing-bottom`,
`main-content-top`, `main-content-bottom` and `topbar`.

`skosmos:customCss` accepts a stylesheet path relative to the Skosmos webroot.
`skosmos:globalPlugins` accepts plugin names, with each plugin described by a
`plugins/<name>/plugin.json` file containing `js`, `css` and/or `templates`
arrays. The migration currently needs no plugin.

## Updating and testing branding

1. Inspect the corresponding v3.3 template and slot before adding markup.
2. Keep styling in `branding/css/acdh-vocabs.css` and prefer existing variables.
3. Add only ACDH-owned binary assets under `branding/images/` or
   `branding/assets/`.
4. Run `python3 tests/test_theme.py`, `python3 tests/helm/test_render.py` and
   `git diff --check`.
5. Build locally with `scripts/build-images.py` using the existing profile and
   a pinned Java base image. Do not push from the build script.
6. Deploy the resulting image in an isolated namespace and inspect the browser
   console and all responsive states before changing the image revision.

Manual acceptance must cover landing page, header, footer, logo, favicon,
About, vocabulary, concept and search results at mobile, tablet and desktop
widths, plus language selection, keyboard navigation and focus visibility.
Visual parity has not been claimed until those browser checks are performed.

Intentional differences from Skosmos 2 are the Bootstrap 5/Vue 3 DOM, the
upstream responsive navigation and controls, the upstream accessibility/focus
behavior, and the absence of legacy jQuery hierarchy/sidebar scripts.

## Image revision

The current development profile remains on upstream Skosmos `v3.3`. The shared
ACDH revision remains `r1` for Fuseki and Jena tools, while the profile's
Skosmos-specific revision is `r2` for the theme image:
`ghcr.io/acdh-oeaw/vocabs-skosmos:3.3-r2`. This avoids an unrelated rebuild/tag
bump for the data/runtime images.

The following legacy files are intentionally not runtime dependencies: all
Skosmos-2 core PHP/model/controller files, all full-page files under `view/`
other than the content inspected for migration, `resource/js/*`, the remaining
relationship icons and screenshots under `resource/pics/`, the unused font
formats, the `.po`/`.mo` translation catalogues, and both Matomo plugin
directories. The legacy repository remains the audit/reference source.