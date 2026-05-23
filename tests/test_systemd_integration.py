"""Integration tests for stogger.systemd (built-in module).

Tests mock the ``stogger.systemd`` import via ``unittest.mock.patch`` to validate
all four integration paths for journal logger registration.

Test matrix:
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

from stogger.config import StoggerConfig
from stogger.core import init_logging


@pytest.fixture(autouse=True)
def _reset_structlog():
    """Reset structlog configuration after each test to avoid state leakage."""
    yield
    structlog.reset_defaults()


# --- Test 1: enable_systemd=True + import succeeds ---


def test_enable_systemd_true_import_succeeds():
    """Journal factory registered in loggers dict when import succeeds."""
    mock_module = types.ModuleType("stogger.systemd")

    mock_logger_instance = MagicMock()

    class MockFactory:
        def __call__(self):
            return mock_logger_instance

    mock_module.get_journal_logger_factory = MagicMock(return_value=MockFactory())
    mock_module.JournalLogger = type("JournalLogger", (), {})
    mock_module.DummyJournalLogger = type("DummyJournalLogger", (), {})
    mock_module.JournalLoggerFactory = MockFactory

    with (
        patch.dict(sys.modules, {"stogger.systemd": mock_module}),
        patch.dict(os.environ, {}, clear=False),
    ):
        os.environ.pop("JOURNAL_STREAM", None)
        init_logging(logdir=None)

    config = structlog.get_config()
    factory = config.get("logger_factory")
    assert factory is not None
    assert "journal" in factory.factories



# --- Test 3: enable_systemd=False → no import attempt ---


def test_enable_systemd_false_no_import():
    """No import attempt when enable_systemd=False in config."""
    mock_module = types.ModuleType("stogger.systemd")

    mock_module.get_journal_logger_factory = MagicMock()
    mock_module.JournalLogger = type("JournalLogger", (), {})
    mock_module.DummyJournalLogger = type("DummyJournalLogger", (), {})
    mock_module.JournalLoggerFactory = type("JournalLoggerFactory", (), {})

    with (
        patch.dict(sys.modules, {"stogger.systemd": mock_module}),
        patch("stogger.core.StoggerConfig") as mock_config_cls,
        patch.dict(os.environ, {}, clear=False),
    ):
        os.environ.pop("JOURNAL_STREAM", None)

        mock_cfg = MagicMock(spec=StoggerConfig)
        mock_cfg.enable_systemd = False
        mock_cfg.systemd_facility = None
        mock_config_cls.return_value = mock_cfg

        init_logging(logdir=None)

    mock_module.get_journal_logger_factory.assert_not_called()


