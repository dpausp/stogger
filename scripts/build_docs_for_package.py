#!/usr/bin/env python3
"""Build script: copy Sphinx docs into stogger package for agent discovery.

This runs AFTER sphinx-build has generated docs/_build/html/.
Copies _sources/, llms.txt, and llms-full.txt into the stogger package.
Strips leading '/' from llms.txt links so paths are relative.
"""

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_BUILD = REPO_ROOT / "docs" / "_build" / "html"
PACKAGE_DIR = REPO_ROOT / "packages" / "stogger" / "src" / "stogger"


def main():
    # Ensure Sphinx build exists
    if not (DOCS_BUILD / "index.html").exists():
        print("Sphinx build not found. Running sphinx-build ...")
        subprocess.run(
            ["sphinx-build", "-b", "html", "docs", "docs/_build/html"],
            cwd=REPO_ROOT,
            check=True,
        )

    # Copy _sources/
    dest_sources = PACKAGE_DIR / "_sources"
    if dest_sources.exists():
        print(f"Removing old {dest_sources.relative_to(REPO_ROOT)} ...")
        shutil.rmtree(dest_sources)

    print(f"Copying _sources/ -> {dest_sources.relative_to(REPO_ROOT)} ...")
    shutil.copytree(DOCS_BUILD / "_sources", dest_sources)

    # Copy llms-full.txt
    print("Copying llms-full.txt ...")
    shutil.copy2(DOCS_BUILD / "llms-full.txt", PACKAGE_DIR / "llms-full.txt")

    # Copy and fix llms.txt
    print("Copying llms.txt (fixing relative paths) ...")
    content = (DOCS_BUILD / "llms.txt").read_text(encoding="utf-8")
    content = content.replace("(/", "(")
    (PACKAGE_DIR / "llms.txt").write_text(content, encoding="utf-8")

    # Summary
    source_files = sum(1 for _ in dest_sources.rglob("*") if _.is_file())
    llms_size = (PACKAGE_DIR / "llms-full.txt").stat().st_size
    print(f"Done: {source_files} files in _sources/, llms-full.txt {llms_size:,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
