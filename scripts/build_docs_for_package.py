"""Copy Sphinx-generated docs into the package source tree for embedding.

Copies ``_sources/`` and ``llms.txt`` from ``docs/_build/html/`` into
``src/stogger/_docs/``, copies the agent skill file, and rewrites paths
so links resolve from the embedded location.

Idempotent: removes old ``_docs/`` before copying.
"""

import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SPHINX_OUTPUT = REPO_ROOT / "docs" / "_build" / "html"
TARGET_DIR = REPO_ROOT / "src" / "stogger" / "_docs"
AGENT_SKILL = REPO_ROOT / ".agents" / "skills" / "stogger-logging.md"


def main() -> None:
    if not SPHINX_OUTPUT.is_dir():
        sys.exit(f"ERROR: Sphinx output not found at {SPHINX_OUTPUT}")
    if not AGENT_SKILL.is_file():
        sys.exit(f"ERROR: Agent skill not found at {AGENT_SKILL}")

    # Idempotent: remove old _docs/ before copying
    if TARGET_DIR.is_dir():
        shutil.rmtree(TARGET_DIR)

    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    # Copy _sources/
    sources_src = SPHINX_OUTPUT / "_sources"
    if sources_src.is_dir():
        shutil.copytree(sources_src, TARGET_DIR / "_sources", dirs_exist_ok=True)

    # Copy and fix llms.txt
    llms_src = SPHINX_OUTPUT / "llms.txt"
    if llms_src.is_file():
        content = llms_src.read_text()
        # Fix paths: /_sources/ → _sources/ (relative to _docs/)
        content = content.replace("/_sources/", "_sources/")

        # Add agent_skill.md as first entry in the ## Docs section
        agent_line = "- [Agent Skill (Logging Conventions)](agent_skill.md)"
        lines = content.split("\n")
        new_lines: list[str] = []
        inserted = False
        for line in lines:
            new_lines.append(line)
            if line.startswith("## Docs") and not inserted:
                new_lines.append(agent_line)
                inserted = True
        content = "\n".join(new_lines)

        (TARGET_DIR / "llms.txt").write_text(content)

    # Copy agent skill as agent_skill.md
    shutil.copy2(AGENT_SKILL, TARGET_DIR / "agent_skill.md")

    print(f"Copied embedded docs to {TARGET_DIR}")
    print(f"  llms.txt: {(TARGET_DIR / 'llms.txt').is_file()}")
    print(f"  _sources/: {(TARGET_DIR / '_sources').is_dir()}")
    print(f"  agent_skill.md: {(TARGET_DIR / 'agent_skill.md').is_file()}")


if __name__ == "__main__":
    main()
