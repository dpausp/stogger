#!/usr/bin/env python3
"""Release all stogger projects together.

Bumps version (CalVer), commits, and tags each project.
Projects default to: stogger, pytest-stogger, stogger-systemd.

Usage:
    python scripts/release.py              # release all projects
    python scripts/release.py stogger      # release single project
    python scripts/release.py --dry-run    # show what would happen
"""

import subprocess
import sys
from pathlib import Path

PROJECTS = {
    "stogger": Path(__file__).resolve().parent.parent,
    "pytest-stogger": Path(__file__).resolve().parent.parent.parent / "pytest-stogger",
    "stogger-systemd": Path(__file__).resolve().parent.parent.parent / "stogger-systemd",
}


def run(cmd: list[str], cwd: Path, dry_run: bool) -> None:
    label = f"[{cwd.name}] " + " ".join(cmd)
    print(f"  {label}")
    if dry_run:
        return
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  FAILED: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    if result.stdout.strip():
        print(f"  {result.stdout.strip()}")


def release_project(name: str, path: Path, dry_run: bool) -> None:
    if not path.is_dir():
        print(f"  SKIP {name}: {path} not found")
        return
    print(f"\nReleasing {name} ({path})")
    run(["uvx", "bump-my-version", "bump", "release"], cwd=path, dry_run=dry_run)


def main() -> None:
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    targets = [a for a in args if not a.startswith("--")]

    if dry_run:
        print("DRY RUN — no changes will be made")

    if targets:
        for t in targets:
            if t not in PROJECTS:
                print(f"Unknown project: {t}. Available: {', '.join(PROJECTS)}")
                sys.exit(1)
            release_project(t, PROJECTS[t], dry_run)
    else:
        for name, path in PROJECTS.items():
            release_project(name, path, dry_run)

    print("\nDone.")


if __name__ == "__main__":
    main()
