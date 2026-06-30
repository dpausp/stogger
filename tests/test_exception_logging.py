"""AST-based checks for logging conventions in except blocks."""

import pytest

from pytest_stogger.report import format_violations
from pytest_stogger.rules import check_except_must_log, check_no_info_in_except


def test_except_blocks_follow_logging_conventions(source_files, stogger_config) -> None:
    """Except blocks must log and must not use log.info()."""
    pfi = stogger_config.get("per-file-ignores", {})
    skip = {p for p, rules in pfi.items() if "except-must-log" in rules}
    filtered = [(p, t) for p, t in source_files if p.name not in skip]
    violations = {}
    violations.update(check_except_must_log(filtered))
    violations.update(check_no_info_in_except(source_files))
    if violations:
        pytest.fail(format_violations(violations))
