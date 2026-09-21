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

## Production palette migration (after deployed r4)

Authoritative source: [vocabs-update-theme at 46e0fa7](https://github.com/acdh-oeaw/vocabs-update-theme/tree/46e0fa7e0ea79eba7188298a716d22e09f55cc01).
The production homepage was also inspected: it loads `styles.css`,
`stylesheet.css`, then `fundament.min.css` and `fundament-vocabs.css` in that order.
The final Fundament overrides, not the earlier Skosmos defaults or unused
framework classes, establish the white navigation/footer and turquoise strips.

| Legacy source/token or selector | Exact value | Skosmos 3 mapping |
|---|---|---|
| `fundament-vocabs.css`: main border, headerbar, search buttons; `fundament.min.css`: navbar border | `#88dbdf` | `--acdh-primary`: separator, vocabulary header/search backgrounds |
| `fundament-vocabs.css`: `.search-vocab-text` | `#5cc0c4` | `--acdh-accent`: secondary accents/underline and scrollbar token |
| `fundament-vocabs.css`: links / hover | `#00748f` / `#23527c` | `--acdh-link` / `--acdh-link-hover`: links, selected controls, focus |
| `fundament.min.css`: body / headings and final footer | `#444` / `#212529` | `--acdh-text` / `--acdh-heading`, `--acdh-footer-text` |
| `styles.css`: gray-850 | `#555555` | `--acdh-muted-text`: readable secondary text |
| `fundament.min.css`: final navbar/footer backgrounds | `#fff` | `--acdh-surface`, `--acdh-footer-bg`, both topbar variants |
| `fundament.min.css`: final body background | `#f1f1f1` | `--acdh-page-bg`: inner-page surfaces |
| `fundament.min.css`: footer separator | `rgba(0,0,0,.15)` | `--acdh-border`: restrained footer divider |
| `styles.css`: light-color | `#d4edeb` | `--acdh-divider`: content dividers |
| `fundament.min.css`: hero overlay | `rgba(108,117,125,.75)` | `--acdh-hero-overlay`: darker accessible derivative below |
| `fundament_header_hero.twig`, `.hero-dark`, `.lead` | white text over image | `--acdh-on-hero`: intro heading, copy, underlined link |

`view/light.twig` establishes the stylesheet cascade;
`view/fundament_header_hero.twig` selects `resource/pics/vocabs_intro_bg.jpg`;
`view/fundament_footer.twig` supplies the light footer classes. The packaged
`branding/images/vocabs-intro-bg.jpg` is byte-identical to the legacy image
(SHA-256 `8f2feed2a38d1dd0665ac9f48a8c5cd7a541703788653c26d4d5ed2cf52e5568`).
The earlier 95% white wash is replaced with the legacy grey-overlay/white-text
approach, confined to the existing intro card rather than a full-width hero.

The r4 navy surface `#394554`, generic cyan `#00acd3`, magenta borders/buttons
`#ed0d6c`, dark pink headings `#ae0950`, and pale cyan footer hover `#9cecff` are
removed from general theme styling. Magenta really exists in legacy `styles.css`
as `--alert-color-bright` (with pale `#d95f8a`); it is not a sitewide brand accent.
We do not recolor upstream semantic alerts or modify colors embedded in logos.
Obsolete Bootstrap/Foundation grid, control, fixed-height, global-font and
focus-suppression rules are not migrated. All new palette literals live in the
root semantic tokens; page/header branching and navigation repair are unchanged.

Accessibility deviations from exact legacy styling:

- White text on `#88dbdf`/`#5cc0c4` is too low-contrast for normal text. Search
  buttons and vocabulary header titles instead use legacy dark `#212529` on
  turquoise. Selected dropdowns use legacy `#00748f` with white text.
- The hero overlay uses `rgba(76,82,88,.9)`, a darker version of the source
  grey-blue overlay, to guarantee at least 4.5:1 white-text contrast even over
  white image pixels. The image remains visible but more subdued.
- Secondary text uses existing legacy `#555555` rather than `#74787a` for contrast
  on light grey surfaces. Focus outlines remain visible: dark on light surfaces,
  white within the hero. No legacy `outline: none` rules are copied.

Regression tests check semantic light-surface mappings and text contrast,
including the worst-case hero image background, rather than every cosmetic
value. Keep visual QA for `/en/`, `/en/about`, `/en/feedback`, vocabulary home,
concept, vocabulary search and global search: one ACDH header identity, no
upstream logo, turquoise search accents, readable white hero copy, light footer,
and keyboard focus. Responsive structure, Fira Sans, the empty-state wording,
and the compact two-column layout remain Skosmos 3 adaptations. No versions
are changed by this palette pass and nothing is published.

## Structural alignment after r5

The palette is unchanged. The legacy `fundament_header.twig` uses a bounded
navigation container and `fundament_header_hero.twig` places service copy over
the image. Their composition is adapted without importing Foundation markup.

- `topbar` retains its existing guarded global-search identity; inner-page
  `#skosmos-logo-top` and landing-only `headerbar-top` remain mutually exclusive.
  CSS gives navigation, landing header and footer a shared 72rem maximum, compact
  7–9rem header logos, restrained padding and wrapping. Internal navigation now
  follows the logo rather than being pushed to the far edge; languages retain
  right-side auto spacing. Landing retains a shallow separate identity row to
  preserve native DOM/tab order and its hidden h1.
- `landing-top` now contains the bounded Vocabs services hero. `landing-end`
  contains only a comment to suppress the upstream placeholder, and its empty
  column is hidden. The native vocabulary list occupies the width below the
  hero, including real empty states and populated categories.
- About uses `about/05-acdh-hero.twig`, before `10-acdh-services.twig`. Source
  inspection confirms About has neither `headerbar-bottom` nor a generic
  `main-content-top` slot. Therefore its native About h1 remains above the hero:
  placing the banner literally before that heading would require DOM movement
  or a page override. This small intentional difference preserves reading order.
  The concise hero summary avoids repeating the detailed service paragraph.
- Shared `.acdh-hero` styling uses the existing image and contrast-tested overlay
  and text tokens. Height follows content; no fixed hero height is introduced.
- Nested upstream About/Feedback container padding is reduced from 8rem. About
  has a 72rem outer region with readable paragraph lengths; Feedback is bounded
  to 48rem. Footer uses the same site grid with a smaller logo. Native search,
  heading semantics, skip repair and accessible names remain intact.

Active slots: `html-head`, `topbar`, `headerbar-top`, `landing-top`, `landing-end`
(intentional empty placeholder suppression), `about`, and `footer`.

Browser QA: check 320px, tablet, desktop, ultrawide and 200% zoom on landing,
About, Feedback, vocabulary, concept and both search variants. Confirm one
header identity, sensible wrapping/tab order, visible languages, unclipped focus,
Skip to main behavior, white hero copy, related-tools columns, intentional form
width and footer alignment. Check both empty and populated vocabulary listings
without inventing data. These remain deployment checks, not claimed browser
results. This structural pass targets Skosmos `3.3-r6` and chart
`0.2.0-dev.10`; shared Fuseki/Jena revisions and appVersion stay unchanged.
