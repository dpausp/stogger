"""Sphinx configuration for stogger."""

import subprocess
from importlib.metadata import version as _pkg_version
from pathlib import Path

# -- Project information -----------------------------------------------------

project = "stogger"
copyright = "2024-2026, stogger contributors"  # noqa: A001
author = "stogger contributors"

# -- Version -----------------------------------------------------------------

_pkg = "stogger"

# Full version (e.g. "2026.5.4")
try:
    release = _pkg_version(_pkg)
except Exception:
    release = "unknown"

# Short version for sidebar (major.minor)
version = ".".join(release.split(".")[:2])


# Git short rev
def _git_rev() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            cwd=Path(__file__).parent,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


git_rev = _git_rev()

# -- General configuration ---------------------------------------------------

extensions = [
    # Markdown support
    "myst_parser",
    # AI-friendly output (llms.txt)
    "sphinx_llms_txt",
    # UX enhancements
    "sphinx_copybutton",
    "sphinx_design",
    # Additional
    "sphinx.ext.intersphinx",
    "notfound.extension",
    # Toggle buttons (collapsible content)
    "sphinx_togglebutton",
    # Open Graph metadata
    "sphinxext.opengraph",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- sphinx-llm configuration ------------------------------------------------
llms_txt_build_parallel = True
llms_txt_full_build = False
llms_txt_description = "stogger - A sophisticated multi-target structured logging system built on structlog"

# -- MyST Parser configuration ----------------------------------------------
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "dollarmath",
    "fieldlist",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "strikethrough",
    "substitution",
    "tasklist",
]
myst_heading_anchors = 3

# -- Furo theme configuration -----------------------------------------------
html_theme = "furo"
html_title = f"stogger v{release} ({git_rev})"

html_theme_options = {
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
    "light_css_variables": {
        "color-brand-primary": "#2563eb",
        "color-brand-content": "#2563eb",
        "color-admonition-background": "#f8fafc",
    },
    "dark_css_variables": {
        "color-brand-primary": "#60a5fa",
        "color-brand-content": "#60a5fa",
    },
    "source_repository": "https://github.com/stogger/stogger",
    "source_branch": "main",
    "source_directory": "docs/",
}

# -- Intersphinx configuration ----------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "structlog": ("https://www.structlog.org/en/stable/", None),
}
