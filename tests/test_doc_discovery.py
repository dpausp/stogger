"""Tests for embedded documentation discovery in the installed package.

Verify that Sphinx-generated docs are accessible via importlib.resources
and that the __docs_path__ attribute works for agent discovery.
"""

import re
from importlib.resources import files
from pathlib import Path

import pytest
import stogger

_docs_path = Path(__file__).resolve().parent.parent / "src" / "stogger" / "_docs"
if not _docs_path.exists():
    pytest.skip("Embedded docs not generated — run build_docs_for_package.py", allow_module_level=True)


def test_llms_txt_exists_and_readable() -> None:
    """llms.txt must exist in _docs/ and be readable via importlib.resources."""
    docs_dir = files("stogger").joinpath("_docs")
    llms_txt = docs_dir.joinpath("llms.txt")
    assert llms_txt.is_file(), f"llms.txt not found at {llms_txt}"
    content = llms_txt.read_text()
    assert content.strip(), "llms.txt is empty"


def test_llms_txt_links_resolve() -> None:
    """Links in llms.txt must resolve to real files in _docs/."""
    docs_dir = files("stogger").joinpath("_docs")
    llms_txt = docs_dir.joinpath("llms.txt")
    content = llms_txt.read_text()

    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    links = link_pattern.findall(content)
    assert links, "llms.txt contains no links"

    for text, path in links:
        resolved = docs_dir.joinpath(path)
        assert resolved.is_file(), f"Link [{text}]({path}) does not resolve: {resolved}"


def test_agent_skill_md_exists() -> None:
    """_docs/agent_skill.md must exist and be non-empty."""
    agent_skill = files("stogger").joinpath("_docs").joinpath("agent_skill.md")
    assert agent_skill.is_file(), f"agent_skill.md not found at {agent_skill}"
    content = agent_skill.read_text()
    assert content.strip(), "agent_skill.md is empty"


def test_docs_path_attribute() -> None:
    """__docs_path__ must point to a directory containing _docs/."""
    assert hasattr(stogger, "__docs_path__"), "stogger has no __docs_path__ attribute"
    docs_path = stogger.__docs_path__
    assert isinstance(docs_path, Path), f"__docs_path__ is {type(docs_path)}, expected Path"
    docs_dir = docs_path / "_docs"
    assert docs_dir.is_dir(), f"_docs/ directory not found at {docs_dir}"
