"""End-to-end test: a minimal single-module application using stogger for logging.

This test verifies that stogger works correctly when used as a logging library
in a small application -- from init_logging() through to output verification.

Exercises: init_logging -> structlog.get_logger -> log statements -> console output -> file output.
No mocks. Real structlog pipeline.
"""

import logging
import sys

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


@pytest.mark.e2e
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


@pytest.mark.e2e
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


@pytest.mark.e2e
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


@pytest.mark.e2e
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


@pytest.mark.e2e
def test_single_module_app_exception_logging_with_log_exception(tmp_path, capsys, monkeypatch):
    """log.exception() injects traceback automatically — no manual exc_info=True needed."""
    monkeypatch.delenv("JOURNAL_STREAM", raising=False)

    logdir = tmp_path / "logs"
    logdir.mkdir()

    import stogger

    stogger.init_logging(
        logdir=str(logdir),
        log_to_console=True,
        syslog_identifier="e2e-exc-auto",
    )

    log = structlog.get_logger("myapp")

    try:
        raise RuntimeError("auto-injected")
    except RuntimeError:
        log.exception("operation-failed")

    captured = capsys.readouterr()

    assert "operation-failed" in captured.err
    assert "RuntimeError" in captured.err
    assert "auto-injected" in captured.err
    assert "Traceback" in captured.err or "traceback" in captured.err.lower()


@pytest.mark.e2e
def test_pipeline_survives_recursion_error_during_exception_formatting(tmp_path, capsys, monkeypatch):
    """Deep stack + exception formatting hits RecursionError → pipeline must not crash.

    Real-world scenario: application has a deep call stack, throws an exception
    with a __context__ chain, and the RecursionError occurs inside Python's
    linecache/traceback module during formatting. The stogger pipeline must
    degrade gracefully and continue accepting log calls — a logger that kills
    itself while trying to log is the worst possible failure mode.

    No journal stream (DummyJournalLogger) — exercises the full pipeline without
    systemd, including the journal-noop path that previously caused re-entry.
    """
    monkeypatch.delenv("JOURNAL_STREAM", raising=False)

    logdir = tmp_path / "logs"
    logdir.mkdir()

    import stogger

    stogger.init_logging(
        logdir=str(logdir),
        log_to_console=True,
        syslog_identifier="e2e-recursion",
    )

    log = structlog.get_logger("myapp")

    # Consume most of the recursion limit with a deep call stack.
    # This leaves very little headroom — when format_exc_info calls
    # traceback.print_exception → linecache.getline, it hits RecursionError.
    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(150)

    try:
        # Nested exception with __context__ chain — exercises the
        # exact code path from the original bug report.
        try:
            raise ValueError("inner-error")
        except ValueError:
            raise RuntimeError("outer-error") from None

        pytest.fail("Should have raised RuntimeError")  # pragma: no cover
    except RuntimeError:
        # This MUST not crash the pipeline — format_exc_info catches
        # the RecursionError internally and provides degraded output.
        log.exception("recursion-scenario")

    # Restore limit BEFORE asserting — otherwise the asserts themselves
    # might hit the low limit if pytest internals are deep enough.
    sys.setrecursionlimit(old_limit)

    captured = capsys.readouterr()

    # The pipeline survived: we got output for the exception event.
    # With degraded formatting we get "[traceback unavailable]", with
    # full formatting we get the actual traceback. Either is acceptable.
    assert "recursion-scenario" in captured.err
    assert "RuntimeError" in captured.err or "traceback unavailable" in captured.err.lower()

    # CRITICAL: the pipeline must still accept new log calls after the
    # RecursionError. If the pipeline is dead, this will either raise
    # an exception or produce no output.
    log.info("pipeline-alive", status="ok")

    captured2 = capsys.readouterr()
    assert "pipeline-alive" in captured2.err

    # File output must also have survived.
    log_file = logdir / "e2e-recursion.log"
    assert log_file.exists()
    file_content = log_file.read_text()
    assert "recursion-scenario" in file_content
    assert "pipeline-alive" in file_content
