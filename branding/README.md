# Thin ACDH branding

Migrate only ACDH-owned changes from the old theme/plugin repositories after an
inventory and license review. Put Twig overrides in `custom-templates`, plugins
in `plugins`, CSS in `css`, and image assets in `images`. The Dockerfile overlays
these onto the verified upstream web root without vendoring Skosmos core.

Paths are verified from upstream v3.3's Dockerfile: `/var/www/html/custom-templates`
and `/var/www/html/plugins`; assets go into dedicated ACDH subdirectories under
`resource/css` and `resource/pics`. Reference `resource/css/acdh/...` using
`skosmos:customCss` and the corresponding image URLs from templates. These are
extension locations, not automatic plugin registration. Enable migrated plugins
in validated configuration. Test template/API compatibility and plugin state
before using multiple replicas. Placeholder .gitkeep files are not branding.
See `docs/skosmos-branding.md` for the migration matrix and browser acceptance
checklist.
