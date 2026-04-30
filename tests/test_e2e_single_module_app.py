"""End-to-end test: a minimal single-module application using stogger for logging.

This test verifies that stogger works correctly when used as a logging library
in a small application -- from init_logging() through to output verification.

Exercises: init_logging -> structlog.get_logger -> log statements -> console output -> file output.
No mocks. Real structlog pipeline.
"""

import logging

import pytest
import structlog


@pytest.fixture(autouse=True)
def _cleanup_root_logging():
    """Close and remove all root logger handlers after each E2E test."""
    yield
    root = logging.getLogger()
    for handler in root.handlers[:]:
        handler.close()
        root.removeHandler(handler)

    # Close file handles opened by structlog's PrintLoggerFactory
    config = structlog.get_config()
    factory = config.get("logger_factory")
    if hasattr(factory, "factories"):
        for _name, sub_factory in factory.factories.items():
            if hasattr(sub_factory, "_file"):
                sub_factory._file.close()

    structlog.reset_defaults()


def test_single_module_app_console_and_file(tmp_path, capsys, monkeypatch):
    """A minimal app initializes stogger, logs events, and output arrives at console + file."""
    monkeypatch.delenv("JOURNAL_STREAM", raising=False)

    logdir = tmp_path / "logs"
    logdir.mkdir()

    import stogger

    stogger.init_logging(
        logdir=str(logdir),
        log_to_console=True,
        syslog_identifier="e2e-test",
    )

    log = structlog.get_logger("myapp")

    log.info("app-started", version="1.0.0")
    log.warning("disk-space-low", percent=12)
    log.error("connection-failed", host="db.example.com", port=5432)

    captured = capsys.readouterr()

    # Console output (stderr) should contain our events
    assert "app-started" in captured.err
    assert "disk-space-low" in captured.err
    assert "connection-failed" in captured.err

    # Structured key-value data should be present
    assert "version" in captured.err
    assert "db.example.com" in captured.err

    # File output should exist and contain the events
    log_file = logdir / "e2e-test.log"
    assert log_file.exists()

    file_content = log_file.read_text()
    assert "app-started" in file_content
    assert "disk-space-low" in file_content
    assert "connection-failed" in file_content


def test_single_module_app_bound_logger_context(tmp_path, capsys, monkeypatch):
    """Bound logger propagates context to all subsequent log calls."""
    monkeypatch.delenv("JOURNAL_STREAM", raising=False)

    logdir = tmp_path / "logs"
    logdir.mkdir()

    import stogger

    stogger.init_logging(
        logdir=str(logdir),
        log_to_console=True,
        syslog_identifier="e2e-bound",
    )

    log = structlog.get_logger("myapp")
    request_log = log.bind(request_id="req-abc", user_id=42)

    request_log.info("request-started", method="POST", path="/api/users")
    request_log.info("request-completed", status_code=201)

    captured = capsys.readouterr()

    # Both log lines should contain the bound context
    assert "req-abc" in captured.err
    assert captured.err.count("req-abc") >= 2
    assert captured.err.count("user_id") >= 2
    assert "request-started" in captured.err
    assert "request-completed" in captured.err


def test_single_module_app_no_console_when_disabled(tmp_path, capsys, monkeypatch):
    """When log_to_console=False, nothing goes to stderr."""
    monkeypatch.delenv("JOURNAL_STREAM", raising=False)

    logdir = tmp_path / "logs"
    logdir.mkdir()

    import stogger

    stogger.init_logging(
        logdir=str(logdir),
        log_to_console=False,
        syslog_identifier="e2e-noconsole",
    )

    log = structlog.get_logger("myapp")
    log.info("silent-event", key="value")

    captured = capsys.readouterr()

    # No console output, but file should have it
    assert "silent-event" not in captured.err

    log_file = logdir / "e2e-noconsole.log"
    assert log_file.exists()
    assert "silent-event" in log_file.read_text()


def test_single_module_app_exception_logging(tmp_path, capsys, monkeypatch):
    """Exceptions are captured and rendered in log output."""
    monkeypatch.delenv("JOURNAL_STREAM", raising=False)

    logdir = tmp_path / "logs"
    logdir.mkdir()

    import stogger

    stogger.init_logging(
        logdir=str(logdir),
        log_to_console=True,
        syslog_identifier="e2e-exc",
    )

    log = structlog.get_logger("myapp")

    try:
        raise ValueError("something broke")
    except ValueError:
        log.error("operation-failed", exc_info=True)

    captured = capsys.readouterr()

    assert "operation-failed" in captured.err
    assert "ValueError" in captured.err
    assert "something broke" in captured.err
