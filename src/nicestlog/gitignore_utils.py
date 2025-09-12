"""Utilities for respecting .gitignore patterns in file analysis."""

import fnmatch
from pathlib import Path

import structlog

log = structlog.get_logger(__name__)


def load_gitignore_patterns(directory: Path) -> list[str]:
    """Load patterns from .gitignore file."""
    gitignore_path = directory / ".gitignore"
    patterns = []

    if gitignore_path.exists():
        try:
            content = gitignore_path.read_text(encoding="utf-8")
            for line in content.splitlines():
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith("#"):
                    patterns.append(line)

            log.info(
                "gitignore-loaded",
                count=len(patterns),
                gitignore_path=str(gitignore_path),
            )
        except Exception as e:
            log.warning(
                "gitignore-load-failed",
                error=str(e),
                gitignore_path=str(gitignore_path),
            )

    # Add common patterns that should always be ignored for AST analysis
    default_patterns = [
        ".git/*",
        ".venv/*",
        "venv/*",
        "__pycache__/*",
        "*.pyc",
        "*.pyo",
        "*.egg-info/*",
        ".tox/*",
        ".pytest_cache/*",
        "node_modules/*",
        ".mypy_cache/*",
        ".ruff_cache/*",
        "build/*",
        "dist/*",
    ]

    patterns.extend(default_patterns)
    return patterns


def should_ignore_path(file_path: Path, base_dir: Path, patterns: list[str]) -> bool:
    """Check if a file path should be ignored based on gitignore patterns."""
    try:
        # Get relative path from base directory
        rel_path = file_path.relative_to(base_dir)
        rel_path_str = str(rel_path)

        # Check each pattern
        for pattern in patterns:
            # Handle directory patterns (ending with /)
            if pattern.endswith("/"):
                pattern = pattern.rstrip("/") + "/*"

            # Check if pattern matches
            if fnmatch.fnmatch(rel_path_str, pattern):
                return True

            # Also check if any parent directory matches
            for parent in rel_path.parents:
                parent_str = str(parent)
                if fnmatch.fnmatch(parent_str, pattern.rstrip("/*")):
                    return True

        return False

    except ValueError:
        # File is not relative to base_dir, ignore it
        return True


def filter_python_files(directory: Path, respect_gitignore: bool = True) -> list[Path]:
    """Get Python files in directory, respecting .gitignore if requested."""
    # Filtering Python files

    # Load gitignore patterns if requested
    patterns = []
    if respect_gitignore:
        patterns = load_gitignore_patterns(directory)

    # Find all Python files
    python_files = []
    for py_file in directory.rglob("*.py"):
        if py_file.is_file():
            # Check if file should be ignored
            if respect_gitignore and should_ignore_path(py_file, directory, patterns):
                continue

            python_files.append(py_file)

    # Found Python files

    return python_files
