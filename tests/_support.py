"""Shared helpers for the test suite.

Puts the compiler modules on sys.path and, when possible, makes sure the
ANTLR-generated parser is importable so the integration tests can run.
"""

import importlib
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROGRAM_DIR = os.path.abspath(os.path.join(HERE, "..", "program"))
FIXTURES_DIR = os.path.join(HERE, "fixtures")


def add_program_to_path():
    if PROGRAM_DIR not in sys.path:
        sys.path.insert(0, PROGRAM_DIR)


def parser_available():
    add_program_to_path()
    try:
        importlib.import_module("SiteLangLexer")
        importlib.import_module("SiteLangParser")
        importlib.import_module("SiteLangListener")
        return True
    except Exception:
        return False


def ensure_parser():
    """Return True if the ANTLR parser is importable, generating it if needed.

    Generation is only attempted when an ANTLR jar is reachable (env var
    ANTLR_JAR or the standard Docker path) and Java is installed. Otherwise the
    caller should skip parser-dependent tests.
    """
    if parser_available():
        return True

    jar = os.environ.get("ANTLR_JAR") or "/usr/local/lib/antlr-4.13.2-complete.jar"
    if not os.path.isfile(jar) or shutil.which("java") is None:
        return False

    subprocess.run(
        ["java", "-jar", jar, "-Dlanguage=Python3", "-listener", "SiteLang.g4"],
        cwd=PROGRAM_DIR,
        check=True,
    )
    importlib.invalidate_caches()
    return parser_available()


def fixture(name):
    return os.path.join(FIXTURES_DIR, name)
