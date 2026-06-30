"""Spec validation tests for stogger-self-logging.

These tests define the CONTRACT that the stogger-self-logging implementation
must fulfill. All tests pass — spec fully implemented.

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
    cap = structlog.testing.LogCapture()
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            cap,
        ],
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.BoundLogger,
        cache_logger_on_first_use=False,
    )
    # Allow init_early_logging() to enter its setup code while still
    # capturing events through the configured LogCapture pipeline.
    structlog._config._CONFIG.is_configured = False  # noqa: SLF001
    return cap.entries


# ---------------------------------------------------------------------------
# 1. core.py: PermissionError in _build_logger_factories → warning
# ---------------------------------------------------------------------------


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


def test_early_init_crashes_on_failure():
    """init_early_logging must propagate errors, not suppress them.

    SPEC: legacy-elimination::broad-exception-cleanup — remove try/except entirely.
    """
    from stogger.core import init_early_logging

    with patch("stogger.core.build_timestamp_processor", side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError, match="boom"):
            init_early_logging()


# ---------------------------------------------------------------------------
# 5. core.py: ImportError for stogger_postgres → debug
# ---------------------------------------------------------------------------


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
# 9. Config: decorators.py uses inline ignore instead of per-file-ignores
# ---------------------------------------------------------------------------


def test_config_decorators_inline_ignore():
    """decorators.py must NOT be in per-file-ignores; instead _filter_args()
    has an inline ignore for complexity-needs-log.

    RATIONALE: per-file-ignores suppresses ALL log calls in a file for the
    budget rule. Using inline ignore on the single violating function avoids
    suppressing the ~30 legitimate decorator log calls.
    """
    pyproject = Path("pyproject.toml")
    with pyproject.open("rb") as f:
        config = tomllib.load(f)

    per_file_ignores = config["tool"]["pytest-stogger"]["per-file-ignores"]
    assert "decorators.py" not in per_file_ignores

    # Verify inline ignore exists on the def line
    source = Path("src/stogger/decorators.py").read_text()
    lines = source.splitlines()
    for line in lines:
        if line.strip().startswith("def _filter_args("):
            assert "stogger: ignore complexity-needs-log" in line, (
                f"Expected inline ignore on _filter_args() def line: {line!r}"
            )
            break
    else:
        pytest.fail("_filter_args() not found in decorators.py")


# ---------------------------------------------------------------------------
# 10. Config: file-open-permission-denied in exempt_event_ids
# ---------------------------------------------------------------------------


def test_config_exempt_event_ids_empty():
    """pyproject.toml must have empty exempt_event_ids.

    SPEC: logging-level — all events covered by log.has() tests,
    no exemptions needed.
    """
    pyproject = Path("pyproject.toml")
    with pyproject.open("rb") as f:
        config = tomllib.load(f)

    exempt_ids = config["tool"]["pytest-stogger"]["exempt_event_ids"]
    assert exempt_ids == []


# ---------------------------------------------------------------------------
# 11. Config: infrastructure_files key removed
# ---------------------------------------------------------------------------


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
