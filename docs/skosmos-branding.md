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
styling, with a small navigation repair script in the `html-head` slot. No
plugin registration or full-page override is needed.

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
`headerbar-top`, `landing-end`, `about`, `footer` and `topbar`; v3.3 also provides
`headerbar-bottom`, `landing-start`, `landing-top`, `landing-bottom`,
`main-content-top` and `main-content-bottom`.

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
Skosmos-specific deployed revision is `r3`:
`ghcr.io/acdh-oeaw/vocabs-skosmos:3.3-r3`. The theme cleanup requires a new
immutable `3.3-r4` image and a subsequent chart release `0.2.0-dev.8`; neither
version is changed or published by this cleanup. This avoids an unrelated rebuild/tag
bump for the data/runtime images.

The following legacy files are intentionally not runtime dependencies: all
Skosmos-2 core PHP/model/controller files, all full-page files under `view/`
other than the content inspected for migration, `resource/js/*`, the remaining
relationship icons and screenshots under `resource/pics/`, the unused font
formats, the `.po`/`.mo` translation catalogues, and both Matomo plugin
directories. The legacy repository remains the audit/reference source.

## Landing cleanup and navigation audit (Skosmos 3.3)

Inspected upstream [base template](https://github.com/NatLibFi/Skosmos/blob/v3.3/src/view/base-template.twig),
[landing template](https://github.com/NatLibFi/Skosmos/blob/v3.3/src/view/landing.twig),
[styles](https://github.com/NatLibFi/Skosmos/blob/v3.3/resource/css/skosmos.css)
and navigation scripts. Bootstrap `py-4` plus the custom logo's bottom margin
made the header unnecessarily tall. The 7/5-column split, background on the
entire stretched right column, minimum height and grey vocabulary list made
empty deployments look unbalanced. The dark logo also lacked contrast against
the dark footer.

CSS now gives the landing page a bounded, equal-column desktop layout, stacked
mobile content, a compact header and a content-sized intro background. The
existing translated empty-state heading remains visible with neutral styling;
no vocabulary data or translations are substituted. The footer logo has a white
backing and its headings, underlines and focus rings contrast with the dark
background. The upstream visually-hidden landing h1 remains accessible: only
its decorative Skosmos background and dimensions are removed. The inner-page
background logo uses the ACDH asset too, preserving its upstream accessible name.

The base template's skip link points at missing `#maincontent` and is always
`visually-hidden`. Its actual main wrapper is `#main-container-row`, already
inside `<main>` and focusable with `tabindex="-1"`. The small `html-head` slot
script points the existing link at this wrapper on the *current page* (important
because of `<base>`), switches to Bootstrap's focus-visible skip-link class,
and focuses/scrolls the wrapper only on activation. It never steals initial
focus. No upstream source file, page template, translation or outline rule is
replaced. Without JavaScript, the upstream skip-link defect remains; Skosmos
itself declares JavaScript required. Reassess this repair on upstream upgrades.

The blue container outline is consistent with upstream `:focus-visible`, not
a decorative border. Static source inspection cannot establish what focused
the wrapper in a particular browser session. After activating Skip to main,
a wrapper focus outline is intentional and must remain. In dev, inspect
`document.activeElement` when reproducing an unexpected outline before assuming
it is a layout problem.

Tests cover packaged extension paths/assets, absence of full-page forks,
retained heading container, no outline suppression, current-page skip targets,
no initial focus, activation and missing-element handling. Theme tests are now
included in `make test` and `make validate`. These checks do not substitute for
browser layout or screen-reader acceptance.

Before promoting r4, visually check 320px mobile, tablet and wide desktop,
200% zoom, empty and populated vocabulary lists, About/concept/search pages,
logo proportions, footer wrapping and no horizontal overflow. Tab from the
address bar: Skip to main must appear, Enter must focus main without navigating
to a different page, and subsequent Tab must reach content links. Verify the
hidden h1 with a screen reader and visible focus on navigation/footer links.

### Header variants and logo regression audit

A full search of the Skosmos v3.3 source for `skosmos-logo`, `skosmos-logo-top`,
`skosmos-RGB.svg` and `skosmos-NEGA-RGB.svg` found only the two containers in
`src/view/base-template.twig` and their rules in `resource/css/skosmos.css`.
All major page templates extend that base; none introduces a third logo.

| Page/template | Upstream header identity | ACDH identity |
|---|---|---|
| `/en/` (`landing.twig`) | `#skosmos-logo`, RGB background, hidden h1 | `headerbar-top` image; upstream background removed and dimensions reset |
| `/en/about` (`about.twig`) | `#skosmos-logo-top`, NEGA background, hidden service-name h2 | ACDH background on the existing home link |
| `/en/feedback` (`feedback.twig`) | Same topbar link; no headerbar | Same ACDH background |
| Vocabulary home (`vocab-home.twig`) | Topbar link plus vocabulary title/search headerbar | Topbar ACDH background only; no extra headerbar logo |
| Concept (`concept.twig`) | Same vocabulary header variant | Topbar ACDH background only |
| Vocabulary search (`vocab-search.twig`) | Same vocabulary header variant | Topbar ACDH background only |
| Global search (`global-search.twig`) | Search toggle, no logo and no headerbar | Small `topbar` slot image, guarded by the base template's no-logo condition |

The headerbar fragment now renders only on landing. The extra topbar fragment
renders only when neither existing logo variant is present. Both preserve the
existing vocabulary title/search controls. The topbar background replacement
keeps its hidden service-name heading and home link, but replaces the upstream
168×60 fixed dimensions with responsive width and the ACDH asset's aspect ratio.
There is no empty fixed-height logo block and no hidden heading container.
The footer identity is intentional and separate from header duplication.

This matrix is based on upstream template branches and CSS inspection, not a
live deployment render. In addition to landing, visual acceptance must explicitly
visit **`/en/about` and `/en/feedback`**, then a configured vocabulary, concept,
vocabulary search and global search. Each header should show exactly one ACDH
identity and no Skosmos logo at mobile/desktop sizes. Check home-link keyboard
focus, accessible service names, navigation wrapping and title/search usability.
