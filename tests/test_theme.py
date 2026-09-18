#!/usr/bin/env python3
"""Cluster-free contracts for the immutable Skosmos branding layer."""
import re
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
        self.assertEqual(len(templates), 5)
        for template in templates:
            self.assertNotIn('{% extends "light.twig" %}', template.read_text())
        self.assertEqual(
            {path.parent.name for path in templates},
            {"html-head", "headerbar-top", "landing-end", "about", "footer"},
        )

    def test_css_references_packaged_assets(self):
        css = (BRANDING / "css/acdh-vocabs.css").read_text()
        self.assertIn("../../fonts/acdh/FiraSans-Regular.woff", css)
        self.assertIn("../../pics/acdh/vocabs-intro-bg.jpg", css)
        self.assertNotIn("!important", css)


if __name__ == "__main__":
    unittest.main()