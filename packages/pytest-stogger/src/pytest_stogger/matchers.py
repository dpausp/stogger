"""AST node matching primitives."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


def is_method_call(
    node: ast.AST,
    *,
    obj: str,
    methods: frozenset[str] | set[str] | Sequence[str],
) -> tuple[str, ast.Call] | None:
    """Match ``obj.method()`` call patterns.

    Checks whether *node* is an ``ast.Call`` of the form ``<obj>.<method>()``
    where the caller is a plain ``ast.Name`` with ``id`` equal to *obj* and the
    attribute name is in *methods*.

    Args:
        node: Any AST node (typically from ``ast.walk``).
        obj: Expected name of the caller object (e.g. ``"log"``).
        methods: Allowed method names (e.g. ``{"debug", "info", "warning"}``).

    Returns:
        ``(method_name, call_node)`` if matched, otherwise ``None``.

    """
    if not isinstance(node, ast.Call):
        return None
    if not isinstance(node.func, ast.Attribute):
        return None
    if not isinstance(node.func.value, ast.Name):
        return None
    if node.func.value.id != obj:
        return None
    if node.func.attr not in methods:
        return None
    return node.func.attr, node


def find_method_calls(
    tree: ast.AST,
    *,
    obj: str,
    methods: frozenset[str] | set[str] | Sequence[str],
) -> list[tuple[str, ast.Call]]:
    """Return all ``(method_name, call_node)`` matches in *tree*.

    Walks the entire tree and collects every node matching
    :func:`is_method_call`.

    Args:
        tree: Any AST node to walk.
        obj: Expected name of the caller object (e.g. ``"log"``).
        methods: Allowed method names (e.g. ``{"debug", "info", "warning"}``).

    Returns:
        List of ``(method_name, call_node)`` tuples.

    """
    results: list[tuple[str, ast.Call]] = []
    for node in ast.walk(tree):
        match = is_method_call(node, obj=obj, methods=methods)
        if match is not None:
            results.append(match)
    return results
