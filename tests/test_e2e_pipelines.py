"""End-to-end tests for JSON output, async logging, and translation pipelines.

Each test exercises a REAL pipeline end-to-end without mocking internals.
Uses the same patterns as test_e2e_single_module_app.py for cleanup and
test_integration.py for structlog configuration.
"""

import json
import logging
import sys
from logging.handlers import QueueHandler, QueueListener
from queue import Queue

import pytest
import structlog

from stogger.config import StoggerConfig
from stogger.core import SelectRenderedString
from stogger.factory import build_shared_processors


@pytest.fixture(autouse=True)
def _cleanup_logging():
    """Reset structlog and stdlib logging after each E2E test."""
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


def _parse_json_lines(stderr_output: str) -> list[dict]:
    """Extract valid JSON objects from stderr output, ignoring non-JSON lines."""
    events = []
    for line in stderr_output.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            if isinstance(data, dict) and "event" in data:
                events.append(data)
        except json.JSONDecodeError:
            pass
    return events


@pytest.mark.e2e
def test_json_format_pipeline(capsys, monkeypatch):
    """Full pipeline: StoggerConfig(json) → build_shared_processors → log → valid JSON output."""
    monkeypatch.delenv("JOURNAL_STREAM", raising=False)

    config = StoggerConfig(log_format="json")
    processors = build_shared_processors(config)
    processors.append(SelectRenderedString(key="console"))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.BoundLogger,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=False,
    )

    log = structlog.get_logger("json-app")
    log.info("json-event", key="value", count=42)
    log.warning("json-warning", reason="timeout")
    log.error("json-error", code=500)

    captured = capsys.readouterr()
    events = _parse_json_lines(captured.err)

    assert len(events) >= 3

    # Every event must have required structured logging keys
    for event in events:
        assert "event" in event
        assert "level" in event
        assert "timestamp" in event

    # Verify all three events arrived
    event_names = {e["event"] for e in events}
    assert "json-event" in event_names
    assert "json-warning" in event_names
    assert "json-error" in event_names

    # Verify structured data survived JSON round-trip
    json_event = next(e for e in events if e["event"] == "json-event")
    assert json_event["key"] == "value"
    assert json_event["count"] == 42

    json_error = next(e for e in events if e["event"] == "json-error")
    assert json_error["code"] == 500

    json_warning = next(e for e in events if e["event"] == "json-warning")
    assert json_warning["reason"] == "timeout"


@pytest.mark.e2e
def test_async_logging_pipeline(tmp_path, monkeypatch):
    """Async pipeline: QueueHandler → QueueListener → FileHandler → verify file delivery."""
    monkeypatch.delenv("JOURNAL_STREAM", raising=False)

    logdir = tmp_path / "logs"
    logdir.mkdir()
    log_file = logdir / "async-e2e.log"

    # Set up async queue (same pattern as _configure_async_logging in factory.py)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter("%(message)s"))

    log_queue: Queue = Queue(-1)
    queue_handler = QueueHandler(log_queue)
    listener = QueueListener(log_queue, file_handler)
    listener.start()

    # Configure root logger with queue handler
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(queue_handler)
    root.setLevel(logging.DEBUG)

    # Build real structlog processors
    config = StoggerConfig(logdir=logdir, syslog_identifier="async-e2e")
    processors = build_shared_processors(config)
    processors.append(SelectRenderedString(key="console"))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.BoundLogger,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=False,
    )

    # Log through stdlib → async queue → file handler
    logging.info("async-stdlib-event")
    logging.warning("async-stdlib-warning")

    # Flush: stop listener — drains queue and ensures all messages are delivered
    listener.stop()

    # Verify messages were delivered through the async queue
    content = log_file.read_text()
    assert "async-stdlib-event" in content
    assert "async-stdlib-warning" in content


@pytest.mark.e2e
def test_translation_pipeline(tmp_path, capsys, monkeypatch):
    """Translation pipeline: TOML → TranslationProcessor → JSON with translated messages."""
    monkeypatch.delenv("JOURNAL_STREAM", raising=False)

    # Create translation TOML file
    translation_dir = tmp_path / "translations"
    translation_dir.mkdir()
    (translation_dir / "en.toml").write_text(
        'welcome = "Welcome {user} to {app}!"\ngoodbye = "Goodbye {user}!"\n',
    )

    # Build real pipeline with translations + JSON rendering
    # JSON format preserves _translated_msg field in output
    config = StoggerConfig(
        translation_dir=translation_dir,
        language="en",
        log_format="json",
    )
    processors = build_shared_processors(config)
    processors.append(SelectRenderedString(key="console"))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.BoundLogger,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=False,
    )

    log = structlog.get_logger("i18n-app")
    log.info("welcome", user="Alice", app="stogger")
    log.info("goodbye", user="Bob")
    log.info("untranslated-event", detail="no translation key")

    captured = capsys.readouterr()
    events = _parse_json_lines(captured.err)

    # Translated event: welcome → "Welcome Alice to stogger!"
    welcome_events = [e for e in events if e.get("event") == "welcome"]
    assert len(welcome_events) == 1
    assert welcome_events[0]["_translated_msg"] == "Welcome Alice to stogger!"
    assert welcome_events[0]["_original_event"] == "welcome"

    # Translated event: goodbye → "Goodbye Bob!"
    goodbye_events = [e for e in events if e.get("event") == "goodbye"]
    assert len(goodbye_events) == 1
    assert goodbye_events[0]["_translated_msg"] == "Goodbye Bob!"

    # Untranslated event: no _translated_msg field
    untranslated = [e for e in events if e.get("event") == "untranslated-event"]
    assert len(untranslated) == 1
    assert "_translated_msg" not in untranslated[0]
