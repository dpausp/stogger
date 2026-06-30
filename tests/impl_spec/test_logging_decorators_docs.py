"""Spec validation tests for logging-decorators-docs.

These tests define the CONTRACT that the implementation must fulfill.
All tests are marked xfail because the changes don't exist yet.
They will be garbage-collected after Phase 2 makes them green.
"""

import importlib
import importlib.util
import pathlib
import re

# --- api-docs-visibility: module rename ---


def test_decorators_module_importable():
    """stogger.decorators module MUST exist and be importable."""
    import stogger.decorators  # noqa: F401


def test_old_decorators_module_gone():
    """stogger._decorators module MUST NOT exist after rename."""
    result = importlib.util.find_spec("stogger._decorators")
    assert result is None, "stogger._decorators must not exist after rename to stogger.decorators"


def test_decorators_module_exports_all_symbols():
    """All 5 public symbols must be importable from stogger.decorators."""
    from stogger.decorators import LogScope, log_call, log_operation, log_result, log_scope  # noqa: F401


def test_top_level_re_exports_sourced_from_decorators():
    """Top-level imports must resolve through stogger.decorators (not _decorators)."""
    from stogger import log_call

    # The re-export chain must go through the renamed module
    assert log_call.__module__ == "stogger.decorators", (
        f"Top-level re-export still points to old module: {log_call.__module__}"
    )


# --- spec-test-cleanup ---


def test_old_spec_test_file_removed():
    """tests/impl_spec/test_logging_decorators.py must not exist after cleanup."""
    old_test = pathlib.Path(__file__).parent / "test_logging_decorators.py"
    assert not old_test.exists(), f"Old spec test file must be removed: {old_test}"


# --- docstring-quality: LogScope fix ---


def test_logscope_docstring_has_complete_event_schema():
    """LogScope class docstring MUST contain a complete event schema example."""
    from stogger import LogScope

    doc = LogScope.__doc__
    assert doc is not None, "LogScope must have a docstring"

    # Must contain event schema references for both success and failure
    assert "scope-end" in doc, "Docstring must document scope-end event"
    assert "scope-failed" in doc, "Docstring must document scope-failed event"

    # Must contain a complete JSON-like event example with proper closing
    # The docstring should have at least one complete event dict showing all fields
    # for the success case: event, scope, duration_ms, and bound fields
    has_complete_example = bool(
        re.search(r'"event".*"scope-end".*"duration_ms"', doc, re.DOTALL)
    )
    assert has_complete_example, (
        "LogScope docstring must contain a complete event schema with "
        '"event", "scope-end", and "duration_ms" fields'
    )


def test_logscope_docstring_no_truncated_json():
    """LogScope docstring MUST NOT contain truncated/incomplete JSON in event schema blocks."""
    from stogger import LogScope

    doc = LogScope.__doc__
    assert doc is not None, "LogScope must have a docstring"

    # Find all lines that start a dict literal (event schema blocks)
    # and check that none are truncated (ending with comma but no closing brace on same/next lines)
    # Specifically: lines like {"event": "scope-end", "scope": "<name>", ...  are truncated
    truncated_pattern = re.compile(r'\{["\s\w]*"event"[:\s]*"[^"]+",.*,\s*$')
    truncated_lines = [
        line.strip()
        for line in doc.splitlines()
        if truncated_pattern.search(line)
    ]
    assert not truncated_lines, (
        f"LogScope docstring contains truncated JSON event schemas: {truncated_lines}"
    )


# --- Import chain integrity (derived from api-docs-visibility) ---


def test_log_call_module_is_decorators():
    """log_call.__module__ MUST be stogger.decorators (not stogger._decorators)."""
    from stogger import log_call

    assert log_call.__module__ == "stogger.decorators", (
        f"Expected log_call.__module__ == 'stogger.decorators', got '{log_call.__module__}'"
    )


def test_log_scope_module_is_decorators():
    """log_scope.__module__ MUST be stogger.decorators."""
    from stogger import log_scope

    assert log_scope.__module__ == "stogger.decorators", (
        f"Expected log_scope.__module__ == 'stogger.decorators', got '{log_scope.__module__}'"
    )


def test_log_result_module_is_decorators():
    """log_result.__module__ MUST be stogger.decorators."""
    from stogger import log_result

    assert log_result.__module__ == "stogger.decorators", (
        f"Expected log_result.__module__ == 'stogger.decorators', got '{log_result.__module__}'"
    )


def test_log_operation_module_is_decorators():
    """log_operation.__module__ MUST be stogger.decorators."""
    from stogger import log_operation

    assert log_operation.__module__ == "stogger.decorators", (
        f"Expected log_operation.__module__ == 'stogger.decorators', got '{log_operation.__module__}'"
    )


def test_logscope_class_module_is_decorators():
    """LogScope class __module__ MUST be stogger.decorators."""
    from stogger import LogScope

    assert LogScope.__module__ == "stogger.decorators", (
        f"Expected LogScope.__module__ == 'stogger.decorators', got '{LogScope.__module__}'"
    )
