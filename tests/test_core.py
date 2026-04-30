"""Tests for core logging functionality."""

import datetime
import io
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import structlog

# Import the modules we want to test
from stogger.config import SimpleFormatSettings
from stogger.core import (
    CmdOutputFileRenderer,
    ConsoleFileRenderer,
    JournalLoggerFactory,
    JSONRenderer,
    MultiOptimisticLogger,
    MultiOptimisticLoggerFactory,
    MultiRenderer,
    PartialFormatter,
    SelectRenderedString,
    SystemdJournalRenderer,
    TranslationProcessor,
    drop_cmd_output_logfile,
    init_command_logging,
    init_early_logging,
    init_logging,
    log_to_stdlib,
    logging_initialized,
    prefix,
    process_exc_info,
)


@pytest.fixture(autouse=True)
def _reset_structlog():
    """Reset structlog configuration after each test to avoid state leakage."""
    yield
    structlog.reset_defaults()


class TestConsoleFileRenderer:
    """Tests for the ConsoleFileRenderer class."""

    def test_caller_info_option(self):
        """Test the show_caller_info option."""
        settings = SimpleFormatSettings(show_code_info=True)
        renderer = ConsoleFileRenderer(settings=settings)
        assert renderer.settings.show_code_info is True

    def test_pad_event_width(self):
        """Test the pad_event_width option."""
        settings = SimpleFormatSettings(pad_event_width=20)
        renderer = ConsoleFileRenderer(settings=settings)
        result = renderer(
            None,
            "info",
            {
                "event": "short",
                "timestamp": "2023-01-01T00:00:00Z",
                "level": "info",
            },
        )

        assert "short" + " " * 15 in result["file"]

    def test_console_file_renderer_with_simple_format_settings(self):
        """Test ConsoleFileRenderer with SimpleFormatSettings."""
        settings = SimpleFormatSettings(
            min_level="debug",
            show_logger_brackets=False,
            show_pid=False,
            show_code_info=True,
            timestamp_format="iso_no_z",
        )
        renderer = ConsoleFileRenderer(settings=settings)

        result = renderer(
            None,
            "info",
            {
                "event": "test_event",
                "timestamp": "2023-01-01T00:00:00Z",
                "level": "info",
                "code_file": "test.py",
                "code_func": "test_func",
                "code_lineno": 42,
            },
        )

        assert "2023-01-01T00:00:00 " in result["console"]
        assert "2023-01-01T00:00:00Z" not in result["console"]

    def test_console_renderer_output(self):
        """Test the output of the ConsoleFileRenderer."""
        renderer = ConsoleFileRenderer(min_level="info")
        event_dict = {
            "event": "test-event",
            "level": "info",
            "timestamp": "2025-01-01T00:00:00Z",
            "some_key": "some_value",
        }
        result = renderer(None, "info", event_dict.copy())
        assert "test-event" in result["console"]
        assert "some_value" in result["console"]
        assert "\x1b" not in result["file"]  # No ANSI codes in file output

    def test_json_renderer_output(self):
        """Test the output of the JSONRenderer."""
        renderer = JSONRenderer()
        event_dict = {
            "event": "test-event",
            "level": "info",
            "timestamp": "2025-01-01T00:00:00Z",
            "some_key": "some_value",
        }
        result = renderer(None, "info", event_dict.copy())

        console_json = json.loads(result["console"])
        file_json = json.loads(result["file"])

        assert console_json["event"] == "test-event"
        assert console_json["some_key"] == "some_value"
        assert file_json["level"] == "info"


class TestCoreEdgeCases:
    """Tests for edge cases in core functionality."""

    def test_console_file_renderer_with_simple_format_settings(self):
        """Test ConsoleFileRenderer with SimpleFormatSettings."""
        settings = SimpleFormatSettings(
            min_level="debug",
            show_logger_brackets=False,
            show_pid=False,
            show_code_info=True,
            timestamp_format="iso_no_z",
        )
        renderer = ConsoleFileRenderer(settings=settings)

        result = renderer(
            None,
            "info",
            {
                "event": "test_event",
                "timestamp": "2023-01-01T00:00:00Z",
                "level": "info",
                "code_file": "test.py",
                "code_func": "test_func",
                "code_lineno": 42,
            },
        )

        assert "2023-01-01T00:00:00 " in result["console"]
        assert "2023-01-01T00:00:00Z" not in result["console"]

    def test_early_logging_initialization(self):
        """Test that early logging initialization reduces uninitialized structlog messages."""
        test_script = """
import stogger
import structlog

# This should show proper format from the start
log = structlog.get_logger('test')
log.info('early-message', message='Should show early format')

# Full initialization should work without issues
# stogger.init_logging()
log.info('after-full-init', message='Should show full format')
"""

        result = subprocess.run(
            [sys.executable, "-c", test_script],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0, f"Script failed: {result.stderr}"

        output = result.stdout + result.stderr
        assert output.strip(), "No logging output received"

        lines = output.strip().split("\n")
        assert len(lines) >= 2, f"Expected at least 2 log lines, got: {lines}"

        early_lines = [line for line in lines if "early-message" in line]
        assert len(early_lines) == 1, f"Expected exactly 1 early message, got: {early_lines}"

        early_line = early_lines[0]
        assert "Should show early format" in early_line
        assert "2026-" in early_line

        full_init_lines = [line for line in lines if "after-full-init" in line and "Should show full format" in line]
        assert len(full_init_lines) == 1, f"Expected exactly 1 full init message, got: {full_init_lines}"

        full_init_line = full_init_lines[0]
        assert "Should show full format" in full_init_line

    def test_early_logging_graceful_fallback(self):
        """Test that early logging fails gracefully if there are issues."""
        test_script = """
import stogger
import structlog

# Should be configured after import
print("Configured:", stogger.logging_initialized())

# Should still work after full init
stogger.init_logging()
print("Still configured:", stogger.logging_initialized())
"""

        result = subprocess.run(
            [sys.executable, "-c", test_script],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")

        assert "Configured:" in lines[0]
        assert "Still configured:" in lines[-1]


# --- Batch 4: Extracted Private Methods ---


class TestResolveLevelName:
    """Tests for ConsoleFileRenderer._resolve_level_name."""

    def test_resolve_level_name_string(self):
        """String method_name is lowercased."""
        renderer = ConsoleFileRenderer()
        result = renderer._resolve_level_name("INFO", {})
        assert result == "info"

    def test_resolve_level_name_fallback(self):
        """Non-string method_name falls back to event_dict['level']."""
        renderer = ConsoleFileRenderer()
        result = renderer._resolve_level_name(None, {"level": "WARNING"})
        assert result == "warning"

    def test_resolve_level_name_none(self):
        """Non-string method_name with no level in event_dict returns None."""
        renderer = ConsoleFileRenderer()
        result = renderer._resolve_level_name(None, {})
        assert result is None


class TestShouldDropByLevel:
    """Tests for ConsoleFileRenderer._should_drop_by_level."""

    def test_should_drop_by_level_none(self):
        """None level_name returns False (never drop)."""
        renderer = ConsoleFileRenderer()
        assert renderer._should_drop_by_level(None, {}) is False

    def test_should_drop_by_level_unknown(self):
        """Unknown level name (ValueError) returns False."""
        renderer = ConsoleFileRenderer()
        assert renderer._should_drop_by_level("unknown_level", {}) is False

    def test_should_drop_by_level_above_min(self):
        """Level above min_level returns True (should drop)."""
        renderer = ConsoleFileRenderer(min_level="info")
        assert renderer._should_drop_by_level("debug", {}) is True

    def test_should_drop_by_level_below_min(self):
        """Level at or below min_level returns False (keep)."""
        renderer = ConsoleFileRenderer(min_level="info")
        assert renderer._should_drop_by_level("info", {}) is False


class TestFormatTimestamp:
    """Tests for ConsoleFileRenderer._format_timestamp."""

    def test_format_timestamp_none(self):
        """ts=None returns 'notimestamp'."""
        renderer = ConsoleFileRenderer()
        result = renderer._format_timestamp(None, {})
        assert "notimestamp" in result


class TestRenderOutputSections:
    """Tests for ConsoleFileRenderer._render_output_sections."""

    def test_render_output_sections_all_types(self):
        """All output section types are rendered correctly."""
        renderer = ConsoleFileRenderer()
        buf = io.StringIO()

        event_dict = {
            "cmd_output_line": "cmd> ls -la",
            "_output": "program output",
            "stdout": "standard out",
            "stderr": "standard error",
            "stack": "stack trace here",
            "exception_traceback": "traceback details",
        }
        renderer._render_output_sections(event_dict, buf.write)
        output = buf.getvalue()

        assert "cmd> ls -la" in output
        assert "program output" in output
        assert "out" in output
        assert "standard out" in output
        assert "err" in output
        assert "standard error" in output
        assert "stack" in output
        assert "stack trace here" in output
        assert "exception" in output
        assert "traceback details" in output
        assert "=" * 79 in output  # separator between stack and traceback


# --- Batch 5: Remaining Functions ---


class TestPartialFormatter:
    """Tests for PartialFormatter get_field and format_field."""

    def test_get_field_missing_key(self):
        """KeyError/AttributeError in get_field returns (None, field_name)."""
        fmt = PartialFormatter()
        result = fmt.get_field("nonexistent", [], {})
        assert result == (None, "nonexistent")

    def test_get_field_present(self):
        """Normal field lookup returns (value, rest)."""
        fmt = PartialFormatter()
        result = fmt.get_field("name", [], {"name": "Alice"})
        assert result[0] == "Alice"

    def test_format_field_none(self):
        """value=None returns '<missing>'."""
        fmt = PartialFormatter()
        assert fmt.format_field(None, "") == "<missing>"

    def test_format_field_bad_format(self):
        """ValueError in format_field returns '<bad format>'."""
        fmt = PartialFormatter()
        result = fmt.format_field(42, "z")
        assert result == "<bad format>"


class TestTranslationProcessor:
    """Tests for TranslationProcessor."""

    def test_translation_processor_template_hit(self):
        """Translations dict has key -> _translated_msg set."""
        proc = TranslationProcessor({"greeting": "Hello {name}!"})
        event_dict = {"event": "greeting", "name": "World"}
        result = proc(None, "info", event_dict)
        assert result["_translated_msg"] == "Hello World!"
        assert result["_original_event"] == "greeting"

    def test_translation_processor_replace_msg(self):
        """No template match, _replace_msg present -> _translated_msg set."""
        proc = TranslationProcessor({})
        event_dict = {"event": "something", "_replace_msg": "Value: {val}", "val": 42}
        result = proc(None, "info", event_dict)
        assert result["_translated_msg"] == "Value: 42"

    def test_translation_processor_no_match(self):
        """No template, no _replace_msg -> event_dict unchanged (no _translated_msg)."""
        proc = TranslationProcessor({})
        event_dict = {"event": "something"}
        result = proc(None, "info", event_dict)
        assert "_translated_msg" not in result


class TestPrefix:
    """Tests for prefix function."""

    def test_prefix_empty_string(self):
        """prefix('x', '') returns ''."""
        assert prefix("x", "") == ""

    def test_prefix_normal(self):
        """Prefix with content adds prefix to each line."""
        result = prefix("tag", "line1\nline2")
        assert "tag: line1" in result
        assert "tag: line2" in result


class TestProcessExcInfo:
    """Tests for process_exc_info."""

    def test_process_exc_info_base_exception(self):
        """exc_info is BaseException -> converts to tuple."""
        exc = ValueError("test error")
        event_dict = {"exc_info": exc}
        result = process_exc_info(None, "error", event_dict)
        assert isinstance(result["exc_info"], tuple)
        assert result["exc_info"][0] is ValueError
        assert result["exc_info"][1] is exc

    def test_process_exc_info_non_tuple(self):
        """exc_info is neither BaseException nor tuple -> calls sys.exc_info()."""
        with patch("stogger.core.sys.exc_info", return_value=(TypeError, TypeError("x"), None)):
            event_dict = {"exc_info": "not_an_exception"}
            result = process_exc_info(None, "error", event_dict)
            assert isinstance(result["exc_info"], tuple)
            assert result["exc_info"][0] is TypeError

    def test_process_exc_info_none(self):
        """No exc_info -> event_dict unchanged."""
        event_dict = {"event": "test"}
        result = process_exc_info(None, "info", event_dict)
        assert "exc_info" not in result


class TestSelectRenderedString:
    """Tests for SelectRenderedString processor."""

    def test_select_rendered_string_passthrough(self):
        """String input -> returned as-is."""
        proc = SelectRenderedString()
        assert proc(None, "info", "already a string") == "already a string"

    def test_select_rendered_string_dict(self):
        """Dict with key -> returns value."""
        proc = SelectRenderedString(key="console")
        result = proc(None, "info", {"console": "output", "file": "log"})
        assert result == "output"

    def test_select_rendered_string_fallback(self):
        """Dict without key -> returns str()."""
        proc = SelectRenderedString(key="missing")
        result = proc(None, "info", {"console": "output"})
        assert result == "{'console': 'output'}"


class TestJSONRendererDropEvent:
    """Tests for JSONRenderer level filtering."""

    def test_json_renderer_drop_event(self):
        """Level above min_level raises structlog.DropEvent."""
        renderer = JSONRenderer(min_level="info")
        event_dict = {"event": "debug-msg", "level": "debug"}
        with pytest.raises(structlog.DropEvent):
            renderer(None, "debug", event_dict)


class TestConsoleFileRendererConsoleIgnore:
    """Tests for console_ignore setting."""

    def test_console_file_renderer_console_ignore(self):
        """_log_settings with console_ignore=True returns None."""
        renderer = ConsoleFileRenderer()
        event_dict = {
            "event": "test",
            "level": "info",
            "_log_settings": {"console_ignore": True},
        }
        result = renderer(None, "info", event_dict)
        assert result is None


class TestConsoleRendererShowPid:
    """Tests for show_pid in ConsoleFileRenderer."""

    def test_console_renderer_show_pid(self):
        """show_pid=True, pid in event -> output contains pid."""
        settings = SimpleFormatSettings(show_pid=True)
        renderer = ConsoleFileRenderer(settings=settings)
        event_dict = {
            "event": "test",
            "level": "info",
            "timestamp": "2025-01-01T00:00:00Z",
            "pid": 12345,
        }
        result = renderer(None, "info", event_dict)
        assert "12345" in result["console"]


class TestConsoleRendererShowLoggerBrackets:
    """Tests for show_logger_brackets in ConsoleFileRenderer."""

    def test_console_renderer_show_logger_brackets(self):
        """show_logger_brackets=True, logger name -> brackets in output."""
        settings = SimpleFormatSettings(show_logger_brackets=True)
        renderer = ConsoleFileRenderer(settings=settings)
        event_dict = {
            "event": "test",
            "level": "info",
            "timestamp": "2025-01-01T00:00:00Z",
            "logger": "mymodule",
        }
        result = renderer(None, "info", event_dict)
        assert "[mymodule]" in result["console"]


class TestLogToStdlib:
    """Tests for log_to_stdlib processor."""

    def test_log_to_stdlib(self):
        """Call with event dict -> logging.log called with correct level."""
        with patch("stogger.core.logging.log") as mock_log:
            event_dict = {
                "event": "test message",
                "level": "warning",
            }
            result = log_to_stdlib(None, "warning", event_dict)
            mock_log.assert_called_once_with(logging.WARNING, "test message")
            assert result is event_dict

    def test_log_to_stdlib_with_exc_info(self):
        """Call with exc_info -> logging.log called with exc_info kwarg."""
        with patch("stogger.core.logging.log") as mock_log:
            exc = ValueError("boom")
            event_dict = {
                "event": "error msg",
                "level": "error",
                "exc_info": (type(exc), exc, None),
            }
            log_to_stdlib(None, "error", event_dict)
            mock_log.assert_called_once()
            call_kwargs = mock_log.call_args
            assert call_kwargs[1].get("exc_info") is not None or len(call_kwargs[0]) > 1

    def test_log_to_stdlib_default_level(self):
        """Missing level defaults to INFO."""
        with patch("stogger.core.logging.log") as mock_log:
            event_dict = {"event": "default"}
            log_to_stdlib(None, "info", event_dict)
            mock_log.assert_called_once_with(logging.INFO, "default")


class TestInitEarlyLogging:
    """Tests for init_early_logging."""

    def test_init_early_logging_fresh(self):
        """Calling init_early_logging configures structlog."""
        init_early_logging()
        assert structlog.is_configured()

    def test_init_early_logging_already_configured(self):
        """Calling when already configured is a no-op."""
        init_early_logging()
        first_config = structlog.get_config()
        init_early_logging()
        second_config = structlog.get_config()
        assert first_config == second_config


class TestLoggingInitialized:
    """Tests for logging_initialized."""

    def test_logging_initialized(self):
        """Returns True after init_logging."""
        with patch("os.environ", {**os.environ}):
            os.environ.pop("JOURNAL_STREAM", None)
            init_logging(logdir=None)
        assert logging_initialized() is True

    def test_logging_not_initialized(self):
        """Returns False when structlog is not configured."""
        assert not structlog.is_configured()
        assert logging_initialized() is False


class TestJournalLoggerFactory:
    """Tests for JournalLoggerFactory."""

    def test_journal_logger_factory(self):
        """JournalLoggerFactory()() returns None."""
        factory = JournalLoggerFactory()
        assert factory() is None


class TestSystemdJournalRenderer:
    """Tests for SystemdJournalRenderer."""

    def test_trace_returns_empty(self):
        """method_name='trace' -> returns {}."""
        renderer = SystemdJournalRenderer("test-id")
        result = renderer(None, "trace", {"event": "msg"})
        assert result == {}

    def test_replace_msg_path(self):
        """_replace_msg present -> message extended with formatted msg."""
        renderer = SystemdJournalRenderer("test-id")
        event_dict = {
            "event": "base",
            "_replace_msg": "detail: {key}",
            "key": "val",
            "level": "info",
        }
        result = renderer(None, "info", event_dict)
        assert "journal" in result
        journal = result["journal"]
        assert "detail: val" in journal["MESSAGE"]

    def test_handle_json_fallback_with_structlog(self):
        """Object with __structlog__ -> uses it."""
        renderer = SystemdJournalRenderer("test-id")

        class StructlogObj:
            def __structlog__(self):
                return "serialized"

        result = renderer.handle_json_fallback(StructlogObj())
        assert result == "serialized"

    def test_handle_json_fallback_without_structlog(self):
        """Object without __structlog__ -> repr()."""
        renderer = SystemdJournalRenderer("test-id")
        result = renderer.handle_json_fallback(42)
        assert result == "42"

    def test_dump_datetime(self):
        """Datetime value -> isoformat."""
        renderer = SystemdJournalRenderer("test-id")
        dt = datetime.datetime(2025, 1, 15, 12, 30, 45, tzinfo=datetime.UTC)
        result = renderer.dump_for_journal(dt)
        assert result == dt.isoformat()

    def test_dump_string_passthrough(self):
        """String values pass through unchanged."""
        renderer = SystemdJournalRenderer("test-id")
        assert renderer.dump_for_journal("hello") == "hello"

    def test_kv_rendering_branch(self):
        """Non-replace-msg path with extra kv data -> message extended with kv."""
        renderer = SystemdJournalRenderer("test-id")
        event_dict = {
            "event": "test-event",
            "level": "info",
            "extra_key": "extra_val",
        }
        result = renderer(None, "info", event_dict)
        assert "journal" in result
        journal = result["journal"]
        # kv renderer should include the extra key
        assert "extra_key" in journal["MESSAGE"] or "extra_val" in journal["MESSAGE"]


class TestCmdOutputFileRenderer:
    """Tests for CmdOutputFileRenderer."""

    def test_with_cmd_output_line(self):
        """cmd_output_line present -> returns {'cmd_output_file': line}."""
        renderer = CmdOutputFileRenderer()
        event_dict = {"event": "test", "cmd_output_line": "output line here"}
        result = renderer(None, "info", event_dict)
        assert result == {"cmd_output_file": "output line here"}

    def test_without_cmd_output_line(self):
        """No cmd_output_line -> returns {}."""
        renderer = CmdOutputFileRenderer()
        event_dict = {"event": "test"}
        result = renderer(None, "info", event_dict)
        assert result == {}


class TestMultiRenderer:
    """Tests for MultiRenderer."""

    def test_multi_renderer_exception(self):
        """Renderer that raises -> exception caught, partial results returned."""
        _err_msg = "boom"

        def bad_renderer(_logger, _method, _event_dict):
            raise RuntimeError(_err_msg)

        def good_renderer(_logger, _method, _event_dict):
            return {"good": "output"}

        mr = MultiRenderer(bad=bad_renderer, good=good_renderer)
        with patch("stogger.core.logging.getLogger") as mock_get_logger:
            mock_get_logger.return_value.exception = MagicMock()
            result = mr(None, "info", {"event": "test"})

        assert result == {"good": "output"}


class TestMultiOptimisticLogger:
    """Tests for MultiOptimisticLogger."""

    def test_msg_with_truthy_line(self):
        """Msg with truthy line -> logger.msg called."""
        mock_logger = MagicMock()
        mol = MultiOptimisticLogger({"target": mock_logger})
        mol.msg(target="hello world")
        mock_logger.msg.assert_called_once_with("hello world")

    def test_msg_exception(self):
        """Logger that raises -> exception caught."""
        failing_logger = MagicMock()
        failing_logger.msg.side_effect = RuntimeError("write failed")
        mol = MultiOptimisticLogger({"target": failing_logger})
        with patch("stogger.core.logging.getLogger") as mock_get_logger:
            mock_get_logger.return_value.exception = MagicMock()
            mol.msg(target="hello")
        # Should not raise

    def test_msg_empty_line(self):
        """Msg with empty/missing line -> logger not called."""
        mock_logger = MagicMock()
        mol = MultiOptimisticLogger({"target": mock_logger})
        mol.msg(target="")
        mock_logger.msg.assert_not_called()


class TestInitCommandLogging:
    """Tests for init_command_logging."""

    def test_init_command_logging(self, tmp_path):
        """Creates cmd_output_file factory in multi-logger."""
        # Set up structlog with MultiOptimisticLoggerFactory
        factories = {}
        factory = MultiOptimisticLoggerFactory({"logdir": tmp_path}, factories)
        structlog.configure(
            processors=[],
            wrapper_class=structlog.BoundLogger,
            logger_factory=factory,
        )
        log = structlog.get_logger()
        init_command_logging(log, tmp_path)

        assert "cmd_output_file" in factories
        # Clean up file handle
        factories["cmd_output_file"]._file.close()  # noqa: SLF001, RUF100

    def test_init_command_logging_no_logdir(self):
        """No logdir and no context logdir -> logs warning and returns."""
        factory = MultiOptimisticLoggerFactory({}, {})
        structlog.configure(
            processors=[],
            wrapper_class=structlog.BoundLogger,
            logger_factory=factory,
        )
        log = structlog.get_logger()
        # Should not raise
        init_command_logging(log)


class TestDropCmdOutputLogfile:
    """Tests for drop_cmd_output_logfile."""

    def test_drop_cmd_output_logfile(self, tmp_path):
        """After setup -> file closed and deleted."""
        cmd_file = tmp_path / "build-output.log"
        cmd_file_handle = cmd_file.open("w")
        factories = {"cmd_output_file": structlog.PrintLoggerFactory(cmd_file_handle)}
        factory = MultiOptimisticLoggerFactory({"logdir": tmp_path}, factories)
        structlog.configure(
            processors=[],
            wrapper_class=structlog.BoundLogger,
            logger_factory=factory,
        )
        log = structlog.get_logger()

        assert cmd_file.exists()
        drop_cmd_output_logfile(log)
        assert not cmd_file.exists()

    def test_drop_missing_factory(self):
        """KeyError when cmd_output_file not in factories."""
        factory = MultiOptimisticLoggerFactory({}, {})
        structlog.configure(
            processors=[],
            wrapper_class=structlog.BoundLogger,
            logger_factory=factory,
        )
        log = structlog.get_logger()
        with pytest.raises(KeyError):
            drop_cmd_output_logfile(log)
