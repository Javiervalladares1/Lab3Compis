"""Code generation stage of the SiteLang compiler.

Takes the plain-Python model that the listener extracts from the parse tree
(site name, site-level attributes and pages) and produces a complete, valid
and responsive ``index.html`` document. Every value coming from the DSL is
HTML-escaped so that user content can never break the surrounding markup.
"""

import html

# Themes the generator knows how to render. Kept in sync with validation.py.
THEMES = {
    "dark": {
        "bg": "#0f172a",
        "fg": "#e2e8f0",
        "card_bg": "#1e293b",
        "border": "#334155",
        "accent": "#4ade80",
    },
    "light": {
        "bg": "#ffffff",
        "fg": "#1e293b",
        "card_bg": "#f8fafc",
        "border": "#e2e8f0",
        "accent": "#16a34a",
    },
}

# Index attributes rendered by the header instead of as their own section.
_HEADER_ATTRS = {"hero"}


def _esc(value):
    """Escape a DSL value so it is safe to interpolate into HTML."""
    return html.escape(str(value), quote=True)


def _humanize(key):
    """Turn an attribute identifier (e.g. ``about_me``) into a heading."""
    return key.replace("_", " ").replace("-", " ").strip().title()


def _section(heading, inner_html):
    return (
        "\n  <section>\n"
        f"    <h2>{_esc(heading)}</h2>\n"
        f"    {inner_html}\n"
        "  </section>"
    )


def _attr_section(key, value):
    """Render a single index attribute as an HTML section."""
    if key == "contact":
        addr = _esc(value)
        return _section("Contact", f'<p><a href="mailto:{addr}">{addr}</a></p>')
    return _section(_humanize(key), f"<p>{_esc(value)}</p>")


def _page_section(page_name, attrs):
    """Render a non-index page as one section listing its attributes."""
    rows = "".join(
        f"\n    <p><strong>{_esc(_humanize(k))}:</strong> {_esc(v)}</p>"
        for k, v in attrs.items()
    )
    return (
        "\n  <section>\n"
        f"    <h2>{_esc(_humanize(page_name))}</h2>{rows}\n"
        "  </section>"
    )


def generate_html(site_name, site_attrs, pages):
    """Generate the full HTML document for a compiled site.

    Args:
        site_name:  the identifier from ``site "..."``.
        site_attrs: dict of site-level attributes (title, description, theme...).
        pages:      dict mapping page name -> dict of page attributes.

    Returns:
        A complete HTML5 document as a string.
    """
    title = site_attrs.get("title") or site_name
    description = site_attrs.get("description", "")
    theme = site_attrs.get("theme", "light")
    lang = site_attrs.get("lang", "en")
    colors = THEMES.get(theme, THEMES["light"])

    index = pages.get("index", {})
    hero = index.get("hero") or f"Welcome to {site_name}"

    # Sections come from the index page (except attributes shown in the header)
    # and, after that, from any additional pages defined in the DSL.
    sections = [
        _attr_section(key, value)
        for key, value in index.items()
        if key not in _HEADER_ATTRS
    ]
    sections += [
        _page_section(name, attrs)
        for name, attrs in pages.items()
        if name != "index"
    ]
    main_content = "".join(sections)

    return f"""<!DOCTYPE html>
<html lang="{_esc(lang)}">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{_esc(title)}</title>
  <meta name="description" content="{_esc(description)}" />
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: {colors['bg']};
           color: {colors['fg']}; line-height: 1.7; }}
    header {{ padding: 5rem 1.5rem 4rem; text-align: center; border-bottom: 1px solid {colors['border']}; }}
    header h1 {{ font-size: clamp(1.8rem, 5vw, 3rem); color: {colors['accent']}; margin-bottom: 0.75rem; }}
    header p {{ opacity: 0.75; font-size: 1.1rem; max-width: 600px; margin: 0 auto; }}
    main {{ max-width: 860px; margin: 0 auto; padding: 3rem 1.5rem; }}
    section {{ background: {colors['card_bg']}; border: 1px solid {colors['border']};
              border-radius: 12px; padding: 2rem; margin-bottom: 1.5rem; }}
    section h2 {{ color: {colors['accent']}; font-size: 0.85rem; text-transform: uppercase;
                 letter-spacing: 3px; margin-bottom: 0.75rem; }}
    section p {{ opacity: 0.9; word-wrap: break-word; }}
    a {{ color: {colors['accent']}; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    footer {{ text-align: center; padding: 2rem; opacity: 0.4; font-size: 0.8rem;
             border-top: 1px solid {colors['border']}; }}
    .badge {{ display: inline-block; background: {colors['accent']}22; color: {colors['accent']};
             border: 1px solid {colors['accent']}44; border-radius: 999px; padding: 0.2rem 0.75rem;
             font-size: 0.75rem; margin-top: 1rem; }}
  </style>
</head>
<body>
  <header>
    <h1>{_esc(hero)}</h1>
    <p>{_esc(description)}</p>
    <span class="badge">Built with a custom DSL compiler</span>
  </header>
  <main>{main_content}
  </main>
  <footer>Universidad del Valle de Guatemala &mdash; Construcci&oacute;n de Compiladores 2026</footer>
</body>
</html>"""
