# Production navigation parity

Sources: [`view/fundament_topbar.twig`](https://github.com/acdh-oeaw/vocabs-update-theme/blob/46e0fa7e0ea79eba7188298a716d22e09f55cc01/view/fundament_topbar.twig)
and [`view/fundament_about.inc`](https://github.com/acdh-oeaw/vocabs-update-theme/blob/46e0fa7e0ea79eba7188298a716d22e09f55cc01/view/fundament_about.inc).

| Production entry | Actual legacy destination/behavior | New behavior |
|---|---|---|
| Vocabularies | `{{ request.lang }}/` with content-language query parameters | Unmodified native Skosmos home routing |
| About | `{{ request.lang }}/about` with language query parameters | Unmodified native About route |
| Editor | About `#editor` (optionally prefixed by vocabulary); section links to `https://vocabseditor.acdh.oeaw.ac.at/` | Primary navbar keeps the native language-aware About `#editor` anchor; the About service link is runtime-configurable |
| API | About `#api` (optionally prefixed by vocabulary); section links to `https://vocabs-api.acdh.oeaw.ac.at/` | Primary navbar keeps the native language-aware About `#api` anchor; the About service link points to the environment-specific Swagger UI when configured |
| Help | **No URL**: focusable tooltip with translated `helper_help` and `search_example_text` | Keyboard-operable native details/summary with those same translated messages |
| Interface language | Native current-language name, alternate `request.langurl(langcode)` links | Translated label and current `lang_name`; original upstream alternate links remain |
| Feedback | Commented out in the primary legacy navbar | Primary navbar entry hidden; native route/backend unchanged |

Legacy links use the same tab; no new-window behavior is introduced. Legacy
labels use translation messages; Editor/API remain invariant service names here,
while Help and Interface language use the existing Skosmos translations. Legacy
Editor/API reused `id="navi3"`; that duplicate-ID defect is not migrated. Native
Vocabularies/About IDs are untouched; new entries have unique `acdh-nav-*` IDs.

## Runtime configuration

```yaml
skosmos:
  navigation:
    editorUrl: https://vocabseditor.acdh.oeaw.ac.at/
    apiUrl: ""
```

The Editor default is the verified shared public service and is configured in
Helm, never embedded in the image. Set it to a public environment-specific Editor
URL if available. Empty keeps the native language-aware About#editor link and
omits the About page's external Editor link.

For API, explicit `skosmos.navigation.apiUrl` takes precedence. If empty, and
both `swagger.enabled` and `swagger.ingress.enabled` are true, the chart derives
`http(s)://<swagger.ingress.host>/`, using HTTPS when Swagger ingress TLS is
enabled. This is the Swagger **UI**, not `swagger.specUrl` (the JSON specification),
not Fuseki, and not a guessed hostname based on the main site. With no public
Swagger ingress or override, API links are omitted. For deployments where TLS is
terminated elsewhere, set the explicit public HTTPS docs URL.

For example, with the existing dedicated development Swagger ingress configured:

```yaml
swagger:
  enabled: true
  specUrl: https://vocabs.example.org/swagger.json
  ingress:
    enabled: true
    allowAnubisBypass: true
    host: api-dev.example.org
    tls:
      enabled: true
      secretName: api-tls
```

navigation resolves to `https://api-dev.example.org/`. Use actual installation
values rather than these illustrative domains. No additional ingress is created
by navigation. Help deliberately has no URL setting because production Help is
local usage guidance, not an external helpdesk destination; footer helpdesk links
are unchanged.

A separate public ConfigMap supplies `resource/acdh-navigation.json`, mounted
read-only into Skosmos's existing resource directory. It works with either the
chart-managed or an externally supplied `config.ttl`; no Turtle migration is
required. A checksum rolls Skosmos when these values change. The tiny html-head
script updates existing link elements with a no-store same-origin fetch, without
moving focus or creating language URLs. Missing configuration/network failures
retain the native Editor fallback and omit API. About's service links use the
same configuration so the image no longer embeds those production hosts.

URLs must be absolute HTTP(S) public DNS names, without userinfo. The chart
rejects IP literals, unqualified/internal service names and common private DNS
suffixes. This deterministic syntax check does not resolve DNS: operators must
still supply only publicly accessible user-facing services, never private hosts,
credentials, Fuseki administration or query endpoints.

## Accessibility and QA

The existing `topbar` slot adds only small fragments. CSS hides the Feedback
list item, not its route. The native `navi1`/`navi2` links, alternate-language
links, their IDs and upstream cookie/routing handlers remain intact. The current
language name uses `request.lang | lang_name(request.lang)` with `lang` metadata;
there is no second locale system or hard-coded English label. The Help summary
works with keyboard/assistive technology, and its content stays in normal flow
on mobile. Existing skip repair, focus rings, logo guards, palette, hero, landing
search relocation and footer layout remain intact.

After deployment check EN/DE current/alternate labels and language persistence,
Editor and API destinations (including configured dev Swagger), Help keyboard
activation, direct `/en/feedback`, all header variants, no duplicate identities,
mobile wrapping and 200% zoom. No Rancher deployment is part of publication.
