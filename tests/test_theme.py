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
        self.assertEqual(len(templates), 7)
        for template in templates:
            self.assertNotIn('{% extends "light.twig" %}', template.read_text())
        self.assertEqual(
            {path.parent.name for path in templates},
            {"html-head", "headerbar-top", "landing-end", "about", "footer", "topbar"},
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
            self.assertIn(prop, {"padding-block", "padding", "margin-bottom", "font-size"})

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