"""Entry point of the SiteLang compiler.

Pipeline: parse arguments -> read a ``.sl`` file -> lex & parse it with ANTLR
-> stop on any lexical/syntactic error -> walk the tree with the listener ->
validate -> generate HTML -> deploy to GitHub + Vercel.

Usage:
    python3 Driver.py site.sl              # full compile + deploy (needs tokens)
    python3 Driver.py site.sl --dry-run    # parse + validate + generate HTML only
"""

import argparse
import os
import sys

from antlr4 import CommonTokenStream, FileStream, ParseTreeWalker
from antlr4.error.ErrorListener import ErrorListener


class _CollectingErrorListener(ErrorListener):
    """Collects lexer/parser errors instead of only printing them, so the
    driver can refuse to deploy when the input is syntactically invalid."""

    def __init__(self):
        super().__init__()
        self.errors = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.errors.append(f"line {line}:{column} {msg}")


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="Driver.py",
        description="Compile a SiteLang (.sl) file into a deployed website.",
    )
    parser.add_argument("input", help="path to the SiteLang source file (.sl)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="parse, validate and generate index.html locally without "
             "calling GitHub or Vercel (no tokens required)",
    )
    parser.add_argument(
        "--output",
        default="index.html",
        help="where to write the HTML in --dry-run mode (default: index.html)",
    )
    return parser.parse_args(argv)


def read_tokens(environ):
    """Return (github_token, vercel_token) from the environment."""
    return environ.get("GITHUB_TOKEN", ""), environ.get("VERCEL_TOKEN", "")


def main(argv):
    args = parse_args(argv)

    if not os.path.isfile(args.input):
        print(f"Error: input file not found: {args.input}", file=sys.stderr)
        return 2

    github_token, vercel_token = read_tokens(os.environ)
    if not args.dry_run and (not github_token or not vercel_token):
        print(
            "Error: GITHUB_TOKEN and VERCEL_TOKEN must be set (see program/.env).\n"
            "       Use --dry-run to compile and generate HTML without deploying.",
            file=sys.stderr,
        )
        return 1

    # Import the ANTLR-generated modules lazily so the rest of the driver can be
    # unit-tested before the parser has been generated.
    from SiteLangLexer import SiteLangLexer
    from SiteLangParser import SiteLangParser
    from SiteListener import SiteDeployListener
    from validation import ValidationError
    from deploy_api import DeploymentError

    error_listener = _CollectingErrorListener()

    input_stream = FileStream(args.input, encoding="utf-8")
    lexer = SiteLangLexer(input_stream)
    lexer.removeErrorListeners()
    lexer.addErrorListener(error_listener)

    stream = CommonTokenStream(lexer)
    parser = SiteLangParser(stream)
    parser.removeErrorListeners()
    parser.addErrorListener(error_listener)

    tree = parser.site()

    # Refuse to do anything external if the source is not syntactically valid.
    if error_listener.errors:
        print("Error: the SiteLang file has syntax errors:", file=sys.stderr)
        for err in error_listener.errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    listener = SiteDeployListener(github_token, vercel_token)
    ParseTreeWalker().walk(listener, tree)

    try:
        listener.deploy(dry_run=args.dry_run, output_path=args.output)
    except ValidationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except DeploymentError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
