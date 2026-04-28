"""Violation collection and formatting for pytest output."""

from __future__ import annotations


def format_violations(
    violations: dict[str, list[str]],
) -> str:
    """Format a violations dict into a human-readable report string.

    The returned string is suitable for ``pytest.fail()``. Each rule is listed
    with its count and all individual violation messages indented below it.

    Args:
        violations: Mapping of rule name to list of violation message strings.

    Returns:
        Formatted multi-line report string. Empty string if no violations.

    """
    if not violations:
        return ""

    total = sum(len(v) for v in violations.values())
    parts = [f"\n{total} convention violation(s):"]
    for rule in sorted(violations):
        parts.append(f"\n  {rule} ({len(violations[rule])}):")
        parts.extend(f"    {v}" for v in violations[rule])
    return "\n".join(parts)
