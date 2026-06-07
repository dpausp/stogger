"""Regression tests for the package docs build script.

The build script runs concurrently from the ``build`` and ``outsider`` tox
environments (both depend on ``docs``). It must merge into ``_docs/`` in place
and never remove it — a ``shutil.rmtree`` would let one invocation delete files
another is copying. See ``.agents/impl_specs/fix-doc-discovery-isolation.md``.
"""

import importlib.util
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "build_docs_for_package.py"


@pytest.fixture(scope="module")
def build_docs():
    spec = importlib.util.spec_from_file_location("build_docs_for_package", _SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_repeated_build_keeps_target_dir_identity(tmp_path, monkeypatch, build_docs):
    """main() merges into _docs/ in place across repeated invocations.

    A stable inode proves the directory is never deleted and recreated — no
    rmtree runs — which is what makes concurrent ``tox -p`` invocation safe.
    """
    sphinx_out = tmp_path / "html"
    (sphinx_out / "_sources").mkdir(parents=True)
    (sphinx_out / "_sources" / "index.md").write_text("# Home\n")
    (sphinx_out / "llms.txt").write_text("# Stogger\n\n## Docs\n\n- [Home](home)\n")

    target = tmp_path / "src" / "stogger" / "_docs"
    target.mkdir(parents=True)

    agent_skill = tmp_path / "skill.md"
    agent_skill.write_text("# Logging skill\n")

    monkeypatch.setattr(build_docs, "SPHINX_OUTPUT", sphinx_out)
    monkeypatch.setattr(build_docs, "TARGET_DIR", target)
    monkeypatch.setattr(build_docs, "AGENT_SKILL", agent_skill)

    inode_before = target.stat().st_ino

    build_docs.main()
    build_docs.main()  # second, concurrent-style invocation

    assert target.stat().st_ino == inode_before, "main() deleted _docs/ (rmtree present)"
    assert (target / "llms.txt").is_file()
    assert (target / "agent_skill.md").is_file()
    assert (target / "_sources" / "index.md").is_file()
