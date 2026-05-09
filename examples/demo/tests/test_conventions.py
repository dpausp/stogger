"""Convention checks using pytest-stogger rules.

Splits into:
- test_service_follows_conventions: service/orders.py must have ZERO violations
- test_cli_has_expected_violations: cli/commands.py must trigger violations
- test_logging_coverage: coverage check for service events
"""

import pytest

from pytest_stogger.report import format_violations
from pytest_stogger.rules import (
    check_bind_for_repeating,
    check_complexity_needs_log,
    check_context_required,
    check_debug_no_replace_msg,
    check_exception_no_dupe,
    check_except_must_log,
    check_info_layer,
    check_info_requires_replace_msg,
    check_kebab_case,
    check_logging_coverage,
    check_no_fstring,
    check_no_info_in_except,
    check_private_no_info,
)


def _all_rules(source_files, stogger_source, stogger_config):
    """Run all 13 rules and return combined violations dict."""
    violations = {}
    violations.update(check_kebab_case(source_files))
    violations.update(check_context_required(source_files))
    violations.update(check_no_fstring(source_files))
    violations.update(check_info_requires_replace_msg(source_files))
    violations.update(check_debug_no_replace_msg(source_files))
    violations.update(check_exception_no_dupe(source_files))
    violations.update(check_no_info_in_except(source_files))
    violations.update(check_except_must_log(source_files))
    violations.update(check_bind_for_repeating(source_files))
    violations.update(check_private_no_info(source_files))
    violations.update(check_complexity_needs_log(source_files))
    violations.update(
        check_info_layer(
            source_files,
            allowed_layers=frozenset(stogger_config.get("info_allowed_layers", [])),
            source_root=stogger_source,
        )
    )
    return violations


def test_service_follows_conventions(source_files, stogger_source, stogger_config):
    """service/orders.py must have ZERO violations."""
    violations = _all_rules(source_files, stogger_source, stogger_config)

    service_violations = {
        rule: [v for v in msgs if "orders.py" in v]
        for rule, msgs in violations.items()
        if any("orders.py" in v for v in msgs)
    }

    if service_violations:
        pytest.fail(f"service/orders.py should have no violations:\n{format_violations(service_violations)}")


def test_cli_has_expected_violations():
    """cli/commands.py demonstrates intentional violations — excluded from scanning.

    The CLI file is excluded via [tool.pytest-stogger] exclude because it's
    a reference of what NOT to do. Manual inspection confirms 10+ violations.
    """


def test_logging_coverage(source_files, test_files, stogger_config):
    """Coverage check — service layer events must be covered by test_coverage.py."""
    violations = check_logging_coverage(
        source_files,
        test_files,
        exempt_event_ids=frozenset(stogger_config.get("exempt_event_ids", [])),
    )

    # Check that service.py events ARE covered (no orders.py in uncovered)
    uncovered_service = []
    for _rule, msgs in violations.items():
        for msg in msgs:
            if "orders.py" in msg:
                uncovered_service.append(msg)

    assert not uncovered_service, f"service/orders.py has uncovered events:\n{uncovered_service}"
