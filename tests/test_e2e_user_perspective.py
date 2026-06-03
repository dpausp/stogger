"""E2E tests: what a library user actually sees on stderr/file after init_logging().

These tests capture the RENDERED output — no log.has(), no structured assertions.
What lands on the wire is what the user sees. Every test asserts on string content
in captured.err or file.read_text(), exactly like an operator reading logs.

Each test is a self-contained scenario: configure stogger one way, log something,
verify the output.
"""

import logging
import os
import sys
import types
from unittest.mock import MagicMock, patch

import pytest
import structlog


@pytest.fixture(autouse=True)
def _cleanup():
    """Reset structlog, stdlib logging, and file handles after each test."""
    yield
    root = logging.getLogger()
    for handler in root.handlers[:]:
        handler.close()
        root.removeHandler(handler)

    if structlog.is_configured():
        config = structlog.get_config()
        factory = config.get("logger_factory")
        if hasattr(factory, "factories"):
            for sub_factory in factory.factories.values():
                if hasattr(sub_factory, "_file") and sub_factory._file not in (sys.stderr, sys.stdout):
                    sub_factory._file.close()

    structlog.reset_defaults()


# --- Scenario 1: Default init, console only, no systemd ---


@pytest.mark.e2e
def test_default_init_no_internals_on_stderr(capsys, monkeypatch):
    """Default init_logging produces no internal events on stderr."""
    monkeypatch.delenv("JOURNAL_STREAM", raising=False)

    # Mock systemd module to prevent any journal events
    mock_module = types.ModuleType("stogger.systemd")
    mock_module.get_journal_logger_factory = MagicMock()
    mock_module._journal_socket_available = MagicMock(return_value=False)
    mock_module.JournalLogger = type("JournalLogger", (), {})
    mock_module.DummyJournalLogger = type("DummyJournalLogger", (), {})

    import stogger

    with patch.dict(sys.modules, {"stogger.systemd": mock_module}):
        stogger.init_logging(logdir=None, log_to_console=True, syslog_identifier="user-persp")

    captured = capsys.readouterr()
    # init_logging itself should be silent on success — no internal noise
    assert captured.err == ""


@pytest.mark.e2e
def test_default_init_user_events_rendered(capsys, monkeypatch):
    """User log.info() produces rendered output with event name and structured data."""
    monkeypatch.delenv("JOURNAL_STREAM", raising=False)

    import stogger

    stogger.init_logging(logdir=None, log_to_console=True, syslog_identifier="user-persp")

    log = structlog.get_logger("myapp")
    log.info("order-placed", order_id=42, item="widget")

    captured = capsys.readouterr()

    assert "order-placed" in captured.err
    assert "42" in captured.err
    assert "widget" in captured.err


@pytest.mark.e2e
def test_default_init_debug_events_filtered(capsys, monkeypatch):
    """User log.debug() is filtered out at default INFO level."""
    monkeypatch.delenv("JOURNAL_STREAM", raising=False)

    import stogger

    stogger.init_logging(logdir=None, log_to_console=True, syslog_identifier="user-persp")

    log = structlog.get_logger("myapp")
    log.debug("internal-diagnostic", detail="should not appear")
    log.info("visible-event")

    captured = capsys.readouterr()

    assert "visible-event" in captured.err
    assert "internal-diagnostic" not in captured.err


# --- Scenario 2: Verbose mode ---


@pytest.mark.e2e
def test_verbose_mode_shows_debug_events(capsys, monkeypatch):
    """verbose=True lowers the threshold — debug events appear in rendered output."""
    monkeypatch.delenv("JOURNAL_STREAM", raising=False)

    import stogger

    stogger.init_logging(verbose=True, logdir=None, log_to_console=True, syslog_identifier="user-persp")

    log = structlog.get_logger("myapp")
    log.debug("debug-visible-now", context="verbose-mode")

    captured = capsys.readouterr()

    assert "debug-visible-now" in captured.err
    assert "verbose-mode" in captured.err


# --- Scenario 3: File logging ---


@pytest.mark.e2e
def test_file_logging_renders_to_file(tmp_path, capsys, monkeypatch):
    """init_logging with logdir writes rendered output to file, not just console."""
    monkeypatch.delenv("JOURNAL_STREAM", raising=False)

    logdir = tmp_path / "logs"
    logdir.mkdir()

    import stogger

    stogger.init_logging(logdir=str(logdir), log_to_console=True, syslog_identifier="user-file")

    log = structlog.get_logger("myapp")
    log.warning("disk-check", percent=85)

    captured = capsys.readouterr()

    # Console has it
    assert "disk-check" in captured.err
    assert "85" in captured.err

    # File also has it
    log_file = logdir / "user-file.log"
    assert log_file.exists()
    file_content = log_file.read_text()
    assert "disk-check" in file_content
    assert "85" in file_content


# --- Scenario 4: Systemd journal active ---


@pytest.mark.e2e
def test_systemd_auto_active_logs_confirmation(capsys, monkeypatch):
    """When journal is available in AUTO mode, init_logging logs systemd-journal-active."""
    monkeypatch.delenv("JOURNAL_STREAM", raising=False)

    from stogger.systemd import DummyJournalLogger

    mock_logger_instance = MagicMock(spec=DummyJournalLogger)

    class MockFactory:
        def __call__(self):
            return mock_logger_instance

    mock_module = types.ModuleType("stogger.systemd")
    mock_module.get_journal_logger_factory = MagicMock(return_value=MockFactory())
    mock_module._journal_socket_available = MagicMock(return_value=True)
    mock_module.JournalLogger = type("JournalLogger", (), {})
    mock_module.DummyJournalLogger = type("DummyJournalLogger", (), {})
    mock_module.JournalLoggerFactory = MockFactory

    import stogger

    with patch.dict(sys.modules, {"stogger.systemd": mock_module}):
        stogger.init_logging(logdir=None, log_to_console=True, syslog_identifier="user-sd")

    captured = capsys.readouterr()

    # The confirmation event should be rendered on stderr
    assert "systemd-journal-active" in captured.err


@pytest.mark.e2e
def test_systemd_auto_unavailable_no_journal_events(capsys, monkeypatch):
    """When journal is unavailable in AUTO mode, no journal-related events on stderr."""
    monkeypatch.delenv("JOURNAL_STREAM", raising=False)

    mock_module = types.ModuleType("stogger.systemd")
    mock_module.get_journal_logger_factory = MagicMock()
    mock_module._journal_socket_available = MagicMock(return_value=False)
    mock_module.JournalLogger = type("JournalLogger", (), {})
    mock_module.DummyJournalLogger = type("DummyJournalLogger", (), {})

    import stogger

    with patch.dict(sys.modules, {"stogger.systemd": mock_module}):
        stogger.init_logging(logdir=None, log_to_console=True, syslog_identifier="user-sd")

    captured = capsys.readouterr()

    # No journal confirmation — journal is not active
    assert "systemd-journal-active" not in captured.err


@pytest.mark.e2e
def test_systemd_auto_unavailable_verbose_still_clean(capsys, monkeypatch):
    """Even in verbose mode, AUTO unavailable produces no socket-check noise."""
    monkeypatch.delenv("JOURNAL_STREAM", raising=False)

    mock_module = types.ModuleType("stogger.systemd")
    mock_module.get_journal_logger_factory = MagicMock()
    mock_module._journal_socket_available = MagicMock(return_value=False)
    mock_module.JournalLogger = type("JournalLogger", (), {})
    mock_module.DummyJournalLogger = type("DummyJournalLogger", (), {})

    import stogger

    with patch.dict(sys.modules, {"stogger.systemd": mock_module}):
        stogger.init_logging(verbose=True, logdir=None, log_to_console=True, syslog_identifier="user-sd")

    captured = capsys.readouterr()

    # Even verbose should not leak pre-configuration internals
    assert "systemd-journal-socket-check" not in captured.err


# --- Scenario 5: Exception rendering ---


@pytest.mark.e2e
def test_exception_renders_traceback_on_stderr(capsys, monkeypatch):
    """log.exception() renders the exception type, message, and traceback on stderr."""
    monkeypatch.delenv("JOURNAL_STREAM", raising=False)

    import stogger

    stogger.init_logging(logdir=None, log_to_console=True, syslog_identifier="user-exc")

    log = structlog.get_logger("myapp")

    try:
        msg = "database connection refused"
        raise ConnectionError(msg)
    except ConnectionError:
        log.exception("db-connect-failed", host="db.example.com")

    captured = capsys.readouterr()

    assert "db-connect-failed" in captured.err
    assert "ConnectionError" in captured.err
    assert "database connection refused" in captured.err
    assert "db.example.com" in captured.err


# --- Scenario 6: _replace_msg renders human-readable text ---


@pytest.mark.e2e
def test_replace_msg_renders_human_readable(capsys, monkeypatch):
    """_replace_msg produces a human-readable formatted message in rendered output."""
    monkeypatch.delenv("JOURNAL_STREAM", raising=False)

    import stogger

    stogger.init_logging(logdir=None, log_to_console=True, syslog_identifier="user-replace")

    log = structlog.get_logger("myapp")
    log.info("user-login", _replace_msg="User {user} logged in from {ip}", user="alice", ip="10.0.0.1")

    captured = capsys.readouterr()

    # The rendered output should contain the human-readable message
    assert "User alice logged in from 10.0.0.1" in captured.err
    # The event name should still be present
    assert "user-login" in captured.err
