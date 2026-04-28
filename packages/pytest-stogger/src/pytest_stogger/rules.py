"""Built-in logging convention rules.

Each rule function takes ``(path, tree)`` pairs and returns a
``{rule_name: [violation_message, ...]}`` dict.  Compose freely in
your test files:

    from pytest_stogger.rules import (
        check_kebab_case,
        check_no_fstring,
    )
    from pytest_stogger.report import format_violations

    def test_my_conventions(source_files):
        violations = {}
        violations.update(check_kebab_case(source_files))
        violations.update(check_no_fstring(source_files))
        if violations:
            pytest.fail(format_violations(violations))
"""

from __future__ import annotations

import ast
import re
from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from .matchers import find_method_calls, is_method_call

# --- Constants ---

LOG_METHODS = frozenset({"debug", "info", "warn", "warning", "error", "exception"})

REPLACE_MSG_METHODS = frozenset({"info", "warn", "warning"})

KEBAB_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")

_NON_KEBAB = re.compile(r"[A-Z]|_+|\s+")

EXCEPTION_DUPE_KEYS = frozenset({"error", "exc", "exception", "e"})

BIND_THRESHOLD = 3

SCOPE_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)


# --- Helpers ---


def _collect_log_calls_in_func(
    func_node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[tuple[str, ast.Call]]:
    """Collect all (method, call) pairs of log.*() calls within a function body."""
    calls: list[tuple[str, ast.Call]] = []
    for node in ast.walk(func_node):
        match = is_method_call(node, obj="log", methods=LOG_METHODS)
        if match is not None:
            calls.append(match)
    return calls


def _find_repeating_keys(calls: list[tuple[str, ast.Call]]) -> list[str]:
    """Return keyword arg names that appear in 3+ different log calls."""
    key_counter: Counter[str] = Counter()
    seen_per_call: set[frozenset[str]] = set()

    for _, call in calls:
        keys = frozenset(kw.arg for kw in call.keywords if kw.arg)
        if keys in seen_per_call:
            continue
        seen_per_call.add(keys)
        for kw in call.keywords:
            if kw.arg:
                key_counter[kw.arg] += 1

    return [key for key, count in key_counter.items() if count >= BIND_THRESHOLD]


def _visit_functions(
    body: list[ast.stmt], class_name: str | None = None
) -> list[tuple[ast.FunctionDef | ast.AsyncFunctionDef, str | None]]:
    """Yield (func_node, class_name) for all function/method definitions."""
    results: list[tuple[ast.FunctionDef | ast.AsyncFunctionDef, str | None]] = []
    for node in body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            results.append((node, class_name))
            results.extend(_visit_functions(node.body, class_name))
        elif isinstance(node, ast.ClassDef):
            results.extend(_visit_functions(node.body, node.name))
    return results


def _has_log_call(body: list[ast.stmt]) -> bool:
    """Check if body contains any log.xxx() call (excluding nested scopes)."""
    stack: list[ast.AST] = list(body)
    while stack:
        node = stack.pop()
        if is_method_call(node, obj="log", methods=LOG_METHODS) is not None:
            return True
        stack.extend(c for c in ast.iter_child_nodes(node) if not isinstance(c, SCOPE_NODES))
    return False


def _has_log_info(body: list[ast.stmt]) -> bool:
    """Check if body contains log.info() call (excluding nested scopes)."""
    stack: list[ast.AST] = list(body)
    while stack:
        node = stack.pop()
        if is_method_call(node, obj="log", methods=frozenset({"info"})) is not None:
            return True
        stack.extend(c for c in ast.iter_child_nodes(node) if not isinstance(c, SCOPE_NODES))
    return False


def _to_kebab(s: str) -> str:
    """Best-effort conversion to kebab-case."""
    s = _NON_KEBAB.sub("-", s).strip("-")
    return re.sub(r"-{2,}", "-", s).lower()


# --- Rule functions ---


def check_kebab_case(
    source_files: list[tuple[Path, ast.Module]],
) -> dict[str, list[str]]:
    """Rule: Event IDs must be strict kebab-case."""
    violations: list[str] = []
    for path, tree in source_files:
        rel = str(path)
        for _method, call in find_method_calls(tree, obj="log", methods=LOG_METHODS):
            if call.args and isinstance(call.args[0], ast.Constant) and isinstance(call.args[0].value, str):
                event_id = call.args[0].value
                if not KEBAB_RE.match(event_id):
                    violations.append(
                        f"{rel}:{call.lineno} — event ID {event_id!r} is not kebab-case "
                        f"→ expected { _to_kebab(event_id)!r}"
                    )
    return {"log-kebab-case-event-id": violations} if violations else {}


def check_context_required(
    source_files: list[tuple[Path, ast.Module]],
) -> dict[str, list[str]]:
    """Rule: Every log call needs at least one keyword argument."""
    violations: list[str] = []
    for path, tree in source_files:
        rel = str(path)
        for method, call in find_method_calls(tree, obj="log", methods=LOG_METHODS):
            if not call.keywords:
                violations.append(
                    f"{rel}:{call.lineno} — log.{method}() has no keyword arguments "
                    f'→ add at least one key=value, e.g. log.{method}("event-id", user_id=42)'
                )
    return {"log-context-required": violations} if violations else {}


def check_no_fstring(
    source_files: list[tuple[Path, ast.Module]],
) -> dict[str, list[str]]:
    """Rule: No f-strings in any log argument."""
    violations: list[str] = []
    for path, tree in source_files:
        rel = str(path)
        for method, call in find_method_calls(tree, obj="log", methods=LOG_METHODS):
            all_values = [*call.args, *(kw.value for kw in call.keywords)]
            if any(isinstance(v, ast.JoinedStr) for v in all_values):
                violations.append(
                    f"{rel}:{call.lineno} — f-string in log.{method}() call "
                    f'→ use log.{method}("event-id", key=value) instead'
                )
    return {"log-no-fstring": violations} if violations else {}


def check_info_requires_replace_msg(
    source_files: list[tuple[Path, ast.Module]],
) -> dict[str, list[str]]:
    """Rule: log.info()/log.warn()/log.warning() must include ``_replace_msg``."""
    violations: list[str] = []
    for path, tree in source_files:
        rel = str(path)
        for method, call in find_method_calls(tree, obj="log", methods=LOG_METHODS):
            if method in REPLACE_MSG_METHODS and not any(kw.arg == "_replace_msg" for kw in call.keywords):
                violations.append(
                    f"{rel}:{call.lineno} — log.{method}() missing _replace_msg "
                    f'→ add _replace_msg="..." as keyword argument'
                )
    return {"log-requires-replace-msg": violations} if violations else {}


def check_debug_no_replace_msg(
    source_files: list[tuple[Path, ast.Module]],
) -> dict[str, list[str]]:
    """Rule: log.debug() must NOT include ``_replace_msg``."""
    violations: list[str] = []
    for path, tree in source_files:
        rel = str(path)
        for method, call in find_method_calls(tree, obj="log", methods=LOG_METHODS):
            if method == "debug" and any(kw.arg == "_replace_msg" for kw in call.keywords):
                violations.append(
                    f"{rel}:{call.lineno} — log.debug() must not have _replace_msg "
                    f'→ use log.info("event-id", _replace_msg="...") if you need message replacement'
                )
    return {"log-debug-no-replace-msg": violations} if violations else {}


def check_exception_no_dupe(
    source_files: list[tuple[Path, ast.Module]],
) -> dict[str, list[str]]:
    """Rule: log.exception() must not duplicate exception info as keyword args."""
    violations: list[str] = []
    for path, tree in source_files:
        rel = str(path)
        for method, call in find_method_calls(tree, obj="log", methods=LOG_METHODS):
            if method == "exception":
                dupe_keys = [kw.arg for kw in call.keywords if kw.arg in EXCEPTION_DUPE_KEYS]
                if dupe_keys:
                    violations.append(
                        f"{rel}:{call.lineno} — log.exception() has redundant key(s): {', '.join(dupe_keys)} "
                        f"→ log.exception() already captures the exception automatically"
                    )
    return {"log-exception-no-error-keyword": violations} if violations else {}


def check_bind_for_repeating(
    source_files: list[tuple[Path, ast.Module]],
) -> dict[str, list[str]]:
    """Rule: Repeating keyword args across log calls in the same function → use log.bind()."""
    violations: list[str] = []
    for path, tree in source_files:
        rel = str(path)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            calls = _collect_log_calls_in_func(node)
            if len(calls) < BIND_THRESHOLD:
                continue
            repeating = _find_repeating_keys(calls)
            if repeating:
                violations.append(
                    f"{rel}:{node.lineno} — function {node.name!r}: "
                    f"key(s) {', '.join(repeating)} appear in {BIND_THRESHOLD}+ log calls "
                    f"→ use log.bind({', '.join(f'{k}=...' for k in repeating[:2])}) to set once"
                )
    return {"log-use-bind-for-repeating-keys": violations} if violations else {}


def check_except_must_log(
    source_files: list[tuple[Path, ast.Module]],
    *,
    exclude_files: frozenset[str] = frozenset(),
) -> dict[str, list[str]]:
    """Rule: Every except block must contain at least one log call."""
    violations: list[str] = []
    for path, tree in source_files:
        if path.name in exclude_files:
            continue
        rel = str(path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue
            has_log = any(is_method_call(n, obj="log", methods=LOG_METHODS) is not None for n in ast.walk(node))
            if not has_log:
                rule = "except-as-must-log" if node.name else "except-must-log"
                violations.append(
                    f"{rel}:{node.lineno} — {rule}: except block has no log call "
                    f'→ add log.exception("event-id") or log.error("event-id", ...)'
                )
    return {"except-must-log": violations} if violations else {}


def check_no_info_in_except(
    source_files: list[tuple[Path, ast.Module]],
) -> dict[str, list[str]]:
    """Rule: No log.info() in except blocks."""
    violations: list[str] = []
    for path, tree in source_files:
        rel = str(path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue
            for _, call in find_method_calls(node, obj="log", methods=frozenset({"info"})):
                violations.append(
                    f"{rel}:{call.lineno} — no-log-info-in-except: "
                    f"use log.exception/error/warning/debug, not log.info()"
                )
    return {"no-log-info-in-except": violations} if violations else {}


def check_private_no_info(
    source_files: list[tuple[Path, ast.Module]],
) -> dict[str, list[str]]:
    """Rule: Private functions/methods must not use log.info()."""
    violations: list[str] = []
    for path, tree in source_files:
        rel = str(path)
        for func_node, class_name in _visit_functions(tree.body):
            if not func_node.name.startswith("_"):
                continue
            if _has_log_info(func_node.body):
                qualname = f"{class_name}.{func_node.name}" if class_name else func_node.name
                violations.append(
                    f"{rel}:{func_node.lineno} — "
                    f"{qualname}() uses log.info() — "
                    f"private methods must use log.debug/warning/error/exception"
                )
    return {"private-no-log-info": violations} if violations else {}


def check_info_layer(
    source_files: list[tuple[Path, ast.Module]],
    *,
    allowed_layers: frozenset[str] = frozenset(),
    source_root: Path | None = None,
) -> dict[str, list[str]]:
    """Rule: log.info() only in configured layer directories.

    Returns empty dict if *allowed_layers* is empty (rule disabled).
    """
    violations: list[str] = []
    if not allowed_layers or source_root is None:
        return {}
    for path, tree in source_files:
        try:
            layer = path.relative_to(source_root).parts[0]
        except ValueError:
            continue
        rel = str(path)
        for _, call in find_method_calls(tree, obj="log", methods=frozenset({"info"})):
            if layer not in allowed_layers:
                violations.append(
                    f"{rel}:{call.lineno} — log.info() only allowed in: {', '.join(sorted(allowed_layers))}"
                )
    return {"log-info-layer-restriction": violations} if violations else {}


def check_complexity_needs_log(
    source_files: list[tuple[Path, ast.Module]],
    *,
    exclude_files: frozenset[str] = frozenset(),
) -> dict[str, list[str]]:
    """Rule: Functions with cognitive complexity >= 1 must contain a log call.

    Silently returns empty dict if ``complexipy`` is not installed.
    """
    try:
        from complexipy import file_complexity
    except ImportError:
        return {}

    violations: list[str] = []
    for path, tree in source_files:
        if path.name in exclude_files:
            continue
        func_index: dict[tuple[int, int], str] = {}
        for func_node, class_name in _visit_functions(tree.body):
            qualname = f"{class_name}.{func_node.name}" if class_name else func_node.name
            func_index[(func_node.lineno, func_node.end_lineno or 0)] = qualname

        result = file_complexity(str(path))
        for fn in result.functions:
            if fn.complexity < 1:
                continue

            func_node = None
            for node, _ in _visit_functions(tree.body):
                if node.lineno == fn.line_start and (node.end_lineno or 0) == fn.line_end:
                    func_node = node
                    break

            if func_node is None:
                continue

            if _has_log_call(func_node.body):
                continue

            rel = str(path)
            key = (fn.line_start, fn.line_end)
            qualname = func_index.get(key, fn.name.replace("::", "."))

            violations.append(
                f"{rel}:{fn.line_start} — {qualname}() has CC={fn.complexity} but no log call "
                f"→ add logging for error handling, branching, or key decisions"
            )

    return {"complexity-needs-log": violations} if violations else {}


def check_logging_coverage(
    source_files: list[tuple[Path, ast.Module]],
    test_files: list[tuple[Path, ast.Module]],
    *,
    exempt_event_ids: frozenset[str] = frozenset(),
    methods: frozenset[str] | None = None,
) -> dict[str, list[str]]:
    """Rule: Every non-debug log call must have a matching log.has() assertion in tests.

    Args:
        source_files: Parsed source files from the ``source_files`` fixture.
        test_files: Parsed test files from the ``test_files`` fixture.
        exempt_event_ids: Event IDs exempt from coverage checking.
        methods: Log methods to check (default: info, warning, error, exception).

    """
    if methods is None:
        methods = frozenset({"info", "warning", "error", "exception"})

    # Collect event IDs from source
    source_events: dict[str, list[str]] = {}
    for path, tree in source_files:
        rel = str(path)
        for _, call in find_method_calls(tree, obj="log", methods=methods):
            if call.args and isinstance(call.args[0], ast.Constant) and isinstance(call.args[0].value, str):
                event_id = call.args[0].value
                source_events.setdefault(event_id, []).append(f"{rel}:{call.lineno}")

    # Collect asserted event IDs from test files
    asserted_ids: set[str] = set()
    for _path, tree in test_files:
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "has"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "log"
            ):
                args = node.args
                if args and isinstance(args[0], ast.Constant) and isinstance(args[0].value, str):
                    asserted_ids.add(args[0].value)

    # Find uncovered
    uncovered = {
        eid: locs for eid, locs in source_events.items() if eid not in asserted_ids and eid not in exempt_event_ids
    }

    if uncovered:
        msgs: list[str] = []
        for eid in sorted(uncovered):
            msgs.append(f"  {eid} → add log.has({eid!r}) in tests")
            msgs.extend(f"    {loc}" for loc in uncovered[eid])
        return {"logging-coverage": msgs}
    return {}
