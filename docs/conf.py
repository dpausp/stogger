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
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    # Markdown support
    "myst_parser",
    # Automatic API documentation (static analysis)
    "autoapi.extension",
    # Source code viewing
    "sphinx.ext.viewcode",
    # Type hints in documentation
    "sphinx_autodoc_typehints",
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
    # Graphviz diagrams
    "sphinx.ext.graphviz",
    # TODO directives
    "sphinx.ext.todo",
    # Open Graph metadata
    "sphinxext.opengraph",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- autoapi configuration ---------------------------------------------------
autoapi_type = "python"
autoapi_dirs = ["../src/stogger"]
autoapi_file_patterns = ["*.py"]
autoapi_generate_api_docs = True
autoapi_add_toctree_entry = False
autoapi_root = "api"

autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
]

# Keep generated files for debugging
autoapi_keep_files = True


# Skip private members and test files
def autoapi_skip_member(app, what, name, obj, skip, options):
    if name.startswith("_") and not name.startswith("__"):
        return True
    if "Test" in name or "test_" in name:
        return True
    return skip


def setup(app):
    app.connect("autoapi-skip-member", autoapi_skip_member)


# -- Type hints presentation -------------------------------------------------
autodoc_typehints = "description"
autodoc_typehints_format = "short"

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
html_static_path = ["_static"]

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

# Custom CSS
html_css_files = [
    "custom.css",
    "logo.css",
]

# -- Copy button configuration ----------------------------------------------
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True
copybutton_only_copy_prompt_lines = True
copybutton_remove_prompts = True

# -- Intersphinx configuration ----------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "structlog": ("https://www.structlog.org/en/stable/", None),
}

# -- Coverage-based documentation tiers --------------------------------------
# Modules organized by test coverage for documentation prioritization
COVERAGE_TIERS = {
    "tier1_full": [  # ≥80% coverage - comprehensive documentation
        "__main__",
        "log_reviewer",
        "config",
        "journal_viewer",
        "advanced_assistant",
        "i18n",
        "factory",
        "core",
        "eliot_integration",
    ],
    "tier2_basic": [  # 40-80% coverage - basic documentation
        "linter",
        "assistant",
        "interactive_transformer",
        "gitignore_utils",
        "project_analyzer",
        "i18n_check",
        "cli",
        "systemd_integration",
    ],
    "tier3_minimal": [  # <40% coverage - minimal docs + warnings
        "live_editor",
        "web_dashboard",
        "log_statement_analyzer",
        "cli_output_transformer",
    ],
}
