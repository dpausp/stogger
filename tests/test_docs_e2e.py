"""End-to-end tests for Sphinx doc building and HTML output verification.

Runs sphinx-build for real (no mocks) and verifies the generated HTML.
All tests use the ``docs`` mark so they only run in the tox docs environment.
"""

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
DOCS_BUILD = DOCS_DIR / "_build" / "html"


# ---------------------------------------------------------------------------
# Session-scoped fixture: build docs once for the whole module
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def build_docs():
    """Build Sphinx docs once for all tests in this module."""
    index_html = DOCS_BUILD / "index.html"
    if not index_html.exists():
        subprocess.run(
            [
                "sphinx-build",
                "-b",
                "html",
                str(DOCS_DIR),
                str(DOCS_BUILD),
            ],
            check=True,
            capture_output=True,
            text=True,
        )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.docs
def test_sphinx_build_succeeds():
    index_html = DOCS_BUILD / "index.html"
    assert index_html.exists(), f"sphinx-build output not found at {index_html}"


@pytest.mark.docs
def test_index_html_contains_project_name():
    html = (DOCS_BUILD / "index.html").read_text(encoding="utf-8")
    assert "stogger" in html.lower(), "project name missing from index.html"
    assert "<title>" in html, "<title> tag missing from index.html"


@pytest.mark.docs
def test_user_guide_pages_exist():
    user_guide_dir = DOCS_BUILD / "user_guide"
    html_files = list(user_guide_dir.glob("**/*.html"))
    assert len(html_files) >= 1, "no HTML files found under user_guide/"

    first = html_files[0].read_text(encoding="utf-8").lstrip().lower()
    assert first.startswith("<!doctype") or "<html" in first, f"{html_files[0].name} does not look like valid HTML"


@pytest.mark.docs
def test_no_broken_links_in_index():
    html = (DOCS_BUILD / "index.html").read_text(encoding="utf-8")

    href_pattern = re.compile(r'<a\s[^>]*href="([^"]+)"', re.IGNORECASE)
    relative_hrefs = {
        match.group(1).split("#")[0].split("?")[0]
        for match in href_pattern.finditer(html)
        if not match.group(1).startswith(("http", "mailto:", "#", "javascript:"))
    }

    for href in sorted(relative_hrefs):
        if not href:
            continue
        resolved = DOCS_BUILD / href
        assert resolved.exists(), f"broken link in index.html: {href}"


@pytest.mark.docs
def test_static_assets_exist():
    static_dir = DOCS_BUILD / "_static"
    assert static_dir.is_dir(), "_static/ directory missing from build output"
    contents = list(static_dir.iterdir())
    assert len(contents) > 0, "_static/ directory is empty — no CSS/JS copied"


@pytest.mark.docs
def test_search_functionality_built():
    search_index = DOCS_BUILD / "searchindex.js"
    assert search_index.exists(), "searchindex.js missing — Sphinx search not built"
