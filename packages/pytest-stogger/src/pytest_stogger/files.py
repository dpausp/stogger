"""Source file discovery and AST parsing."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


def walk_python_files(
    source: Path,
    *,
    exclude: frozenset[str] = frozenset(),
) -> Iterator[tuple[Path, ast.Module]]:
    """Yield ``(path, tree)`` for every parseable ``.py`` file under *source*.

    Skips files whose first directory component under *source* is in *exclude*.
    Files that fail to parse (``SyntaxError``) or cannot be read (``OSError``)
    are silently skipped.

    Args:
        source: Root directory to scan recursively.
        exclude: Directory names to skip (matched against the first path
            component relative to *source*).

    Yields:
        Tuples of ``(file_path, ast_module)``.

    """
    for path in sorted(source.rglob("*.py")):
        rel_parts = path.relative_to(source).parts
        if rel_parts and rel_parts[0] in exclude:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, OSError):
            continue
        yield path, tree
