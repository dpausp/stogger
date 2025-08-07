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
        renderer = ConsoleFileRenderer(show_caller_info=True)
        # This is mainly for initialization - actual caller info is added by add_caller_info processor
        assert renderer.show_caller_info is True

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
        assert "[root]" in result["console"]  # Default logger name


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


if __name__ == "__main__":
    pytest.main([__file__])
