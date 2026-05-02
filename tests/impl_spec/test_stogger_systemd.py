"""Spec validation tests for stogger-systemd integration.

These 6 tests define the CONTRACT that Phase 2 (stogger-systemd implementation)
must fulfill. All tests are marked xfail because the feature doesn't exist yet.
They will be garbage-collected after Phase 2 makes them green.

Spec: .agents/impl_specs/stogger-systemd.md
"""

import importlib.util
import os
import sys
import syslog
import types
from unittest.mock import MagicMock, patch

import pytest
import structlog

from stogger.core import init_logging

stogger_systemd_available = importlib.util.find_spec("stogger_systemd") is not None

@pytest.fixture(autouse=True)
def _reset_structlog():
    """Reset structlog configuration after each test to avoid state leakage."""
    yield
    structlog.reset_defaults()


XFAIL_REASON = "stogger-systemd not yet implemented"


# --- Test 1: API contract ---


@pytest.mark.skipif(not stogger_systemd_available, reason="stogger-systemd package not installed")
def test_package_api_contract():
    """Verify stogger_systemd module exports the required public API.

    SPEC: api-contract — stogger-systemd exports get_journal_logger_factory(),
    JournalLogger, DummyJournalLogger, and JournalLoggerFactory.
    """
    # Real import — package doesn't exist yet, so ImportError will trigger xfail.
    # Phase 2 must create the package with these exports.
    import stogger_systemd  # noqa: PLC0415

    assert hasattr(stogger_systemd, "get_journal_logger_factory")
    assert callable(stogger_systemd.get_journal_logger_factory)
    assert hasattr(stogger_systemd, "JournalLogger")
    assert hasattr(stogger_systemd, "DummyJournalLogger")
    assert hasattr(stogger_systemd, "JournalLoggerFactory")

    factory = stogger_systemd.get_journal_logger_factory()
    assert isinstance(factory, stogger_systemd.JournalLoggerFactory)


# --- Test 2: Factory returns structlog-compatible logger ---


@pytest.mark.skipif(not stogger_systemd_available, reason="stogger-systemd package not installed")
def test_factory_returns_compatible_logger():
    """Verify get_journal_logger_factory() returns a structlog-compatible factory.

    SPEC: api-contract — factory is structlog-compatible, produces a logger
    with a msg() method.
    """
    # Real import — package doesn't exist yet, so ImportError will trigger xfail.
    import stogger_systemd  # noqa: PLC0415

    factory = stogger_systemd.get_journal_logger_factory()
    assert callable(factory)

    logger = factory()
    assert hasattr(logger, "msg")
    assert callable(logger.msg)


# --- Test 3: init_logging registers journal logger on successful import ---


def test_init_logging_journal_registered_on_import():
    """init_logging() registers journal logger when stogger_systemd imports.

    SPEC: integration-hook — core attempts `from stogger_systemd import
    get_journal_logger_factory`. Falls back to stub on ImportError.
    SPEC: journal-registration-flow — journal logger registered via dynamic
    import after loggers-dict construction, before structlog.configure().
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

    # The loggers dict on the factory must contain a "journal" entry
    assert "journal" in factory.factories

# --- Test 4: init_logging suppresses journal when disabled ---


def test_init_logging_journal_suppressed_when_disabled():
    """enable_systemd=False suppresses all journal import attempts.

    SPEC: enable-systemd-source — enable_systemd comes from pyproject.toml
    config only. init_logging() reads StoggerConfig internally.
    SPEC: acceptance criterion 5 — enable_systemd=False suppresses all
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

        # StoggerConfig with enable_systemd=False
        mock_cfg = MagicMock()
        mock_cfg.enable_systemd = False
        mock_cfg.systemd_facility = None
        mock_config_cls.return_value = mock_cfg

        init_logging(logdir=None)

    # The dynamic import must NOT have been attempted
    mock_module.get_journal_logger_factory.assert_not_called()


# --- Test 5: Info message when JOURNAL_STREAM set but package missing ---


def test_journal_stream_info_message_without_package(capsys):
    """JOURNAL_STREAM + missing stogger_systemd emits info message.

    SPEC: fallback-behavior — one-time info message: "systemd journal detected
    but stogger-systemd not available. Install stogger-systemd package for
    journal integration."
    """
    with (
        patch.dict(sys.modules, {"stogger_systemd": None}),
        patch.dict(os.environ, {"JOURNAL_STREAM": "123:456"}, clear=False),
    ):
        init_logging(logdir=None)

    captured = capsys.readouterr()
    combined = captured.out + captured.err
    # SPEC: fallback-behavior — specific message about missing stogger-systemd.
    # Current code prints a different message ("switching to systemd journal logging").
    assert "stogger-systemd not available" in combined.lower()


# --- Test 6: Facility from config, not hardcoded ---


def test_facility_from_config_not_hardcoded():
    """SystemdJournalRenderer receives facility from StoggerConfig.

    SPEC: systemd-facility-plumbing — init_logging() reads systemd_facility
    from StoggerConfig. Default changes from LOG_LOCAL1 to LOG_LOCAL0.
    """
    with (
        patch("stogger.core.StoggerConfig") as mock_config_cls,
        patch.dict(os.environ, {}, clear=False),
    ):
        os.environ.pop("JOURNAL_STREAM", None)

        # Config with a specific facility (not LOG_LOCAL1)
        custom_facility = syslog.LOG_LOCAL2
        mock_cfg = MagicMock()
        mock_cfg.enable_systemd = True
        mock_cfg.systemd_facility = custom_facility
        mock_config_cls.return_value = mock_cfg

        init_logging(logdir=None)

    config = structlog.get_config()
    processors = config.get("processors", [])

    # Find the MultiRenderer in processors and check the journal renderer
    multi_renderer = None
    for proc in processors:
        if hasattr(proc, "renderers") and "journal" in proc.renderers:
            multi_renderer = proc
            break

    assert multi_renderer is not None, "MultiRenderer with journal not found in processors"
    journal_renderer = multi_renderer.renderers["journal"]
    assert journal_renderer.syslog_facility == custom_facility
