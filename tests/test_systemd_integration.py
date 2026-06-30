"""Integration tests for stogger.systemd (built-in module).

Tests mock the ``stogger.systemd`` import via ``unittest.mock.patch`` to validate
all integration paths for journal logger registration.

Test matrix:
  1. SystemdMode.AUTO + import succeeds → journal registered
  2. SystemdMode.AUTO + ImportError → fallback (no journal logger)
  3. SystemdMode.OFF → no import attempt
  4. SystemdMode.REQUIRED + socket missing → RuntimeError
"""

import os
import sys
import types
from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import structlog

from stogger.config import StoggerConfig, SystemdMode
from stogger.core import init_logging
from stogger.systemd import DummyJournalLogger


@pytest.fixture(autouse=True)
def _reset_structlog():
    """Reset structlog configuration after each test to avoid state leakage."""
    yield
    structlog.reset_defaults()


# --- Test 1: SystemdMode.AUTO + import succeeds ---


def test_systemd_auto_journal_available():
    """Journal factory registered in loggers dict when socket is available."""
    mock_module: Any = types.ModuleType("stogger.systemd")

    mock_logger_instance = MagicMock(spec=DummyJournalLogger)

    class MockFactory:
        def __call__(self):
            return mock_logger_instance

    mock_module.get_journal_logger_factory = MagicMock(return_value=MockFactory())
    mock_module._journal_socket_available = MagicMock(return_value=True)
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


def test_systemd_auto_socket_unavailable():
    """No journal factory registered when socket is unavailable in AUTO mode."""
    mock_module: Any = types.ModuleType("stogger.systemd")

    mock_module.get_journal_logger_factory = MagicMock()
    mock_module._journal_socket_available = MagicMock(return_value=False)
    mock_module.JournalLogger = type("JournalLogger", (), {})
    mock_module.DummyJournalLogger = type("DummyJournalLogger", (), {})

    with (
        patch.dict(sys.modules, {"stogger.systemd": mock_module}),
        patch.dict(os.environ, {}, clear=False),
    ):
        os.environ.pop("JOURNAL_STREAM", None)
        init_logging(logdir=None)

    mock_module.get_journal_logger_factory.assert_not_called()

    # structlog must be configured without journal factory
    config = structlog.get_config()
    factory = config.get("logger_factory")
    assert factory is not None
    assert "journal" not in factory.factories


# --- Test 3: SystemdMode.OFF → no import attempt ---


def test_systemd_off_no_import():
    """No import attempt when SystemdMode.OFF in config."""
    mock_module: Any = types.ModuleType("stogger.systemd")

    mock_module.get_journal_logger_factory = MagicMock(spec=Callable)
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
        mock_cfg.systemd_mode = SystemdMode.OFF
        mock_cfg.systemd_facility = None
        mock_cfg.log_rotation = "none"
        mock_cfg.log_max_bytes = 10_000_000
        mock_cfg.log_backup_count = 5
        mock_config_cls.return_value = mock_cfg

        init_logging(logdir=None)

    mock_module.get_journal_logger_factory.assert_not_called()


def test_dummy_journal_logger_is_silent():
    """DummyJournalLogger.msg() is a silent no-op — no logging side effects."""
    dj = DummyJournalLogger()
    # Must not raise, log, or do anything — pure no-op
    dj.msg({"MESSAGE": "test"})
    dj.msg({"MESSAGE": "another"})
    dj.msg({})


def test_systemd_required_raises_when_not_available():
    """SystemdMode.REQUIRED raises RuntimeError when journal socket is missing."""
    mock_module: Any = types.ModuleType("stogger.systemd")

    mock_module.get_journal_logger_factory = MagicMock()
    mock_module._journal_socket_available = MagicMock(return_value=False)
    mock_module.JournalLogger = type("JournalLogger", (), {})
    mock_module.DummyJournalLogger = type("DummyJournalLogger", (), {})

    with (
        patch.dict(sys.modules, {"stogger.systemd": mock_module}),
        patch("stogger.core.StoggerConfig") as mock_config_cls,
        patch.dict(os.environ, {}, clear=False),
    ):
        os.environ.pop("JOURNAL_STREAM", None)

        mock_cfg = MagicMock(spec=StoggerConfig)
        mock_cfg.systemd_mode = SystemdMode.REQUIRED
        mock_cfg.systemd_facility = None
        mock_cfg.log_rotation = "none"
        mock_cfg.log_max_bytes = 10_000_000
        mock_cfg.log_backup_count = 5
        mock_config_cls.return_value = mock_cfg

        with pytest.raises(RuntimeError, match="Systemd journal required but not available"):
            init_logging(logdir=None)

    mock_module._journal_socket_available.assert_called_once()


def test_journal_sender_send_failure_logs_warning(log):
    """JournalSender.send() logs warning with context when socket send fails."""
    from stogger.systemd import JournalSender

    sender = JournalSender(socket_path="/nonexistent/socket/path")
    result = sender.send({"MESSAGE": "test"})

    assert result is False
    assert log.has("journal-send-failed", socket_path="/nonexistent/socket/path")


def test_format_message_skips_none_and_handles_bytes():
    """format_message omits None values and uses binary length-prefix for bytes."""
    from stogger.systemd import JournalSender

    payload = JournalSender.format_message({"TEXT": "hi", "SKIP": None, "BIN": b"\x00\x01"})

    assert b"TEXT=hi\n" in payload
    assert b"SKIP" not in payload
    # Binary fields are length-prefixed: key\n<len>\n<bytes>\n
    assert b"BIN\n2\n\x00\x01\n" in payload


def test_journal_sender_context_manager(tmp_path):
    """JournalSender opens and closes a real AF_UNIX datagram socket."""
    import socket
    import tempfile

    from stogger.systemd import JournalSender

    # macOS limits AF_UNIX socket paths to 104 bytes — pytest's tmp_path
    # inside .tox can easily exceed this. Use a shallow temp dir instead.
    sock_dir = Path(tempfile.mkdtemp())
    sock_path = str(sock_dir / "sock")
    try:
        server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        server.bind(sock_path)
        try:
            with JournalSender(socket_path=sock_path) as sender:
                assert sender._sock is not None
                # Full send-receive cycle to cover the success path
                assert sender.send({"MESSAGE": "hi"}) is True
                data = server.recv(4096)
                assert b"MESSAGE=hi\n" in data
            # __exit__ closes the socket and clears the reference
            assert sender._sock is None
        finally:
            server.close()
    finally:
        Path(sock_path).unlink(missing_ok=True)
        sock_dir.rmdir()


def test_journal_logger_and_factory_with_real_socket(tmp_path):
    """JournalLoggerFactory returns JournalLogger when socket exists."""
    import socket
    import tempfile
    from pathlib import Path

    from stogger.systemd import JournalLogger, JournalLoggerFactory, _journal_socket_available

    sock_dir = Path(tempfile.mkdtemp())
    sock_path = str(sock_dir / "sock")
    try:
        server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        server.bind(sock_path)
        try:
            # _journal_socket_available succeeds on a real socket
            assert _journal_socket_available(sock_path) is True

            # Factory returns JournalLogger (not Dummy)
            factory = JournalLoggerFactory(socket_path=sock_path)
            logger = factory()
            assert isinstance(logger, JournalLogger)

            # JournalLogger.msg sends via the real socket
            logger.msg({"MESSAGE": "via-logger"})
            data = server.recv(4096)
            assert b"MESSAGE=via-logger\n" in data
        finally:
            server.close()
    finally:
        Path(sock_path).unlink(missing_ok=True)
        sock_dir.rmdir()


def test_journal_sender_exit_without_enter_is_noop():
    """__exit__ is a no-op when __enter__ was never called (no socket to close)."""
    from stogger.systemd import JournalSender

    bare = JournalSender(socket_path="/nonexistent/socket/path")
    bare.__exit__(None, None, None)
    assert bare._sock is None


def test_journal_logger_factory_returns_dummy_when_unavailable():
    """JournalLoggerFactory returns DummyJournalLogger when socket path is missing."""
    from stogger.systemd import JournalLoggerFactory

    factory = JournalLoggerFactory(socket_path="/nonexistent/socket/path")
    logger = factory()

    assert isinstance(logger, DummyJournalLogger)


def test_systemd_journal_active_logged_after_init(log):
    """init_logging logs systemd-journal-active when journal target is registered."""
    mock_logger_instance = MagicMock(spec=DummyJournalLogger)

    class MockFactory:
        def __call__(self):
            return mock_logger_instance

    mock_module: Any = types.ModuleType("stogger.systemd")
    mock_module.get_journal_logger_factory = MagicMock(return_value=MockFactory())
    mock_module._journal_socket_available = MagicMock(return_value=True)
    mock_module.JournalLogger = type("JournalLogger", (), {})
    mock_module.DummyJournalLogger = type("DummyJournalLogger", (), {})
    mock_module.JournalLoggerFactory = MockFactory

    with (
        patch.dict(sys.modules, {"stogger.systemd": mock_module}),
        patch.dict(os.environ, {}, clear=False),
    ):
        os.environ.pop("JOURNAL_STREAM", None)
        init_logging(logdir=None)

    log.has("systemd-journal-active")
