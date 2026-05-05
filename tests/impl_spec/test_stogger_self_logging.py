"""Spec validation tests for stogger-self-logging.

These tests define the CONTRACT that the stogger-self-logging implementation
must fulfill. All tests are marked xfail because the feature doesn't exist yet.
They will be garbage-collected after implementation makes them green.

Spec: .agents/impl_specs/stogger-self-logging.md

Decision coverage:
  - overall-strategy: real logging at non-circular code paths + per-file-ignores
  - logging-level: debug for most, warning with _replace_msg for PermissionError
  - recursion-safety: PartialFormatter logging is safe (no _replace_msg)
  - config-single-source: remove infrastructure_files, auto-derive from per-file-ignores
  - event-id-naming: kebab-case, max 4 words per CR-1
  - test-strategy: contract tests for new logging paths and config changes
"""

import tomllib
from pathlib import Path
from unittest.mock import patch

import pytest
import structlog


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_structlog():
    """Reset structlog configuration after each test to avoid state leakage."""
    yield
    structlog.reset_defaults()


@pytest.fixture
def captured_logs():
    """Configure structlog to capture all log events into a list."""
    events = []
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.testing.LogCapture(events),
        ],
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.BoundLogger,
        cache_logger_on_first_use=False,
    )
    return events


# ---------------------------------------------------------------------------
# 1. core.py: PermissionError in _build_logger_factories → warning
# ---------------------------------------------------------------------------


@pytest.mark.xfail(reason="Spec validation: implementation pending")
def test_permission_error_logs_warning(captured_logs):
    """_build_logger_factories must log warning on PermissionError.

    SPEC: logging-level — PermissionError at warning with _replace_msg
    because a missing log file is a real operational problem.
    SPEC: overall-strategy — add log.warning() at non-circular code paths.
    """
    from stogger.config import StoggerConfig
    from stogger.core import _build_logger_factories

    cfg = StoggerConfig(enable_systemd=False, enable_postgres=False)

    with patch.object(Path, "open", side_effect=PermissionError("denied")):
        _build_logger_factories(
            logdir=Path("/fake"),
            log_to_console=False,
            syslog_identifier="test",
            cfg=cfg,
        )

    warning_events = [
        e
        for e in captured_logs
        if e.get("event") == "file-open-permission-denied"
    ]
    assert len(warning_events) == 1


# ---------------------------------------------------------------------------
# 2. core.py: PartialFormatter.get_field → debug on missing field
# ---------------------------------------------------------------------------


@pytest.mark.xfail(reason="Spec validation: implementation pending")
def test_partial_formatter_get_field_logs_debug(captured_logs):
    """PartialFormatter.get_field must log debug on missing field (KeyError).

    SPEC: recursion-safety — safe because no _replace_msg per CR-5.
    SPEC: logging-level — debug, no _replace_msg.
    """
    from stogger.core import PartialFormatter

    formatter = PartialFormatter()
    formatter.get_field("nonexistent", [], {})

    debug_events = [
        e
        for e in captured_logs
        if e.get("event") == "format-field-missing"
    ]
    assert len(debug_events) == 1
    assert debug_events[0].get("field_name") == "nonexistent"


# ---------------------------------------------------------------------------
# 3. core.py: PartialFormatter.format_field → debug on bad format
# ---------------------------------------------------------------------------


@pytest.mark.xfail(reason="Spec validation: implementation pending")
def test_partial_formatter_format_field_logs_debug(captured_logs):
    """PartialFormatter.format_field must log debug on format ValueError.

    SPEC: recursion-safety — safe because no _replace_msg per CR-5.
    SPEC: logging-level — debug, no _replace_msg.
    """
    from stogger.core import PartialFormatter

    formatter = PartialFormatter()
    formatter.format_field(object(), "invalid_spec_for_object")

    debug_events = [
        e
        for e in captured_logs
        if e.get("event") == "format-field-bad-format"
    ]
    assert len(debug_events) == 1
    assert "value" in debug_events[0]
    assert "format_spec" in debug_events[0]


# ---------------------------------------------------------------------------
# 4. core.py: init_early_logging → debug on failure (no crash)
# ---------------------------------------------------------------------------


@pytest.mark.xfail(reason="Spec validation: implementation pending")
def test_early_init_logs_on_failure(captured_logs):
    """init_early_logging must log debug and NOT crash on failure.

    SPEC: overall-strategy — replace suppress(Exception) with try/except + debug.
    SPEC: logging-level — debug, no _replace_msg per CR-5.
    """
    from stogger.core import init_early_logging

    with patch("stogger.core.build_timestamp_processor", side_effect=RuntimeError("boom")):
        # Must NOT raise — suppression stays
        init_early_logging()

    debug_events = [
        e
        for e in captured_logs
        if e.get("event") == "early-init-failed"
    ]
    assert len(debug_events) >= 1


# ---------------------------------------------------------------------------
# 5. core.py: ImportError for stogger_postgres → debug
# ---------------------------------------------------------------------------


@pytest.mark.xfail(reason="Spec validation: implementation pending")
def test_postgres_import_error_logs_debug(captured_logs):
    """_build_logger_factories must log debug when stogger_postgres ImportError.

    SPEC: overall-strategy — add log.debug() at non-circular code paths.
    SPEC: logging-level — debug, no _replace_msg per CR-5.
    """
    from stogger.config import StoggerConfig
    from stogger.core import _build_logger_factories

    cfg = StoggerConfig(enable_postgres=True, enable_systemd=False)
    _MSG = "stogger_postgres not available"
    real_import = __import__

    def blocking_import(name, *args, **kwargs):
        if name == "stogger_postgres":
            raise ImportError(_MSG)
        return real_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=blocking_import):
        _build_logger_factories(
            logdir=None,
            log_to_console=False,
            syslog_identifier="test",
            cfg=cfg,
        )

    debug_events = [
        e
        for e in captured_logs
        if e.get("event") == "stogger-postgres-not-installed"
    ]
    assert len(debug_events) == 1


# ---------------------------------------------------------------------------
# 6. config.py: _probe_stogger_section → debug on empty config
# ---------------------------------------------------------------------------


@pytest.mark.xfail(reason="Spec validation: implementation pending")
def test_probe_stogger_section_logs_none(captured_logs):
    """_probe_stogger_section must log debug when config is empty.

    SPEC: overall-strategy — add log.debug() at non-circular code paths.
    SPEC: logging-level — debug, no _replace_msg per CR-5.
    """
    from stogger.config import _probe_stogger_section

    result = _probe_stogger_section({}, Path("/tmp"))
    assert result is None

    debug_events = [
        e for e in captured_logs if e.get("event") == "no-stogger-section"
    ]
    assert len(debug_events) == 1


# ---------------------------------------------------------------------------
# 7. config.py: _probe_hatch_section → debug on empty config
# ---------------------------------------------------------------------------


@pytest.mark.xfail(reason="Spec validation: implementation pending")
def test_probe_hatch_section_logs_none(captured_logs):
    """_probe_hatch_section must log debug when config is empty.

    SPEC: overall-strategy — add log.debug() at non-circular code paths.
    SPEC: logging-level — debug, no _replace_msg per CR-5.
    """
    from stogger.config import _probe_hatch_section

    result = _probe_hatch_section({}, Path("/tmp"))
    assert result is None

    debug_events = [
        e for e in captured_logs if e.get("event") == "no-hatch-section"
    ]
    assert len(debug_events) == 1


# ---------------------------------------------------------------------------
# 8. config.py: _probe_pytest_section → debug on empty config
# ---------------------------------------------------------------------------


@pytest.mark.xfail(reason="Spec validation: implementation pending")
def test_probe_pytest_section_logs_none(captured_logs):
    """_probe_pytest_section must log debug when config is empty.

    SPEC: overall-strategy — add log.debug() at non-circular code paths.
    SPEC: logging-level — debug, no _replace_msg per CR-5.
    """
    from stogger.config import _probe_pytest_section

    result = _probe_pytest_section({}, Path("/tmp"))
    assert result is None

    debug_events = [
        e for e in captured_logs if e.get("event") == "no-pytest-section"
    ]
    assert len(debug_events) == 1


# ---------------------------------------------------------------------------
# 9. Config: _decorators.py in per-file-ignores
# ---------------------------------------------------------------------------


@pytest.mark.xfail(reason="Spec validation: implementation pending")
def test_config_per_file_ignores_decorators():
    """pyproject.toml must have _decorators.py in per-file-ignores with
    except-must-log and complexity-needs-log.

    SPEC: config-single-source — _decorators.py added to per-file-ignores,
    infrastructure_files removed. Single source of truth.
    """
    pyproject = Path("pyproject.toml")
    with pyproject.open("rb") as f:
        config = tomllib.load(f)

    per_file_ignores = config["tool"]["pytest-stogger"]["per-file-ignores"]
    assert "_decorators.py" in per_file_ignores
    assert set(per_file_ignores["_decorators.py"]) == {
        "except-must-log",
        "complexity-needs-log",
    }


# ---------------------------------------------------------------------------
# 10. Config: file-open-permission-denied in exempt_event_ids
# ---------------------------------------------------------------------------


@pytest.mark.xfail(reason="Spec validation: implementation pending")
def test_config_exempt_event_id():
    """pyproject.toml must have file-open-permission-denied in exempt_event_ids.

    SPEC: logging-level — warning event needs _replace_msg and addition
    to exempt_event_ids.
    SPEC: event-id-naming — file-open-permission-denied is kebab-case,
    4 words (CR-1).
    """
    pyproject = Path("pyproject.toml")
    with pyproject.open("rb") as f:
        config = tomllib.load(f)

    exempt_ids = config["tool"]["pytest-stogger"]["exempt_event_ids"]
    assert "file-open-permission-denied" in exempt_ids


# ---------------------------------------------------------------------------
# 11. Config: infrastructure_files key removed
# ---------------------------------------------------------------------------


@pytest.mark.xfail(reason="Spec validation: implementation pending")
def test_config_infrastructure_files_removed():
    """pyproject.toml must NOT have explicit infrastructure_files key.

    SPEC: config-single-source — remove explicit infrastructure_files,
    let conftest.py auto-derive from per-file-ignores. Single source of truth.
    """
    pyproject = Path("pyproject.toml")
    with pyproject.open("rb") as f:
        config = tomllib.load(f)

    stogger_config = config["tool"]["pytest-stogger"]
    assert "infrastructure_files" not in stogger_config
