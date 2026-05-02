"""Permanent integration tests for stogger-systemd dynamic import.

Tests mock the ``stogger_systemd`` import via ``unittest.mock.patch`` to validate
all four integration paths specified in the stogger-systemd impl spec.

Spec: .agents/impl_specs/stogger-systemd.md
Test matrix from spec decision ``test-strategy``:
  1. enable_systemd=True + import succeeds → journal registered
  2. enable_systemd=True + ImportError → fallback (no journal logger)
  3. enable_systemd=False → no import attempt
  4. JOURNAL_STREAM set + ImportError → info message to stderr
"""

import os
import sys
import types
from unittest.mock import MagicMock, patch

import pytest
import structlog

from stogger.core import init_logging


@pytest.fixture(autouse=True)
def _reset_structlog():
    """Reset structlog configuration after each test to avoid state leakage."""
    yield
    structlog.reset_defaults()


# --- Test 1: enable_systemd=True + import succeeds ---


def test_enable_systemd_true_import_succeeds():
    """Journal factory registered in loggers dict when import succeeds.

    SPEC: integration-hook — core attempts ``from stogger_systemd import
    get_journal_logger_factory`` and registers the factory on success.
    SPEC: journal-registration-flow — journal logger registered via dynamic
    import after loggers-dict construction, before ``structlog.configure()``.
    SPEC: api-contract — ``get_journal_logger_factory()`` returns a callable
    factory whose return value is a structlog-compatible logger.
    """
    mock_module = types.ModuleType("stogger_systemd")

    mock_logger_instance = MagicMock()

    class MockFactory:
        def __call__(self):
            return mock_logger_instance

    mock_module.get_journal_logger_factory = MagicMock(return_value=MockFactory())
    mock_module.JournalLogger = type("JournalLogger", (), {})
    mock_module.DummyJournalLogger = type("DummyJournalLogger", (), {})
    mock_module.JournalLoggerFactory = MockFactory

    with (
        patch.dict(sys.modules, {"stogger_systemd": mock_module}),
        patch.dict(os.environ, {}, clear=False),
    ):
        os.environ.pop("JOURNAL_STREAM", None)
        init_logging(logdir=None)

    config = structlog.get_config()
    factory = config.get("logger_factory")
    assert factory is not None
    assert "journal" in factory.factories


# --- Test 2: enable_systemd=True + ImportError → fallback ---


def test_enable_systemd_true_import_error_fallback():
    """No crash and no journal logger when import fails with ImportError.

    SPEC: integration-hook — falls back to stub on ImportError. Zero-config
    for users.
    SPEC: fallback-behavior — graceful fallback when stogger-systemd absent.
    SPEC: acceptance criterion 3 — ``init_logging()`` falls back gracefully
    when stogger-systemd absent.
    """
    with (
        patch.dict(sys.modules, {"stogger_systemd": None}),
        patch.dict(os.environ, {}, clear=False),
    ):
        os.environ.pop("JOURNAL_STREAM", None)
        init_logging(logdir=None)

    config = structlog.get_config()
    factory = config.get("logger_factory")
    assert factory is not None
    assert "journal" not in factory.factories


# --- Test 3: enable_systemd=False → no import attempt ---


def test_enable_systemd_false_no_import():
    """No import attempt when enable_systemd=False in config.

    SPEC: enable-systemd-source — ``enable_systemd`` comes from
    ``pyproject.toml`` config only. ``init_logging()`` reads
    ``StoggerConfig`` internally.
    SPEC: acceptance criterion 5 — ``enable_systemd=False`` suppresses all
    journal behavior.
    """
    mock_module = types.ModuleType("stogger_systemd")

    mock_module.get_journal_logger_factory = MagicMock()
    mock_module.JournalLogger = type("JournalLogger", (), {})
    mock_module.DummyJournalLogger = type("DummyJournalLogger", (), {})
    mock_module.JournalLoggerFactory = type("JournalLoggerFactory", (), {})

    with (
        patch.dict(sys.modules, {"stogger_systemd": mock_module}),
        patch("stogger.core.StoggerConfig") as mock_config_cls,
        patch.dict(os.environ, {}, clear=False),
    ):
        os.environ.pop("JOURNAL_STREAM", None)

        mock_cfg = MagicMock()
        mock_cfg.enable_systemd = False
        mock_cfg.systemd_facility = None
        mock_config_cls.return_value = mock_cfg

        init_logging(logdir=None)

    mock_module.get_journal_logger_factory.assert_not_called()


# --- Test 4: JOURNAL_STREAM set + ImportError → info message ---


def test_journal_stream_info_without_package(capsys):
    """Info message printed to stderr when JOURNAL_STREAM set and import fails.

    SPEC: fallback-behavior — one-time info message: "systemd journal detected
    but stogger-systemd not available. Install stogger-systemd package for
    journal integration."
    SPEC: acceptance criterion 4 — info message appears when JOURNAL_STREAM
    detected but package missing.
    """
    with (
        patch.dict(sys.modules, {"stogger_systemd": None}),
        patch.dict(os.environ, {"JOURNAL_STREAM": "123:456"}, clear=False),
    ):
        init_logging(logdir=None)

    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert "stogger-systemd not available" in combined.lower()
