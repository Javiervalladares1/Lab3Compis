import os
import tempfile
import unittest
from unittest import mock

import _support
_support.add_program_to_path()

import Driver


class TestDriverUnit(unittest.TestCase):
    """Driver checks that do not need the generated parser."""

    def test_missing_input_file_returns_2(self):
        rc = Driver.main(["does-not-exist.sl"])
        self.assertEqual(rc, 2)

    def test_missing_tokens_returns_1(self):
        with tempfile.NamedTemporaryFile("w", suffix=".sl", delete=False) as fh:
            fh.write('site "x" { page "index" { hero = "h" } }')
            path = fh.name
        try:
            with mock.patch.dict(os.environ, {}, clear=True):
                rc = Driver.main([path])  # not dry-run, no tokens
            self.assertEqual(rc, 1)
        finally:
            os.unlink(path)

    def test_read_tokens(self):
        gh, vc = Driver.read_tokens({"GITHUB_TOKEN": "a", "VERCEL_TOKEN": "b"})
        self.assertEqual((gh, vc), ("a", "b"))

    def test_parse_args_dry_run_flag(self):
        args = Driver.parse_args(["site.sl", "--dry-run"])
        self.assertTrue(args.dry_run)
        self.assertEqual(args.input, "site.sl")


@unittest.skipUnless(_support.ensure_parser(),
                     "ANTLR parser not generated (set ANTLR_JAR or run `antlr`)")
class TestDriverIntegration(unittest.TestCase):
    """End-to-end pipeline in --dry-run mode (no network)."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self.out = os.path.join(self._tmp, "index.html")

    def _run(self, fixture):
        return Driver.main([_support.fixture(fixture), "--dry-run",
                            "--output", self.out])

    def test_valid_file_compiles_and_generates_html(self):
        rc = self._run("valid.sl")
        self.assertEqual(rc, 0)
        self.assertTrue(os.path.isfile(self.out))
        with open(self.out, encoding="utf-8") as fh:
            html = fh.read()
        self.assertIn("<!DOCTYPE html>", html)
        # user content with special chars must be escaped
        self.assertIn("&lt;world&gt;", html)

    def test_syntax_error_blocks_pipeline(self):
        rc = self._run("syntax_error.sl")
        self.assertEqual(rc, 1)
        self.assertFalse(os.path.isfile(self.out))  # nothing generated

    def test_missing_index_page_fails_validation(self):
        rc = self._run("no_index.sl")
        self.assertEqual(rc, 1)

    def test_invalid_theme_fails_validation(self):
        rc = self._run("bad_theme.sl")
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
