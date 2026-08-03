"""Semantic validation stage of the SiteLang compiler.

The grammar guarantees the file is *syntactically* correct. This module
enforces the *semantic* rules of the language before any external API is
touched, so a bad site definition fails fast and locally instead of half-way
through a deployment.
"""

import re

# Themes the code generator knows how to render. Kept in sync with html_generator.py.
ALLOWED_THEMES = {"light", "dark"}

# GitHub repository names may only contain these characters.
_REPO_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")


class ValidationError(Exception):
    """Raised when a site definition violates a semantic rule."""


def normalize_repo_name(site_name):
    """Turn a site name into a GitHub-safe repository name.

    Lowercases, converts spaces/underscores to hyphens and drops any character
    GitHub would reject. Returns an empty string if nothing usable remains.
    """
    name = (site_name or "").strip().lower()
    name = re.sub(r"[\s_]+", "-", name)
    name = re.sub(r"[^a-z0-9._-]", "", name)
    name = name.strip("-.")
    return name


def is_valid_repo_name(name):
    return bool(name) and name not in (".", "..") and bool(_REPO_NAME_RE.match(name))


def validate_site(site_name, site_attrs, pages):
    """Validate a compiled site model.

    Raises ValidationError (aggregating every problem found) on hard errors.
    Returns a list of non-fatal warnings for the caller to display.
    """
    errors = []
    warnings = []

    if not site_name or not site_name.strip():
        errors.append('the site name (site "...") must not be empty')

    repo_name = normalize_repo_name(site_name)
    if not is_valid_repo_name(repo_name):
        errors.append(
            f'the site name "{site_name}" does not yield a valid repository name'
        )

    if "index" not in pages:
        errors.append('a page named "index" is required (page "index" { ... })')

    theme = site_attrs.get("theme")
    if theme is not None and theme not in ALLOWED_THEMES:
        allowed = ", ".join(sorted(ALLOWED_THEMES))
        errors.append(f'theme "{theme}" is invalid; allowed values are: {allowed}')

    # Non-fatal quality hints: the site still deploys without these.
    if not site_attrs.get("title"):
        warnings.append('no "title" set; falling back to the site name')
    if not site_attrs.get("description"):
        warnings.append('no "description" set; the <meta description> will be empty')
    if "index" in pages and not pages["index"].get("hero"):
        warnings.append('the "index" page has no "hero" text; using a default heading')

    if errors:
        raise ValidationError(
            "invalid site definition:\n" + "\n".join(f"  - {e}" for e in errors)
        )

    return warnings
