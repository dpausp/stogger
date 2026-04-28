"""Meta-check: every non-debug log event must be asserted in a test.

Scans source for log calls (info/warning/error/exception), extracts event IDs,
then scans test files for matching ``log.has("event-id")`` assertions.  Any
event ID found in source but not covered by a test causes a failure.

TDD-friendly: write the test with ``log.has("expected-id")`` first,
then implement the log call.
"""

import pytest

from pytest_stogger.report import format_violations
from pytest_stogger.rules import check_logging_coverage


def test_non_debug_log_calls_have_assertions(
    source_files,
    test_files,
    stogger_config,
) -> None:
    """Every non-debug log call must have a matching log.has() assertion."""
    violations = check_logging_coverage(
        source_files,
        test_files,
        exempt_event_ids=frozenset(
            stogger_config.get("exempt_event_ids", [])
        ),
    )
    if violations:
        pytest.fail(format_violations(violations))
