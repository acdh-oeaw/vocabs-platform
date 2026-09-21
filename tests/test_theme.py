#!/usr/bin/env python3
"""Cluster-free contracts for the immutable Skosmos branding layer."""
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BRANDING = ROOT / "branding"


class SkosmosTheme(unittest.TestCase):
    def test_image_build_contains_only_extension_paths(self):
        dockerfile = (ROOT / "images/skosmos/Dockerfile").read_text()
        self.assertIn("COPY branding/custom-templates/ /var/www/html/custom-templates/", dockerfile)
        self.assertIn("COPY branding/css/ /var/www/html/resource/css/acdh/", dockerfile)
        self.assertIn("COPY branding/images/ /var/www/html/resource/pics/acdh/", dockerfile)
        self.assertIn("COPY branding/assets/fonts/ /var/www/html/resource/fonts/acdh/", dockerfile)
        self.assertNotRegex(dockerfile, r"COPY branding/(?:view|resource)/")

    def test_expected_assets_and_config_exist(self):
        for relative in [
            "css/acdh-vocabs.css",
            "images/vocabs-logo.svg",
            "images/favicon.ico",
            "images/vocabs-intro-bg.jpg",
            "images/vocabs-editor.png",
            "images/vocabs-visualize.png",
            "assets/fonts/FiraSans-Regular.woff",
        ]:
            path = BRANDING / relative
            self.assertTrue(path.is_file(), relative)
            self.assertGreater(path.stat().st_size, 0, relative)
        ttl = (ROOT / "chart/vocabs/files/skosmos.ttl").read_text()
        self.assertIn('skosmos:customCss "resource/css/acdh/acdh-vocabs.css"', ttl)

    def test_templates_use_v3_slots_and_no_skosmos2_pages(self):
        templates = sorted((BRANDING / "custom-templates").rglob("*.twig"))
        self.assertEqual(len(templates), 10)
        for template in templates:
            self.assertNotIn('{% extends "light.twig" %}', template.read_text())
        self.assertEqual(
            {path.parent.name for path in templates},
            {"html-head", "headerbar-top", "landing-end", "about", "footer", "topbar", "landing-top"},
        )

    def test_css_references_packaged_assets(self):
        css = (BRANDING / "css/acdh-vocabs.css").read_text()
        self.assertIn("../../fonts/acdh/FiraSans-Regular.woff", css)
        self.assertIn("../../pics/acdh/vocabs-intro-bg.jpg", css)
        self.assertNotRegex(css, r"outline(?:-width|-style)?\s*:\s*(?:none|0(?:px)?|hidden)\b")
        logo = re.search(r"#skosmos-logo\s*\{([^}]+)\}", css).group(1)
        self.assertIn("background-image: none", logo)
        self.assertNotRegex(logo, r"display:\s*none|visibility:\s*hidden")
        # Only Bootstrap spacing/type utilities need priority overrides.
        for prop in re.findall(r"([\w-]+)\s*:[^;{}]+!important", css):
            self.assertIn(prop, {"padding-block", "padding", "margin-bottom", "margin-inline-start", "margin-top", "padding-inline", "font-size", "display"})

    def test_both_upstream_logo_variants_are_rebranded(self):
        css = (BRANDING / "css/acdh-vocabs.css").read_text()
        self.assertNotRegex(css, r"skosmos-(?:NEGA-)?RGB\.svg")
        for selector in ("skosmos-logo", "skosmos-logo-top"):
            rule = re.search(r"#" + selector + r"\s*\{([^}]+)\}", css).group(1)
            self.assertIn("height: auto", rule)
            self.assertNotRegex(rule, r"display:\s*none|visibility:\s*hidden")
            if selector.endswith("-top"):
                self.assertIn('background-image: url("../../pics/acdh/vocabs-logo.svg")', rule)
                self.assertIn("aspect-ratio:", rule)
                self.assertIn("width: clamp(", rule)
            else:
                self.assertIn("background-image: none", rule)
        for selectors, declarations in re.findall(r"([^{}]+)\{([^{}]+)\}", css):
            if re.search(r"\bh[1-6]\b|visually-hidden", selectors):
                self.assertNotRegex(declarations, r"display:\s*none|visibility:\s*hidden")

    def test_header_slots_do_not_duplicate_internal_page_identity(self):
        header = (BRANDING / "custom-templates/headerbar-top/10-acdh-logo.twig").read_text()
        self.assertIn("{% if pageType == 'landing' %}", header)
        topbar = (BRANDING / "custom-templates/topbar/10-acdh-logo.twig").read_text()
        self.assertIn("pageType != 'landing'", topbar)
        self.assertIn("request.vocabid == ''", topbar)
        self.assertIn("request.page != 'about'", topbar)
        self.assertIn("request.page != 'feedback'", topbar)
        self.assertIn('<li class="nav-item acdh-topbar-identity">', topbar)
        self.assertIn('alt="ACDH Vocabs"', topbar)

    def test_palette_semantics_and_contrast(self):
        css = (BRANDING / "css/acdh-vocabs.css").read_text()
        root = css.split(":root {", 1)[1].split("}", 1)[0]
        tokens = dict(re.findall(r"(--[\w-]+):\s*([^;]+);", root))

        def resolve(name):
            value = tokens[name]
            if value.startswith("var("):
                return resolve(value[4:-1])
            return value

        def rgb(value):
            return tuple(int(value[i:i+2], 16) for i in (1, 3, 5))

        def luminance(channels):
            channels = [c / 255 for c in channels]
            linear = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in channels]
            return sum(c * w for c, w in zip(linear, (.2126, .7152, .0722)))

        def contrast(foreground, background):
            a, b = sorted((luminance(foreground), luminance(background)))
            return (b + .05) / (a + .05)

        for text, bg in [
            ("--topbar-text-1", "--topbar-bg-1"),
            ("--topbar-text-2", "--topbar-bg-2"),
            ("--headerbar-text-2", "--headerbar-bg-2"),
            ("--footer-text", "--footer-bg"),
            ("--main-content-text", "--main-content-bg"),
            ("--main-content-link", "--main-content-bg"),
            ("--acdh-link", "--acdh-page-bg"),
            ("--search-button-text", "--search-button-bg"),
            ("--search-dropdown-selected-text", "--search-dropdown-selected-bg"),
        ]:
            self.assertGreaterEqual(contrast(rgb(resolve(text)), rgb(resolve(bg))), 4.5, (text, bg))
        self.assertEqual(resolve("--topbar-bg-1"), resolve("--acdh-surface"))
        self.assertEqual(resolve("--footer-bg"), resolve("--acdh-surface"))
        self.assertNotRegex(css.lower(), r"--acdh-pink|#ae0950|#ed0d6c")
        # White image pixels give the worst-case hero contrast under this overlay.
        r, g, b, alpha = map(float, re.findall(r"[\d.]+", resolve("--acdh-hero-overlay")))
        background = [alpha * c + (1 - alpha) * 255 for c in (r, g, b)]
        self.assertGreaterEqual(contrast(rgb(resolve("--acdh-on-hero")), background), 4.5)

    def test_hero_slots_and_shared_width(self):
        slots = BRANDING / "custom-templates"
        landing = (slots / "landing-top/10-acdh-hero.twig").read_text()
        about = (slots / "about/05-acdh-hero.twig").read_text()
        for hero in (landing, about):
            self.assertIn('class="acdh-hero"', hero)
            self.assertIn("Vocabs services", hero)
        old = (slots / "landing-end/10-acdh-intro.twig").read_text()
        self.assertNotIn("<", old)
        css = (BRANDING / "css/acdh-vocabs.css").read_text()
        self.assertIn("--acdh-content-width:", css)
        self.assertIn("max-width: var(--acdh-content-width)", css)
        self.assertIn("var(--acdh-hero-overlay)", css)
        self.assertIn("var(--acdh-on-hero)", css)

    def test_full_width_search_contract(self):
        slots = BRANDING / "custom-templates"
        hero = (slots / "landing-top/10-acdh-hero.twig").read_text()
        self.assertIn("In many areas of scholarly work, controlled vocabularies", hero)
        self.assertIn("publication of vocabularies and taxonomies of any kind.", hero)
        self.assertIn('id="acdh-landing-search"', hero)
        for template in slots.rglob("*.twig"):
            self.assertNotRegex(template.read_text(), r'id="global-search-(?:bar|wrapper)"')
        css = (BRANDING / "css/acdh-vocabs.css").read_text()
        self.assertNotRegex(css, r"(?:width|margin-inline):[^;]*100vw")
        self.assertNotRegex(css, r"overflow-x:\s*(?:hidden|clip)")
        subprocess.run(["node", str(ROOT / "tests/theme_landing_search.mjs")], check=True)

    def test_navigation_behavior(self):
        subprocess.run(["node", str(ROOT / "tests/theme_navigation.mjs")], check=True)

    def test_logo_accessibility_and_no_page_forks(self):
        header = (BRANDING / "custom-templates/headerbar-top/10-acdh-logo.twig").read_text()
        self.assertIn('alt="ACDH Vocabs"', header)
        for template in (BRANDING / "custom-templates").rglob("*.twig"):
            self.assertNotIn("{% extends", template.read_text())
            self.assertNotIn("<html", template.read_text())


if __name__ == "__main__":
    unittest.main()