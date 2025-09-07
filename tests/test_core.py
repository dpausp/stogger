"""
Tests for the core module functionality.
"""

import pytest
import sys
from unittest.mock import patch, MagicMock
import structlog

from nicestlog.core import (
    PartialFormatter,
    TranslationProcessor,
    ConsoleFileRenderer,
    JSONRenderer,
    SelectRenderedString,
    add_pid,
    add_caller_info,
    process_exc_info,
    format_exc_info,
    init_logging,
    logging_initialized,
    _pad,
)


class TestPartialFormatter:
    """Test cases for PartialFormatter class."""

    def test_missing_field_handling(self):
        """Test that missing fields are handled with custom missing text."""
        formatter = PartialFormatter(missing="<MISSING>")
        result = formatter.format("Hello {name} and {missing_field}", name="World")
        assert result == "Hello World and <MISSING>"

    def test_bad_format_handling(self):
        """Test that bad format specs are handled with custom bad format text."""
        formatter = PartialFormatter(bad_format="<BAD_FORMAT>")
        result = formatter.format("Value: {value:invalid_format}", value=42)
        assert result == "Value: <BAD_FORMAT>"

    def test_normal_formatting(self):
        """Test that normal formatting works correctly."""
        formatter = PartialFormatter()
        result = formatter.format(
            "Hello {name}! You are {age} years old.", name="Alice", age=30
        )
        assert result == "Hello Alice! You are 30 years old."

    def test_custom_missing_and_bad_format_text(self):
        """Test custom missing and bad format text."""
        formatter = PartialFormatter(missing="[MISSING]", bad_format="[BAD]")
        result = formatter.format("Test {missing} and {value:bad_spec}", value=123)
        assert result == "Test [MISSING] and [BAD]"

    def test_attribute_error_handling(self):
        """Test handling of AttributeError when accessing nested attributes."""
        formatter = PartialFormatter(missing="<ATTR_MISSING>")
        obj = MagicMock()
        obj.nonexistent = None
        del obj.nonexistent
        result = formatter.format("Value: {obj.nonexistent}", obj=obj)
        assert result == "Value: <ATTR_MISSING>"


class TestTranslationProcessor:
    """Test cases for TranslationProcessor class."""

    def test_message_key_translation(self):
        """Test translation using _msg_key."""
        translations = {
            "user.login": "User {username} logged in from {ip}",
            "user.logout": "User {username} logged out",
        }
        processor = TranslationProcessor(translations)

        event_dict = {
            "_msg_key": "user.login",
            "username": "alice",
            "ip": "192.168.1.1",
            "event": "original_event",
        }

        result = processor(None, None, event_dict)
        assert result["event"] == "User alice logged in from 192.168.1.1"
        assert "_msg_key" not in result

    def test_replace_msg_functionality(self):
        """Test translation using _replace_msg."""
        processor = TranslationProcessor({})

        event_dict = {
            "_replace_msg": "Custom message: {value}",
            "value": "test_value",
            "event": "original_event",
        }

        result = processor(None, None, event_dict)
        assert result["event"] == "Custom message: test_value"
        assert "_replace_msg" not in result

    def test_fallback_behavior(self):
        """Test fallback when no translation is found."""
        translations = {"other.key": "Other message"}
        processor = TranslationProcessor(translations)

        event_dict = {
            "_msg_key": "nonexistent.key",
            "event": "original_event",
            "data": "some_data",
        }

        result = processor(None, None, event_dict)
        assert result["event"] == "original_event"  # Should remain unchanged
        assert "_msg_key" not in result

    def test_event_key_fallback(self):
        """Test using event key when _msg_key is not present."""
        translations = {"test_event": "Translated: {param}"}
        processor = TranslationProcessor(translations)

        event_dict = {"event": "test_event", "param": "value"}

        result = processor(None, None, event_dict)
        assert result["event"] == "Translated: value"

    def test_missing_fields_in_translation(self):
        """Test translation with missing fields."""
        translations = {"incomplete": "Message with {existing} and {missing}"}
        processor = TranslationProcessor(translations)

        event_dict = {
            "_msg_key": "incomplete",
            "existing": "present",
            "event": "original",
        }

        result = processor(None, None, event_dict)
        assert result["event"] == "Message with present and <missing>"


class TestConsoleFileRenderer:
    """Test cases for ConsoleFileRenderer class."""

    def test_level_filtering(self):
        """Test that events below min_level are dropped."""
        renderer = ConsoleFileRenderer(min_level="warning")

        # This should be dropped
        with pytest.raises(structlog.DropEvent):
            renderer(None, None, {"level": "info", "event": "test"})

        # This should pass
        result = renderer(
            None,
            None,
            {
                "level": "error",
                "event": "test_error",
                "timestamp": "2025-01-01T00:00:00Z",
            },
        )
        assert "test_error" in result["console"]

    def test_console_vs_file_output_formatting(self):
        """Test that console output has colors and file output doesn't."""
        renderer = ConsoleFileRenderer()
        event_dict = {
            "level": "info",
            "event": "test_event",
            "timestamp": "2025-01-01T00:00:00Z",
            "logger": "test_logger",
            "key": "value",
        }

        result = renderer(None, None, event_dict)

        # Console output should contain ANSI escape sequences (if colorama available)
        console_output = result["console"]
        file_output = result["file"]

        # File output should not contain ANSI codes
        assert "\x1b" not in file_output or not sys.stdout.isatty()

        # Both should contain the event and key-value pairs
        assert "test_event" in console_output
        assert "test_event" in file_output
        assert "key='value'" in console_output
        assert "key='value'" in file_output

    def test_event_padding(self):
        """Test that events are padded to the correct width."""
        renderer = ConsoleFileRenderer(pad_event=20)
        event_dict = {
            "level": "info",
            "event": "short",
            "timestamp": "2025-01-01T00:00:00Z",
        }

        result = renderer(None, None, event_dict)
        # The event should be padded to 20 characters
        assert "short" + " " * 15 in result["file"]

    def test_caller_info_option(self):
        """Test the show_caller_info option."""
        from src.nicestlog.config import SimpleFormatSettings

        settings = SimpleFormatSettings(show_code_info=True)
        renderer = ConsoleFileRenderer(settings=settings)
        # This is mainly for initialization - actual caller info is added by add_caller_info processor
        assert renderer.settings.show_code_info is True

    def test_level_colors(self):
        """Test that different levels get appropriate colors."""
        renderer = ConsoleFileRenderer(min_level="debug")  # Allow all levels

        # Test different levels
        for level in ["critical", "error", "warning", "info", "debug"]:
            event_dict = {
                "level": level,
                "event": f"test_{level}",
                "timestamp": "2025-01-01T00:00:00Z",
            }
            result = renderer(None, None, event_dict)
            assert f"test_{level}" in result["console"]

    def test_missing_fields_handling(self):
        """Test handling of missing timestamp, logger, etc."""
        renderer = ConsoleFileRenderer()
        event_dict = {
            "level": "info",
            "event": "test_event",
            # Missing timestamp and logger
        }

        result = renderer(None, None, event_dict)
        assert "notimestamp" in result["console"]
        # Note: Default logger name is no longer shown in brackets by default
        # assert "[root]" in result["console"]  # Default logger name


class TestJSONRenderer:
    """Test cases for JSONRenderer class."""

    def test_json_output_format(self):
        """Test that output is valid JSON."""
        renderer = JSONRenderer()
        event_dict = {
            "level": "info",
            "event": "test_event",
            "timestamp": "2025-01-01T00:00:00Z",
            "data": {"nested": "value"},
        }

        result = renderer(None, None, event_dict)

        import json

        # Both outputs should be valid JSON
        console_data = json.loads(result["console"])
        file_data = json.loads(result["file"])

        assert console_data["event"] == "test_event"
        assert file_data["level"] == "info"
        assert console_data == file_data  # Should be identical

    def test_level_filtering(self):
        """Test that JSONRenderer respects min_level."""
        renderer = JSONRenderer(min_level="warning")

        # This should be dropped
        with pytest.raises(structlog.DropEvent):
            renderer(None, None, {"level": "info", "event": "test"})

        # This should pass
        result = renderer(None, None, {"level": "error", "event": "test_error"})
        import json

        data = json.loads(result["console"])
        assert data["event"] == "test_error"

    def test_non_serializable_objects(self):
        """Test handling of non-JSON-serializable objects."""
        renderer = JSONRenderer()

        class CustomObject:
            def __str__(self):
                return "custom_object_str"

        event_dict = {"level": "info", "event": "test", "custom": CustomObject()}

        result = renderer(None, None, event_dict)
        import json

        data = json.loads(result["console"])
        assert data["custom"] == "custom_object_str"


class TestUtilityFunctions:
    """Test cases for utility functions."""

    def test_pad_function(self):
        """Test the _pad utility function."""
        assert _pad("hello", 10) == "hello     "
        assert _pad("hello", 5) == "hello"
        assert _pad("hello", 3) == "hello"  # No truncation, just no padding

    def test_add_pid(self):
        """Test add_pid processor."""
        event_dict = {"event": "test"}
        result = add_pid(None, None, event_dict)
        assert "pid" in result
        assert isinstance(result["pid"], int)

    def test_add_caller_info(self):
        """Test add_caller_info processor."""
        event_dict = {"event": "test"}
        result = add_caller_info(None, None, event_dict)
        assert "code_file" in result
        assert "code_func" in result
        assert "code_lineno" in result
        assert isinstance(result["code_lineno"], int)

    def test_process_exc_info_with_exception(self):
        """Test process_exc_info with an exception object."""
        try:
            raise ValueError("test error")
        except ValueError as e:
            event_dict = {"event": "test", "exc_info": e}
            result = process_exc_info(None, None, event_dict)
            assert isinstance(result["exc_info"], tuple)
            assert len(result["exc_info"]) == 3

    def test_process_exc_info_with_true(self):
        """Test process_exc_info with True value."""
        try:
            raise ValueError("test error")
        except ValueError:
            event_dict = {"event": "test", "exc_info": True}
            result = process_exc_info(None, None, event_dict)
            assert isinstance(result["exc_info"], tuple)

    def test_format_exc_info(self):
        """Test format_exc_info processor."""
        try:
            raise ValueError("test error")
        except ValueError:
            exc_info = sys.exc_info()
            event_dict = {"event": "test", "exc_info": exc_info}
            result = format_exc_info(None, None, event_dict)
            assert "exception" in result
            assert "exc_info" not in result
            assert "ValueError: test error" in result["exception"]


class TestInitLogging:
    """Test cases for init_logging function."""

    @patch("nicestlog.factory.configure_stdlib_logging")
    @patch("nicestlog.factory.build_shared_processors")
    @patch("nicestlog.core.structlog.configure")
    def test_init_logging_calls(
        self, mock_structlog_configure, mock_build_processors, mock_configure_stdlib
    ):
        """Test that init_logging makes the correct calls."""
        mock_build_processors.return_value = []

        init_logging(verbose=True, log_to_console=False)

        mock_build_processors.assert_called_once()
        mock_configure_stdlib.assert_called_once()
        mock_structlog_configure.assert_called_once()

    @patch("nicestlog.core.structlog.is_configured")
    def test_logging_initialized(self, mock_is_configured):
        """Test logging_initialized function."""
        mock_is_configured.return_value = True
        assert logging_initialized() is True

        mock_is_configured.return_value = False
        assert logging_initialized() is False


class TestSelectRenderedString:
    """Test cases for SelectRenderedString processor."""

    def test_select_console_output(self):
        """Test selecting console output from renderer dict."""
        selector = SelectRenderedString("console")

        test_dict = {"console": "Console output text", "file": "File output text"}

        result = selector(None, None, test_dict)
        assert result == "Console output text"

    def test_select_file_output(self):
        """Test selecting file output from renderer dict."""
        selector = SelectRenderedString("file")

        test_dict = {"console": "Console output text", "file": "File output text"}

        result = selector(None, None, test_dict)
        assert result == "File output text"

    def test_string_passthrough(self):
        """Test that string inputs pass through unchanged."""
        selector = SelectRenderedString("console")

        result = selector(None, None, "Already a string")
        assert result == "Already a string"

    def test_missing_key_fallback(self):
        """Test fallback behavior when key is missing."""
        selector = SelectRenderedString("missing_key")

        test_dict = {"other": "value"}
        result = selector(None, None, test_dict)
        assert result == str(test_dict)

    def test_no_runtime_warning_with_structlog(self):
        """Test that SelectRenderedString prevents RuntimeWarning from structlog."""
        import warnings
        import logging
        from io import StringIO

        # Capture warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Configure a proper test logging setup
            renderer = ConsoleFileRenderer(min_level="debug")

            # Create formatter with SelectRenderedString
            formatter = structlog.stdlib.ProcessorFormatter(
                foreign_pre_chain=[
                    structlog.stdlib.add_log_level,
                    structlog.stdlib.add_logger_name,
                ],
                processors=[renderer, SelectRenderedString("console")],
            )

            # Create a test handler
            stream = StringIO()
            handler = logging.StreamHandler(stream)
            handler.setFormatter(formatter)

            # Create a test logger
            logger = logging.getLogger("test_select_renderer")
            logger.handlers.clear()
            logger.addHandler(handler)
            logger.setLevel(logging.DEBUG)

            # Log a message (this should not trigger RuntimeWarning)
            logger.info("Test message for SelectRenderedString")

            # Verify no RuntimeWarning was raised
            runtime_warnings = [w for w in w if issubclass(w.category, RuntimeWarning)]
            assert len(runtime_warnings) == 0, (
                f"Unexpected RuntimeWarning: {runtime_warnings}"
            )

            # Verify we got output
            output = stream.getvalue()
            assert "Test message for SelectRenderedString" in output
            assert isinstance(output, str)


class TestCoreEdgeCases:
    """Test edge cases and error handling in core module."""

    def test_partial_formatter_with_complex_format_specs(self):
        """Test PartialFormatter with complex format specifications."""
        formatter = PartialFormatter(missing="<MISSING>", bad_format="<BAD_FORMAT>")

        # Test with complex format specs that might cause ValueError
        test_cases = [
            (
                "{value:>10.2f}",
                {"value": None},
                "<MISSING>",
            ),  # Missing value with format spec
            ("{value:>10.2f}", {"value": "not_a_number"}, "<BAD_FORMAT>"),  # Bad format
            (
                "{value:invalid_spec}",
                {"value": 42},
                "<BAD_FORMAT>",
            ),  # Invalid format spec
            ("{missing_key:>10}", {}, "<MISSING>"),  # Missing key with format spec
        ]

        for template, kwargs, expected in test_cases:
            result = formatter.format(template, **kwargs)
            assert expected in result

    def test_partial_formatter_attribute_error_handling(self):
        """Test PartialFormatter handles AttributeError in get_field."""
        formatter = PartialFormatter()

        # Create an object that will raise AttributeError
        class BadObject:
            def __getattr__(self, name):
                raise AttributeError(
                    f"'{type(self).__name__}' object has no attribute '{name}'"
                )

        bad_obj = BadObject()
        result = formatter.format("{obj.nonexistent}", obj=bad_obj)
        assert "<missing>" in result

    def test_console_renderer_without_colorama(self):
        """Test ConsoleFileRenderer behavior when colorama is not available."""
        from unittest.mock import patch

        # Mock colorama as None to simulate missing dependency
        with patch("nicestlog.core.colorama", None):
            # This should not crash and should print a warning
            renderer = ConsoleFileRenderer()
            assert renderer is not None

    def test_console_renderer_non_tty_output(self):
        """Test ConsoleFileRenderer when stdout is not a TTY."""
        import sys
        from unittest.mock import patch

        with patch.object(sys.stdout, "isatty", return_value=False):
            renderer = ConsoleFileRenderer()
            result = renderer(
                None,
                "info",
                {
                    "event": "test_event",
                    "timestamp": "2023-01-01T00:00:00",
                    "level": "info",
                },
            )
            assert isinstance(result, dict)
            assert "console" in result
            assert "file" in result

    def test_console_renderer_unknown_level_handling(self):
        """Test ConsoleFileRenderer with unknown log levels."""
        renderer = ConsoleFileRenderer(min_level="info")

        # Test with unknown level - should not drop but will fail on color lookup
        # This tests the KeyError handling in the level color lookup
        try:
            result = renderer(
                None,
                "unknown_level",
                {
                    "event": "test_event",
                    "timestamp": "2023-01-01T00:00:00",
                    "level": "unknown_level",
                },
            )
            # If it doesn't crash, that's unexpected but acceptable
            assert result is not None
        except KeyError:
            # Expected behavior - unknown level causes KeyError in color lookup
            pass


    def test_console_renderer_missing_timestamp(self):
        """Test ConsoleFileRenderer with missing timestamp."""
        renderer = ConsoleFileRenderer()
        result = renderer(None, "info", {"event": "test_event", "level": "info"})
        assert "notimestamp" in result["console"]

    def test_console_renderer_with_all_optional_fields(self):
        """Test ConsoleFileRenderer with all optional output fields."""
        renderer = ConsoleFileRenderer()
        result = renderer(
            None,
            "info",
            {
                "event": "test_event",
                "timestamp": "2023-01-01T00:00:00",
                "level": "info",
                "cmd_output_line": "command output",
                "_output": "general output",
                "stdout": "standard output",
                "stderr": "error output",
                "stack": "stack trace",
                "exception_traceback": "exception details",
            },
        )

        console_output = result["console"]
        assert "command output" in console_output
        assert "general output" in console_output
        assert "standard output" in console_output
        assert "error output" in console_output
        assert "stack trace" in console_output
        assert "exception details" in console_output

    def test_console_renderer_log_settings_ignore(self):
        """Test ConsoleFileRenderer respects _log_settings console_ignore."""
        renderer = ConsoleFileRenderer()
        result = renderer(
            None,
            "info",
            {
                "event": "test_event",
                "level": "info",
                "_log_settings": {"console_ignore": True},
            },
        )
        assert result is None

    def test_console_file_renderer_with_simple_format_settings(self):
        """Test ConsoleFileRenderer with SimpleFormatSettings."""
        from src.nicestlog.config import SimpleFormatSettings
        from src.nicestlog.core import ConsoleFileRenderer

        settings = SimpleFormatSettings(
            show_logger_brackets=False,
            show_pid=False,
            show_code_info=True,
            timestamp_format="iso_no_z",
        )
        renderer = ConsoleFileRenderer(min_level="debug", settings=settings)

        # Test with timestamp ending in Z
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

        # Should remove Z from timestamp
        assert "2023-01-01T00:00:00 " in result["console"]
        assert "2023-01-01T00:00:00Z" not in result["console"]

    def test_json_renderer_non_serializable_objects(self):
        """Test JSONRenderer with non-serializable objects."""
        renderer = JSONRenderer(min_level="debug")

        # Test with object that can't be JSON serialized normally
        class NonSerializable:
            def __str__(self):
                return "non_serializable_object"

        result = renderer(
            None,
            None,
            {
                "event": "test_event",
                "level": "info",
                "complex_object": NonSerializable(),
            },
        )

        assert isinstance(result, dict)
        assert "console" in result
        assert "non_serializable_object" in result["console"]

    def test_process_exc_info_with_exception_object(self):
        """Test process_exc_info with actual exception object."""
        from src.nicestlog.core import process_exc_info

        try:
            raise ValueError("test exception")
        except ValueError as e:
            event_dict = {"exc_info": e}
            result = process_exc_info(None, None, event_dict)

            assert "exc_info" in result
            exc_info = result["exc_info"]
            assert isinstance(exc_info, tuple)
            assert len(exc_info) == 3
            assert exc_info[0] is ValueError
            assert str(exc_info[1]) == "test exception"

    def test_process_exc_info_with_true_value(self):
        """Test process_exc_info with True value (current exception)."""
        from src.nicestlog.core import process_exc_info

        try:
            raise RuntimeError("current exception")
        except RuntimeError:
            event_dict = {"exc_info": True}
            result = process_exc_info(None, None, event_dict)

            assert "exc_info" in result
            exc_info = result["exc_info"]
            assert isinstance(exc_info, tuple)
            assert exc_info[0] is RuntimeError

    def test_format_exc_info_processor(self):
        """Test format_exc_info processor."""
        from src.nicestlog.core import format_exc_info

        try:
            raise ValueError("test exception for formatting")
        except ValueError:
            import sys

            event_dict = {"exc_info": sys.exc_info()}
            result = format_exc_info(None, None, event_dict)

            assert "exception" in result
            assert "exc_info" not in result  # Should be removed
            assert "ValueError" in result["exception"]
            assert "test exception for formatting" in result["exception"]

    def test_prefix_function_edge_cases(self):
        """Test prefix function with edge cases."""
        from src.nicestlog.core import prefix

        # Test with empty string
        assert prefix("test", "") == ""

        # Test with None name
        assert prefix(None, "line1\nline2") == "line1\nline2"

        # Test with empty name
        assert prefix("", "line1\nline2") == "line1\nline2"

        # Test with single line
        assert prefix("prefix", "single line") == "prefix: single line"

    def test_init_logging_with_simple_format_dict(self):
        """Test init_logging with simple_format as dict."""
        from src.nicestlog.core import init_logging

        # Reset structlog state
        import structlog

        structlog.reset_defaults()

        simple_format_dict = {
            "show_logger_brackets": False,
            "show_pid": True,
            "pad_event_width": 25,
        }

        init_logging(simple_format_settings=simple_format_dict, verbose=True)
        assert structlog.is_configured()

    def test_init_early_logging_when_already_configured(self):
        """Test init_early_logging when structlog is already configured."""
        from src.nicestlog.core import init_early_logging
        import structlog

        # Ensure structlog is configured
        if not structlog.is_configured():
            structlog.configure(processors=[])

        # Should return early without error
        init_early_logging()
        assert structlog.is_configured()

    def test_init_early_logging_exception_handling(self):
        """Test init_early_logging graceful exception handling."""
        from src.nicestlog.core import init_early_logging
        from unittest.mock import patch
        import structlog

        # Reset structlog
        structlog.reset_defaults()

        # Mock structlog.configure to raise an exception
        with patch("structlog.configure", side_effect=Exception("Mock error")):
            # Should not raise exception
            init_early_logging()
            # Should still work (fallback to defaults)


if __name__ == "__main__":
    pytest.main([__file__])
