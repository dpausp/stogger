"""Integration tests for real module interactions and E2E pipeline scenarios."""

import json
import logging
import sys

import pytest
import structlog

from stogger.config import StoggerConfig
from stogger.core import SelectRenderedString, TranslationProcessor, init_logging
from stogger.factory import build_shared_processors


@pytest.fixture(autouse=True)
def _reset_logging():
    """Reset structlog and stdlib logging after each test."""
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


# --- Integration tests ---


@pytest.mark.integration
def test_real_translation_pipeline(tmp_path):
    """Translation TOML → build_shared_processors → TranslationProcessor in chain."""
    translation_dir = tmp_path / "translations"
    translation_dir.mkdir()
    (translation_dir / "en.toml").write_text('greeting = "Hello {name}!"')

    config = StoggerConfig(translation_dir=translation_dir, language="en")
    processors = build_shared_processors(config)

    translation_procs = [p for p in processors if isinstance(p, TranslationProcessor)]
    assert len(translation_procs) == 1

    # Test processor produces translated message with real event dict
    result = translation_procs[0](None, "info", {"event": "greeting", "name": "World"})
    assert result["_translated_msg"] == "Hello World!"
    assert result["_original_event"] == "greeting"


@pytest.mark.integration
def test_real_json_format(capsys, monkeypatch):
    """JSON renderer in real pipeline produces valid JSON output."""
    monkeypatch.delenv("JOURNAL_STREAM", raising=False)

    config = StoggerConfig(log_format="json")
    processors = build_shared_processors(config)
    # build_shared_processors for json omits SelectRenderedString — add it
    processors.append(SelectRenderedString(key="console"))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.BoundLogger,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=False,
    )

    log = structlog.get_logger()
    log.info("json-test", key="value")

    captured = capsys.readouterr()
    lines = [line for line in captured.err.strip().split("\n") if "json-test" in line]
    assert len(lines) >= 1
    data = json.loads(lines[-1])
    assert data["event"] == "json-test"
    assert data["key"] == "value"


@pytest.mark.integration
def test_real_file_logging(tmp_path, monkeypatch):
    """init_logging with logdir creates log file with expected content."""
    monkeypatch.delenv("JOURNAL_STREAM", raising=False)

    logdir = tmp_path / "logs"
    logdir.mkdir()

    init_logging(logdir=str(logdir), syslog_identifier="integration-test")

    log = structlog.get_logger()
    log.info("file-test-message", data="payload")

    log_file = logdir / "integration-test.log"
    assert log_file.exists()
    content = log_file.read_text()
    assert "file-test-message" in content
    assert "payload" in content


@pytest.mark.integration
def test_real_multi_logger_dispatch(tmp_path, capsys, monkeypatch):
    """Console and file loggers both receive the same message."""
    monkeypatch.delenv("JOURNAL_STREAM", raising=False)

    logdir = tmp_path / "logs"
    logdir.mkdir()

    init_logging(
        logdir=str(logdir),
        log_to_console=True,
        syslog_identifier="multi-test",
    )

    log = structlog.get_logger()
    log.info("multi-dispatch", key="both-targets")

    captured = capsys.readouterr()
    assert "multi-dispatch" in captured.err

    log_file = logdir / "multi-test.log"
    assert log_file.exists()
    assert "multi-dispatch" in log_file.read_text()


# --- E2E tests ---


@pytest.mark.e2e
def test_e2e_full_pipeline_with_config(tmp_path, capsys, monkeypatch):
    """Full pipeline: pyproject.toml → StoggerConfig → init_logging → structured output."""
    monkeypatch.delenv("JOURNAL_STREAM", raising=False)

    logdir = tmp_path / "logs"
    logdir.mkdir()

    # pyproject.toml config drives StoggerConfig
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.stogger]\nsyslog_identifier = "e2e-pipeline"\n',
    )
    monkeypatch.chdir(tmp_path)

    # Verify config loaded from pyproject.toml
    cfg = StoggerConfig()
    assert cfg.syslog_identifier == "e2e-pipeline"

    # Full pipeline: config → init_logging → structlog → console + file output
    init_logging(logdir=str(logdir), syslog_identifier=cfg.syslog_identifier)

    log = structlog.get_logger("e2e-app")
    log.info(
        "user-action",
        _replace_msg="User {user} performed {action}",
        user="alice",
        action="login",
    )

    captured = capsys.readouterr()
    assert "User alice performed login" in captured.err
    assert "user-action" in captured.err

    # Config from pyproject.toml flows through to the log file name
    log_file = logdir / "e2e-pipeline.log"
    assert log_file.exists()
    file_content = log_file.read_text()
    assert "user-action" in file_content
