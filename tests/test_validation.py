import unittest

import _support
_support.add_program_to_path()

import validation
from validation import ValidationError


class TestValidation(unittest.TestCase):
    def test_valid_site_passes(self):
        warnings = validation.validate_site(
            "my-site",
            {"title": "T", "description": "D", "theme": "dark"},
            {"index": {"hero": "H"}},
        )
        self.assertEqual(warnings, [])

    def test_missing_index_page_is_error(self):
        with self.assertRaises(ValidationError) as ctx:
            validation.validate_site("my-site", {}, {"home": {"hero": "H"}})
        self.assertIn("index", str(ctx.exception))

    def test_invalid_theme_is_error(self):
        with self.assertRaises(ValidationError) as ctx:
            validation.validate_site(
                "my-site", {"theme": "blue"}, {"index": {"hero": "H"}}
            )
        self.assertIn("blue", str(ctx.exception))

    def test_empty_site_name_is_error(self):
        with self.assertRaises(ValidationError):
            validation.validate_site("   ", {}, {"index": {}})

    def test_missing_title_is_only_a_warning(self):
        warnings = validation.validate_site(
            "my-site", {"description": "D"}, {"index": {"hero": "H"}}
        )
        self.assertTrue(any("title" in w for w in warnings))

    def test_repo_name_normalization(self):
        self.assertEqual(
            validation.normalize_repo_name("My Cool Site!"), "my-cool-site"
        )
        self.assertEqual(
            validation.normalize_repo_name("a_b c"), "a-b-c"
        )

    def test_repo_name_validity(self):
        self.assertTrue(validation.is_valid_repo_name("javier-lab3"))
        self.assertFalse(validation.is_valid_repo_name(""))
        self.assertFalse(validation.is_valid_repo_name(".."))


if __name__ == "__main__":
    unittest.main()
