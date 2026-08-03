import unittest

import _support
_support.add_program_to_path()

import html_generator


class TestHtmlGenerator(unittest.TestCase):
    def _html(self, **overrides):
        site_attrs = {"title": "My Title", "description": "My Desc", "theme": "dark"}
        pages = {"index": {"hero": "Hero", "about": "About", "contact": "a@b.com"}}
        site_attrs.update(overrides.get("site_attrs", {}))
        pages = overrides.get("pages", pages)
        return html_generator.generate_html(
            overrides.get("site_name", "my-site"), site_attrs, pages
        )

    def test_has_required_document_structure(self):
        html = self._html()
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn('<html lang="en">', html)
        self.assertIn('<meta charset="UTF-8"', html)
        self.assertIn('name="viewport"', html)
        self.assertIn("<title>My Title</title>", html)
        self.assertIn('name="description" content="My Desc"', html)

    def test_escapes_user_content(self):
        html = self._html(
            pages={"index": {"hero": '<script>alert("x")</script>', "about": "a & b"}}
        )
        self.assertNotIn("<script>alert", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("a &amp; b", html)

    def test_dark_and_light_themes_differ(self):
        dark = self._html(site_attrs={"theme": "dark"})
        light = self._html(site_attrs={"theme": "light"})
        self.assertIn("#0f172a", dark)   # dark background
        self.assertNotIn("#0f172a", light)

    def test_contact_becomes_mailto(self):
        html = self._html()
        self.assertIn('href="mailto:a@b.com"', html)

    def test_extra_pages_are_rendered(self):
        html = self._html(
            pages={"index": {"hero": "H"}, "blog": {"post": "Hello blog"}}
        )
        self.assertIn("Hello blog", html)


if __name__ == "__main__":
    unittest.main()
