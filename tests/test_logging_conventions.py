"""AST-based logging convention checks for stogger.

All rule logic lives in pytest_stogger.rules — this file only selects
which rules to enforce and wires up fixtures / config.
"""

import pytest

from pytest_stogger.report import format_violations
from pytest_stogger.rules import (
    check_bind_for_repeating,
    check_complexity_needs_log,
    check_context_required,
    check_debug_no_replace_msg,
    check_exception_no_dupe,
    check_info_layer,
    check_info_requires_replace_msg,
    check_kebab_case,
    check_no_fstring,
    check_private_no_info,
)


def test_logging_conventions(
    source_files,
    stogger_source,
    stogger_config,
    stogger_infrastructure_files,
) -> None:
    """All logging convention rules must pass — zero violations."""
    violations = {}
    violations.update(check_kebab_case(source_files))
    violations.update(check_context_required(source_files))
    violations.update(check_no_fstring(source_files))
    violations.update(check_info_requires_replace_msg(source_files))
    violations.update(check_debug_no_replace_msg(source_files))
    violations.update(check_exception_no_dupe(source_files))
    violations.update(check_bind_for_repeating(source_files))
    violations.update(check_private_no_info(source_files))
    violations.update(check_complexity_needs_log(source_files, exclude_files=stogger_infrastructure_files))
    violations.update(
        check_info_layer(
            source_files,
            allowed_layers=frozenset(stogger_config.get("info_allowed_layers", [])),
            source_root=stogger_source,
        )
    )
    if violations:
        pytest.fail(format_violations(violations))
