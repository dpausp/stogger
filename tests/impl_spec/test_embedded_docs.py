"""Spec validation tests for embedded-docs impl spec.

These tests verify the contracts defined in .agents/impl_specs/embedded-docs.md.
"""

import ast
import re
from importlib.resources import files
from pathlib import Path

import pytest

import stogger

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


# --- packaging ---


def test_llms_txt_exists_and_readable() -> None:
    """SPEC: embedded-docs::packaging — llms.txt must exist in _docs/ and be readable."""
    docs_dir = files("stogger").joinpath("_docs")
    llms_txt = docs_dir.joinpath("llms.txt")
    assert llms_txt.is_file(), f"llms.txt not found at {llms_txt}"
    content = llms_txt.read_text()
    assert content.strip(), "llms.txt is empty"


# --- discovery-test ---


def test_llms_txt_links_resolve() -> None:
    """SPEC: embedded-docs::discovery-test — links in llms.txt must resolve to real files."""
    docs_dir = files("stogger").joinpath("_docs")
    llms_txt = docs_dir.joinpath("llms.txt")
    content = llms_txt.read_text()

    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    links = link_pattern.findall(content)
    assert links, "llms.txt contains no links"

    for text, path in links:
        resolved = docs_dir.joinpath(path)
        assert resolved.is_file(), f"Link [{text}]({path}) does not resolve: {resolved}"


# --- agent-skill ---


def test_agent_skill_md_exists() -> None:
    """SPEC: embedded-docs::agent-skill — _docs/agent_skill.md must exist and be non-empty."""
    agent_skill = files("stogger").joinpath("_docs").joinpath("agent_skill.md")
    assert agent_skill.is_file(), f"agent_skill.md not found at {agent_skill}"
    content = agent_skill.read_text()
    assert content.strip(), "agent_skill.md is empty"


# --- init-discovery ---


def test_docs_path_attribute() -> None:
    """SPEC: embedded-docs::init-discovery — __docs_path__ must exist and _docs/ must be present."""
    assert hasattr(stogger, "__docs_path__"), "stogger has no __docs_path__ attribute"
    docs_path = stogger.__docs_path__
    assert isinstance(docs_path, Path), f"__docs_path__ is {type(docs_path)}, expected Path"
    docs_dir = docs_path / "_docs"
    assert docs_dir.is_dir(), f"_docs/ directory not found at {docs_dir}"


def test_init_docstring_describes_layout() -> None:
    """SPEC: embedded-docs::init-discovery — docstring must describe _docs/ layout without llms-full.txt."""
    docstring = stogger.__doc__
    assert docstring is not None, "stogger has no module docstring"

    assert "_docs" in docstring, "Docstring does not mention _docs"
    assert "llms.txt" in docstring, "Docstring does not mention llms.txt"
    assert "_sources" in docstring, "Docstring does not mention _sources"
    assert "llms-full.txt" not in docstring, "Docstring still references deprecated llms-full.txt"


# --- build-script ---


def test_build_script_is_idempotent() -> None:
    """SPEC: embedded-docs::build-script — script must remove old _docs/ before copying."""
    script_path = REPO_ROOT / "scripts" / "build_docs_for_package.py"
    assert script_path.is_file(), f"Build script not found at {script_path}"

    source = script_path.read_text()
    assert "_docs" in source, "Build script does not reference _docs"
    assert "rmtree" in source, "Build script does not remove old _docs/ before copying (not idempotent)"


# --- llms-full-txt ---


def test_llms_full_txt_disabled() -> None:
    """SPEC: embedded-docs::llms-full-txt — conf.py must set llms_txt_full_build = False."""
    conf_path = REPO_ROOT / "docs" / "conf.py"
    source = conf_path.read_text()
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "llms_txt_full_build":
                    assert isinstance(node.value, ast.Constant), (
                        f"llms_txt_full_build is {ast.dump(node.value)}, expected Constant",
                    )
                    assert node.value.value is False, (
                        f"llms_txt_full_build is {node.value.value}, expected False"
                    )
                    return

    pytest.fail("llms_txt_full_build not found in conf.py")
