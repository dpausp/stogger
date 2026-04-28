"""AST-based checks for logging conventions in except blocks."""

import pytest

from pytest_stogger.report import format_violations
from pytest_stogger.rules import check_except_must_log, check_no_info_in_except


def test_except_blocks_follow_logging_conventions(source_files, stogger_infrastructure_files) -> None:
    """Except blocks must log and must not use log.info()."""
    violations = {}
    violations.update(check_except_must_log(source_files, exclude_files=stogger_infrastructure_files))
    violations.update(check_no_info_in_except(source_files))
    if violations:
        pytest.fail(format_violations(violations))
