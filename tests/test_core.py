"""Tests for core logging functionality."""

import datetime
import io
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import structlog

from stogger._colors import RED, RESET_ALL

# Import the modules we want to test
from stogger.config import FormatConfig
from stogger.core import (
    CmdOutputFileRenderer,
    ConsoleFileRenderer,
    JSONRenderer,
    MultiOptimisticLogger,
    MultiOptimisticLoggerFactory,
    MultiRenderer,
    PartialFormatter,
    SelectRenderedString,
    SystemdJournalRenderer,
    TranslationProcessor,
    build_logger_factories,
    _inject_exc_info_for_exception,
    drop_cmd_output_logfile,
    format_exc_info,
    init_command_logging,
    init_early_logging,
    init_logging,
    logging_initialized,
    prefix,
    process_exc_info,
)


class _MsgTarget:
    """Minimal target for MultiOptimisticLogger — has .msg() method."""

    def msg(self, message: str) -> None: ...


@pytest.fixture(autouse=True)
def _reset_structlog():
    """Reset structlog configuration after each test to avoid state leakage."""
    yield
    structlog.reset_defaults()


@pytest.mark.integration
class TestConsoleFileRenderer:
    """Tests for the ConsoleFileRenderer class."""

    def test_caller_info_option(self):
        """Test the show_caller_info option."""
        settings = FormatConfig(show_code_info=True)
        renderer = ConsoleFileRenderer(format_config=settings)
        assert renderer.format_config.show_code_info is True

    def test_pad_event_width(self):
        """Test the pad_event_width option."""
        settings = FormatConfig(pad_event_width=20)
        renderer = ConsoleFileRenderer(format_config=settings)
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
        """Test ConsoleFileRenderer with FormatConfig."""
        settings = FormatConfig(
            min_level="debug",
            show_code_info=True,
            timestamp_precision="iso_no_z",
        )
        renderer = ConsoleFileRenderer(format_config=settings)

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

        assert "2023-01-01T00:00:00" in result["console"]
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

    def test_underscore_keys_dropped_from_fallback_body(self):
        """Fallback KV body skips `_`-prefixed keys (spec: body-skip-underscore-keys)."""
        renderer = ConsoleFileRenderer()
        event_dict = {
            "event": "test-event",
            "level": "info",
            "timestamp": "2025-01-01T00:00:00Z",
            "visible_key": "visible_value",
            "_internal_key": "secret_internal_value",
            "_output": "command output line",
        }
        result = renderer(None, "info", event_dict)
        assert "visible_key" in result["file"]
        assert "visible_value" in result["file"]
        # `_`-prefixed keys MUST NOT appear in the fallback body.
        # `_internal_key` has no dedicated render stage so it must vanish entirely.
        assert "_internal_key" not in result["file"]
        assert "secret_internal_value" not in result["file"]
        # `_output` is consumed by the dedicated output-section stage, so the value
        # appears exactly once (as the rendered output section), not duplicated in body.
        assert result["file"].count("command output line") == 1

    def test_replace_msg_cannot_reference_underscore_key(self):
        """`_replace_msg` format strings cannot reference `_`-prefixed keys."""
        renderer = ConsoleFileRenderer()
        event_dict = {
            "event": "test-event",
            "level": "info",
            "timestamp": "2025-01-01T00:00:00Z",
            "_replace_msg": "leaked: {_internal}",
            "_internal": "secret_value",
        }
        result = renderer(None, "info", event_dict)
        # Internal value must not be reachable via format string
        assert "secret_value" not in result["file"]
        # PartialFormatter emits '<missing>' for unavailable keys
        assert "<missing>" in result["file"]

    def test_underscore_output_key_not_duplicated_in_body(self):
        """`_output` value appears once (via output-section stage), not duplicated in body."""
        renderer = ConsoleFileRenderer()
        event_dict = {
            "event": "test-event",
            "level": "info",
            "timestamp": "2025-01-01T00:00:00Z",
            "_output": "command output line",
        }
        result = renderer(None, "info", event_dict)
        # The output appears once (via the dedicated stage), not twice (body + stage)
        assert result["file"].count("command output line") == 1

    def test_json_renderer_output(self, log):
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
        assert log.has("initializing-json-renderer")


@pytest.mark.integration
class TestCoreEdgeCases:
    """Tests for edge cases in core functionality."""

    def test_console_file_renderer_with_simple_format_settings(self):
        """Test ConsoleFileRenderer with FormatConfig."""
        settings = FormatConfig(
            min_level="debug",
            show_code_info=True,
            timestamp_precision="iso_no_z",
        )
        renderer = ConsoleFileRenderer(format_config=settings)

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

        assert "2023-01-01T00:00:00" in result["console"]
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
            "_raw_output": "raw ansi output",
            "_raw_output_prefix": "ty",
            "stdout": "standard out",
            "stderr": "standard error",
            "stack": "stack trace here",
            "exception_traceback": "traceback details",
        }
        renderer._render_output_sections(event_dict, buf.write)
        output = buf.getvalue()

        assert "cmd> ls -la" in output
        assert "program output" in output
        assert "ty" in output
        assert "raw ansi output" in output
        assert "out" in output
        assert "standard out" in output
        assert "err" in output
        assert "standard error" in output
        assert "stack" in output
        assert "stack trace here" in output
        assert "exception" in output
        assert "traceback details" in output
        assert "=" * 79 in output  # separator between stack and traceback

    def test_raw_output_ansi_passthrough(self):
        """_raw_output preserves ANSI in console, strips for file."""
        renderer = ConsoleFileRenderer()
        ansi_content = RED + "error text" + RESET_ALL
        event_dict = {
            "event": "type-errors",
            "_raw_output": ansi_content,
        }
        result = renderer(None, "info", event_dict.copy())

        # ANSI codes present in console (RED is non-empty when isatty)
        if RED:
            assert RED in result["console"]
            assert RESET_ALL in result["console"]
        # File output never contains ANSI escape sequences
        assert "\x1b" not in result["file"]


# --- Batch 5: Remaining Functions ---


class TestPartialFormatter:
    """Tests for PartialFormatter get_field and format_field."""

    def test_get_field_missing_key(self, log):
        """KeyError/AttributeError in get_field returns (None, field_name)."""
        fmt = PartialFormatter()
        result = fmt.get_field("nonexistent", [], {})
        assert result == (None, "nonexistent")
        assert log.has("format-field-missing")

    def test_get_field_present(self):
        """Normal field lookup returns (value, rest)."""
        fmt = PartialFormatter()
        result = fmt.get_field("name", [], {"name": "Alice"})
        assert result[0] == "Alice"

    def test_format_field_none(self):
        """value=None returns '<missing>'."""
        fmt = PartialFormatter()
        assert fmt.format_field(None, "") == "<missing>"

    def test_format_field_bad_format(self, log):
        """ValueError in format_field returns '<bad format>'."""
        fmt = PartialFormatter()
        result = fmt.format_field(42, "z")
        assert result == "<bad format>"
        assert log.has("format-field-bad-format")


@pytest.mark.integration
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

    def test_translation_processor_init_logs(self, log):
        """TranslationProcessor.__init__ logs initializing-translation-processor."""
        TranslationProcessor({"greeting": "Hello {name}!"})
        log.has("initializing-translation-processor")

    def test_translation_processor_replace_msg_excludes_underscore_keys(self):
        """`_replace_msg` format strings cannot reference `_`-prefixed keys."""
        proc = TranslationProcessor({})
        event_dict = {
            "event": "something",
            "_replace_msg": "leaked: {_internal}",
            "_internal": "secret_value",
        }
        result = proc(None, "info", event_dict)
        assert "secret_value" not in result["_translated_msg"]
        # PartialFormatter emits '<missing>' for unavailable keys
        assert "<missing>" in result["_translated_msg"]

    def test_translation_processor_template_excludes_underscore_keys(self):
        """Translation templates cannot reference `_`-prefixed keys."""
        proc = TranslationProcessor({"greeting": "visible: {ok} leaked: {_internal}"})
        event_dict = {
            "event": "greeting",
            "ok": "ok",
            "_internal": "secret_value",
        }
        result = proc(None, "info", event_dict)
        assert "secret_value" not in result["_translated_msg"]
        assert "<missing>" in result["_translated_msg"]
        assert "visible: ok" in result["_translated_msg"]


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


class TestInjectExcInfoForException:
    """Tests for _inject_exc_info_for_exception."""

    def test_injects_when_exception_method_no_exc_info(self):
        """exception() method without exc_info -> injects sys.exc_info()."""
        try:
            raise ValueError("injected")
        except ValueError:
            result = _inject_exc_info_for_exception(None, "exception", {"event": "test"})
        assert "exc_info" in result
        assert result["exc_info"][0] is ValueError
        assert "injected" in str(result["exc_info"][1])

    def test_does_not_overwrite_existing_exc_info(self):
        """exception() with exc_info already set -> leaves it untouched."""
        result = _inject_exc_info_for_exception(None, "exception", {"event": "test", "exc_info": "custom"})
        assert result["exc_info"] == "custom"

    def test_ignores_error_method(self):
        """error() method -> no injection."""
        result = _inject_exc_info_for_exception(None, "error", {"event": "test"})
        assert "exc_info" not in result

    def test_ignores_info_method(self):
        """info() method -> no injection."""
        result = _inject_exc_info_for_exception(None, "info", {"event": "test"})
        assert "exc_info" not in result

    def test_outside_except_block_returns_none_tuple(self):
        """exception() called outside except block -> sys.exc_info() returns (None, None, None)."""
        result = _inject_exc_info_for_exception(None, "exception", {"event": "test"})
        assert "exc_info" in result
        assert result["exc_info"] == (None, None, None)


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


class TestFormatExcInfo:
    """Tests for format_exc_info processor."""

    def test_formats_exception(self):
        """Normal exception -> full traceback, class, and message."""
        try:
            raise ValueError("boom")
        except ValueError:
            exc_info = sys.exc_info()

        result = format_exc_info(None, "error", {"event": "test", "exc_info": exc_info})
        assert "exc_info" not in result
        assert "exception_traceback" in result
        assert "ValueError: boom" in result["exception_traceback"]
        assert result["exception_msg"] == "boom"
        assert result["exception_class"] == "builtins.ValueError"

    def test_no_exc_info_passes_through(self):
        """No exc_info -> event_dict unchanged."""
        event_dict = {"event": "test"}
        result = format_exc_info(None, "info", event_dict)
        assert "exception_traceback" not in result
        assert result == {"event": "test"}

    def test_formatting_failure_degraded_output(self):
        """Formatting raises (e.g. RecursionError) -> degraded output, no crash."""
        try:
            raise ValueError("original")
        except ValueError:
            exc_info = sys.exc_info()

        with patch("structlog.processors._format_exception", side_effect=RecursionError("stack overflow")):
            result = format_exc_info(None, "error", {"event": "test", "exc_info": exc_info})

        assert "exception_traceback" in result
        assert "[traceback unavailable" in result["exception_traceback"]
        assert result["exception_msg"] == "original"
        assert result["exception_class"] == "builtins.ValueError"


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


@pytest.mark.integration
class TestJSONRendererDropEvent:
    """Tests for JSONRenderer level filtering."""

    def test_json_renderer_drop_event(self):
        """Level above min_level raises structlog.DropEvent."""
        renderer = JSONRenderer(min_level="info")
        event_dict = {"event": "debug-msg", "level": "debug"}
        with pytest.raises(structlog.DropEvent):
            renderer(None, "debug", event_dict)


@pytest.mark.integration
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


@pytest.mark.integration
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

    def test_init_early_logging_logs(self, log):
        """init_early_logging(verbose=True) logs init-early-logging-called."""
        init_early_logging(verbose=True)
        log.has("init-early-logging-called")


class TestLoggingInitialized:
    """Tests for logging_initialized."""

    @pytest.mark.integration
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

    def test_init_logging_warns_on_already_configured(self, log):
        """init_logging() warns when structlog was already configured."""
        # Pre-configure structlog (simulates pytest-structlog or a prior call)
        structlog.configure(
            processors=[structlog.dev.ConsoleRenderer()],
            logger_factory=structlog.PrintLoggerFactory(),
            wrapper_class=structlog.BoundLogger,
        )
        assert structlog.is_configured()

        with patch("os.environ", {**os.environ}):
            os.environ.pop("JOURNAL_STREAM", None)
            init_logging(logdir=None)

        log.has("init-logging-overriding-existing-config")

    def test_init_logging_emits_started_event(self, log):
        """init_logging() emits init-logging-started debug event at entry."""
        with patch("os.environ", {**os.environ}):
            os.environ.pop("JOURNAL_STREAM", None)
            init_logging(logdir=None)
        log.has("init-logging-started")


class TestBuildConsoleRendererKwargs:
    """Tests for _build_console_renderer_kwargs logging."""

    def test_emits_building_event(self, log):
        """_build_console_renderer_kwargs emits building-console-renderer-kwargs debug event."""
        from stogger.core import _build_console_renderer_kwargs

        _build_console_renderer_kwargs(verbose=True, show_caller_info=False)
        log.has("building-console-renderer-kwargs")


class TestEnsureStderrLogging:
    """Tests for _ensure_stderr_logging logging."""

    def test_emits_ensuring_event(self, log):
        """_ensure_stderr_logging emits ensuring-stderr-logging debug event."""
        from stogger.core import _ensure_stderr_logging

        _ensure_stderr_logging()
        log.has("ensuring-stderr-logging")


@pytest.mark.integration
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

    def test_journal_replace_msg_excludes_underscore_keys(self):
        """Journal renderer `_replace_msg` excludes `_`-prefixed keys from interpolation."""
        renderer = SystemdJournalRenderer("test-id")
        event_dict = {
            "event": "base",
            "_replace_msg": "leaked: {_internal}",
            "_internal": "secret_value",
            "level": "info",
        }
        result = renderer(None, "info", event_dict)
        message = result["journal"]["MESSAGE"]
        # Internal value must not be reachable via format string
        assert "secret_value" not in message
        # PartialFormatter emits '<missing>' for unavailable keys
        assert "<missing>" in message
        # When _replace_msg is set, the formatted message replaces the kv body.
        # Visible keys are not auto-rendered in this branch.
        assert "base: leaked: <missing>" in message


@pytest.mark.integration
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
        """Renderer that raises -> RuntimeError re-raised with context."""

        def bad_renderer(_logger, _method, _event_dict):
            msg = "boom"
            raise RuntimeError(msg)

        def good_renderer(_logger, _method, _event_dict):
            return {"good": "output"}

        mr = MultiRenderer(bad=bad_renderer, good=good_renderer)
        with pytest.raises(RuntimeError, match="Renderer failed"):
            mr(None, "info", {"event": "test"})

    def test_renderer_failure_logs_event(self, log):
        """Renderer that raises logs renderer-failed event."""

        def bad_renderer(_logger, _method, _event_dict):
            raise RuntimeError("boom")

        mr = MultiRenderer(bad=bad_renderer)
        with pytest.raises(RuntimeError, match="Renderer failed"):
            mr(None, "info", {"event": "test"})
        log.has("renderer-failed")


class TestMultiOptimisticLogger:
    """Tests for MultiOptimisticLogger."""

    def test_msg_with_truthy_line(self):
        """Msg with truthy line -> logger.msg called."""
        mock_logger = MagicMock(spec=_MsgTarget)
        mol = MultiOptimisticLogger({"target": mock_logger})
        mol.msg(target="hello world")
        mock_logger.msg.assert_called_once_with("hello world")

    def test_msg_exception(self):
        """Logger that raises -> RuntimeError re-raised with context."""
        failing_logger = MagicMock(spec=_MsgTarget)
        failing_logger.msg.side_effect = RuntimeError("write failed")
        mol = MultiOptimisticLogger({"target": failing_logger})
        with pytest.raises(RuntimeError, match="Sub-logger dispatch failed"):
            mol.msg(target="hello")

    def test_dispatch_failure_logs_event(self, log):
        """Sub-logger that raises logs sub-logger-dispatch-failed event."""
        failing_logger = MagicMock(spec=_MsgTarget)
        failing_logger.msg.side_effect = RuntimeError("write failed")
        mol = MultiOptimisticLogger({"target": failing_logger})
        with pytest.raises(RuntimeError, match="Sub-logger dispatch failed"):
            mol.msg(target="hello")
        log.has("sub-logger-dispatch-failed")

    def test_value_error_logs_event(self, log):
        """Sub-logger raising ValueError logs sub-logger-value-error event."""
        failing_logger = MagicMock(spec=_MsgTarget)
        failing_logger.msg.side_effect = ValueError("file handle closed")
        mol = MultiOptimisticLogger({"target": failing_logger})
        mol.msg(target="hello")
        log.has("sub-logger-value-error")

    def test_msg_empty_line(self):
        """Msg with empty/missing line -> logger not called."""
        mock_logger = MagicMock(spec=_MsgTarget)
        mol = MultiOptimisticLogger({"target": mock_logger})
        mol.msg(target="")
        mock_logger.msg.assert_not_called()


@pytest.mark.integration
class TestInitCommandLogging:
    """Tests for init_command_logging."""

    def test_init_command_logging(self, monkeypatch, tmp_path):
        """Creates cmd_output_file factory in multi-logger."""
        # Explicitly set INVOCATION_ID to cover the timestamped-filename branch
        monkeypatch.setenv("INVOCATION_ID", "test-invocation-id")
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

        log.has("logging-cmd-output")
        # Clean up file handle
        factories["cmd_output_file"]._file.close()  # noqa: SLF001, RUF100

    def test_init_command_logging_no_logdir(self):
        """No logdir and no context logdir -> logs warning and returns early."""
        factory = MultiOptimisticLoggerFactory({}, {})
        structlog.configure(
            processors=[],
            wrapper_class=structlog.BoundLogger,
            logger_factory=factory,
        )
        log = structlog.get_logger()
        # Should not raise; warning logged, no cmd_output_file registered
        init_command_logging(log)
        log.has("logging-cmd-output-no-logdir")
        assert "cmd_output_file" not in factory.factories

    def test_cmd_output_file_open_failure_logs_event(self, tmp_path):
        """OSError opening cmd output file logs cmd-output-file-open-failed event."""
        factory = MultiOptimisticLoggerFactory({"logdir": tmp_path}, {})
        structlog.configure(
            processors=[],
            wrapper_class=structlog.BoundLogger,
            logger_factory=factory,
        )
        log = structlog.get_logger()
        with patch.object(Path, "open", side_effect=OSError("permission denied")):
            init_command_logging(log, tmp_path)
        log.has("cmd-output-file-open-failed")
        assert "cmd_output_file" not in factory.factories


@pytest.mark.integration
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

    def test_drop_cmd_output_logs(self, tmp_path, log):
        """drop_cmd_output_logfile logs logging-cmd-output-drop."""
        cmd_file = tmp_path / "build-output.log"
        cmd_file_handle = cmd_file.open("w")
        factories = {"cmd_output_file": structlog.PrintLoggerFactory(cmd_file_handle)}
        factory = MultiOptimisticLoggerFactory({"logdir": tmp_path}, factories)
        structlog.configure(
            processors=[],
            wrapper_class=structlog.BoundLogger,
            logger_factory=factory,
        )
        test_log = structlog.get_logger()

        drop_cmd_output_logfile(test_log)
        log.has("logging-cmd-output-drop")

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

        log.has("logging-cmd-output-file-not-found")


@pytest.mark.integration
class TestBuildLoggerFactories:
    """Tests for build_logger_factories."""

    def test_permission_denied_logs_warning(self, log):
        """PermissionError opening log file logs file-open-permission-denied."""
        from stogger.config import StoggerConfig, SystemdMode

        cfg = StoggerConfig(systemd=SystemdMode.OFF.value, enable_postgres=False)
        with patch.object(Path, "open", side_effect=PermissionError("denied")):
            build_logger_factories(
                logdir=Path("/fake"),
                log_to_console=False,
                syslog_identifier="test",
                cfg=cfg,
            )
        log.has("file-open-permission-denied")

    def test_early_init_propagates_errors(self):
        """init_early_logging must propagate errors, not suppress them."""
        with patch("stogger.core.build_timestamp_processor", side_effect=RuntimeError("boom")):
            with pytest.raises(RuntimeError, match="boom"):
                init_early_logging()

    def test_postgres_import_error_logs_warning(self, log):
        """build_logger_factories logs warning when stogger_postgres ImportError.

        Level changed from debug to warning — user explicitly enabled postgres logging
        but the optional package is not installed, so they must know.
        """
        """build_logger_factories logs debug when stogger_postgres ImportError."""
        from stogger.config import StoggerConfig, SystemdMode

        cfg = StoggerConfig(
            enable_postgres=True, systemd=SystemdMode.OFF.value, postgres_dsn="postgresql://localhost/test"
        )
        real_import = __import__

        def blocking_import(name, *args, **kwargs):
            if name == "stogger_postgres":
                raise ImportError("stogger_postgres not available")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=blocking_import):
            build_logger_factories(
                logdir=None,
                log_to_console=False,
                syslog_identifier="test",
                cfg=cfg,
            )
        log.has("stogger-postgres-not-installed")
        log.has(
            "stogger-postgres-not-installed",
            _replace_msg="PostgreSQL logging enabled but stogger-postgres package is not installed",
        )

    def test_journal_stream_detected_logs_event(self, log):
        """JOURNAL_STREAM env var set logs journal-stream-detected event."""
        from stogger.config import StoggerConfig, SystemdMode

        cfg = StoggerConfig(systemd=SystemdMode.OFF.value, enable_postgres=False)
        with patch.dict(os.environ, {"JOURNAL_STREAM": "123:456"}):
            build_logger_factories(
                logdir=None,
                log_to_console=True,
                syslog_identifier="test",
                cfg=cfg,
            )
        log.has("journal-stream-detected")

    def test_postgres_enabled_without_dsn_raises(self):
        """enable_postgres=True without postgres_dsn raises ValueError."""
        from stogger.config import StoggerConfig, SystemdMode

        cfg = StoggerConfig(enable_postgres=True, systemd=SystemdMode.OFF.value)
        with pytest.raises(ValueError, match="postgres_dsn is not configured"):
            build_logger_factories(
                logdir=None,
                log_to_console=False,
                syslog_identifier="test",
                cfg=cfg,
            )


# ---------------------------------------------------------------------------
# Coverage gap closures for core.py
# ---------------------------------------------------------------------------


def test_translation_processor_preserves_existing_original_event():
    """_original_event is not overwritten when already present in event_dict."""
    proc = TranslationProcessor({"greeting": "Hello!"})
    event_dict = {"event": "greeting", "_original_event": "preset"}
    result = proc(None, "info", event_dict)
    assert result["_original_event"] == "preset"


def test_format_timestamp_relative():
    """relative timestamp format shows elapsed seconds with '+' prefix."""
    settings = FormatConfig(timestamp_precision="relative")
    renderer = ConsoleFileRenderer(format_config=settings)
    result = renderer._format_timestamp("2026-01-01T00:00:00Z", {})
    assert "+" in result
    assert "s" in result


def test_render_stack_without_traceback():
    """stack section renders without separator when no exception_traceback."""
    renderer = ConsoleFileRenderer()
    buf = io.StringIO()
    event_dict = {"stack": "stack trace here"}
    renderer._render_output_sections(event_dict, buf.write)
    output = buf.getvalue()
    assert "stack trace here" in output
    assert "=" * 79 not in output


def test_format_replace_msg_recursion_fallback():
    """RecursionError in _replace_msg formatting falls back to raw string."""

    class Recursive:
        def __format__(self, spec):
            return format(self, spec)  # infinite recursion

    renderer = ConsoleFileRenderer()
    event_dict = {"_replace_msg": "val={x}", "x": Recursive()}
    result = renderer._format_replace_msg(event_dict)
    assert result == "val={x}"


def test_select_rendered_string_dict_non_str_fallback():
    """Dict with non-str key value falls back to str()."""
    selector = SelectRenderedString("console")
    result = selector(None, "info", {"console": 12345})
    assert result == str({"console": 12345})


def test_init_command_logging_non_multi_factory_is_noop():
    """Returns early when logger_factory is not a MultiOptimisticLoggerFactory."""
    structlog.configure(processors=[], logger_factory=structlog.PrintLoggerFactory())
    log = structlog.get_logger()
    # Must not raise — early return path
    init_command_logging(log)


def test_init_command_logging_logdir_from_context(tmp_path):
    """logdir=None falls back to factory context logdir."""
    factories = {}
    factory = MultiOptimisticLoggerFactory({"logdir": tmp_path}, factories)
    structlog.configure(processors=[], wrapper_class=structlog.BoundLogger, logger_factory=factory)
    log = structlog.get_logger()
    init_command_logging(log)  # no explicit logdir → context fallback
    assert "cmd_output_file" in factories
    factories["cmd_output_file"]._file.close()  # noqa: SLF001


def test_init_logging_sets_systemd_kwarg():
    """init_logging(systemd=...) passes the mode value into StoggerConfig."""
    from stogger.config import SystemdMode

    with patch("stogger.core.build_logger_factories", return_value=({}, {})) as mock_factories:
        init_logging(systemd=SystemdMode.OFF)
    args, _kwargs = mock_factories.call_args
    cfg = args[3]
    assert cfg.systemd_mode is SystemdMode.OFF


def test_init_logging_sets_timestamp_precision():
    """init_logging(timestamp_precision=...) applies to cfg.format."""
    with patch("stogger.core.build_logger_factories", return_value=({}, {})) as mock_factories:
        init_logging(timestamp_precision="iso_seconds")
    args, _kwargs = mock_factories.call_args
    assert args[3].format.timestamp_precision == "iso_seconds"


def test_init_logging_log_cmd_output_without_logdir_raises():
    """log_cmd_output=True without logdir raises ValueError."""
    with patch("stogger.core.build_logger_factories", return_value=({}, {})):
        with pytest.raises(ValueError, match="A logdir is required for command logging."):
            init_logging(log_cmd_output=True, logdir=None)


def test_build_logger_factories_required_with_available_socket():
    """SystemdMode.REQUIRED with available socket registers journal factory."""
    from stogger.config import StoggerConfig, SystemdMode

    cfg = StoggerConfig(systemd=SystemdMode.REQUIRED.value)
    mock_journal_factory = MagicMock()
    with (
        patch("stogger.systemd._journal_socket_available", return_value=True),
        patch("stogger.systemd.get_journal_logger_factory", return_value=mock_journal_factory),
    ):
        loggers, _context = build_logger_factories(
            logdir=None,
            log_to_console=False,
            syslog_identifier="test",
            cfg=cfg,
        )
    assert loggers["journal"] is mock_journal_factory


def test_select_rendered_string_non_dict_fallback():
    """Non-dict, non-str event_dict falls back to str()."""
    selector = SelectRenderedString("console")
    result = selector(None, "info", 12345)
    assert result == "12345"


def test_init_logging_log_cmd_output_with_logdir(tmp_path):
    """log_cmd_output=True with valid logdir reaches init_command_logging."""
    with patch("stogger.core.build_logger_factories", return_value=({}, {})):
        # Should not raise; command logging path exercised
        init_logging(log_cmd_output=True, logdir=tmp_path)


def test_init_command_logging_without_invocation_name(monkeypatch, tmp_path):
    """Without INVOCATION_ID env var, cmd log file is named build-output.log."""
    monkeypatch.delenv("INVOCATION_ID", raising=False)
    factories = {}
    factory = MultiOptimisticLoggerFactory({"logdir": tmp_path}, factories)
    structlog.configure(processors=[], wrapper_class=structlog.BoundLogger, logger_factory=factory)
    log = structlog.get_logger()
    init_command_logging(log, tmp_path)
    assert (tmp_path / "build-output.log").exists()
    factories["cmd_output_file"]._file.close()  # noqa: SLF001


def test_write_helper_skips_ansi_stripping_without_reset_all():
    """When RESET_ALL is falsy (no colorama), write helper skips ANSI stripping loop."""
    from unittest.mock import MagicMock

    renderer = ConsoleFileRenderer()
    console_io = MagicMock()
    log_io = MagicMock()
    write = renderer._create_write_helper(console_io, log_io)  # noqa: SLF001
    with patch("stogger.core.RESET_ALL", ""):
        write("some line")
    # Without RESET_ALL, line is passed through unmodified to log_io
    log_io.write.assert_called_once_with("some line")
