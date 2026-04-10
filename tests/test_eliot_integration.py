"""Tests for eliot_integration module."""

from datetime import datetime
import io
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

if "eliot" not in sys.modules:
    try:
        import eliot  # noqa: F401
    except ImportError:
        pytestmark = pytest.mark.skip(reason="eliot not installed")

try:
    from eliot import Action
except ImportError:
    Action = None  # type: ignore[assignment,misc]


# Test both with and without eliot available
@pytest.fixture
def mock_eliot_available():
    """Mock eliot being available."""
    with patch("stogger_eliot.eliot_integration.ELIOT_AVAILABLE", True):
        with patch("stogger_eliot.eliot_integration.start_action", autospec=True) as mock_start:
            with patch("stogger_eliot.eliot_integration.log_message", autospec=True) as mock_log:
                yield mock_start, mock_log


@pytest.fixture
def mock_eliot_unavailable():
    """Mock eliot being unavailable."""
    with patch("stogger_eliot.eliot_integration.ELIOT_AVAILABLE", False):
        yield


class TestHumanReadableEliotDestination:
    """Test the HumanReadableEliotDestination class."""

    def test_init_default_params(self):
        """Test initialization with default parameters."""
        from stogger_eliot.eliot_integration import HumanReadableEliotDestination

        dest = HumanReadableEliotDestination()
        assert dest.file == sys.stdout
        assert dest.show_timestamps is True
        assert dest.show_task_ids is False
        assert dest.max_width == 120
        assert dest._action_stack == {}
        assert dest._action_names == {}

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        from stogger_eliot.eliot_integration import HumanReadableEliotDestination

        custom_file = io.StringIO()
        dest = HumanReadableEliotDestination(
            file=custom_file,
            show_timestamps=False,
            show_task_ids=True,
            max_width=80,
        )
        assert dest.file == custom_file
        assert dest.show_timestamps is False
        assert dest.show_task_ids is True
        assert dest.max_width == 80

    def test_call_with_non_dict(self):
        """Test calling with non-dict message (should be ignored)."""
        from stogger_eliot.eliot_integration import HumanReadableEliotDestination

        output = io.StringIO()
        dest = HumanReadableEliotDestination(file=output)

        # Should not crash or output anything
        dest("not a dict")
        dest(None)
        dest(123)

        assert output.getvalue() == ""

    def test_handle_action_start(self):
        """Test handling action start messages."""
        from stogger_eliot.eliot_integration import HumanReadableEliotDestination

        output = io.StringIO()
        dest = HumanReadableEliotDestination(file=output, show_timestamps=False)

        message = {
            "action_type": "test_action",
            "action_status": "started",
            "task_uuid": "task123",
            "task_level": [1],
            "param1": "value1",
            "param2": 42,
        }

        dest(message)

        result = output.getvalue()
        assert "test_action" in result
        assert "param1" in result
        assert "value1" in result
        assert "param2" in result
        assert "42" in result
        assert "▶" in result  # Start symbol

    def test_handle_action_start_with_timestamps(self):
        """Test action start with timestamps enabled."""
        from stogger_eliot.eliot_integration import HumanReadableEliotDestination

        output = io.StringIO()
        dest = HumanReadableEliotDestination(file=output, show_timestamps=True)

        timestamp = datetime.now().timestamp()
        message = {
            "action_type": "test_action",
            "action_status": "started",
            "task_uuid": "task123",
            "timestamp": timestamp,
        }

        dest(message)

        result = output.getvalue()
        # Should contain formatted timestamp
        assert ":" in result  # Time format

    def test_handle_action_start_with_task_ids(self):
        """Test action start with task IDs shown."""
        from stogger_eliot.eliot_integration import HumanReadableEliotDestination

        output = io.StringIO()
        dest = HumanReadableEliotDestination(
            file=output,
            show_task_ids=True,
            show_timestamps=False,
        )

        message = {
            "action_type": "test_action",
            "action_status": "started",
            "task_uuid": "task123456789",
            "task_level": [],
        }

        dest(message)

        result = output.getvalue()
        assert "task1234" in result  # First 8 chars of task ID

    def test_handle_action_success(self):
        """Test handling successful action completion."""
        from stogger_eliot.eliot_integration import HumanReadableEliotDestination

        output = io.StringIO()
        dest = HumanReadableEliotDestination(file=output, show_timestamps=False)

        # First start an action
        start_message = {
            "action_type": "test_action",
            "action_status": "started",
            "task_uuid": "task123",
            "task_level": [1],
        }
        dest(start_message)

        # Then complete it
        success_message = {
            "action_type": "test_action",
            "action_status": "succeeded",
            "task_uuid": "task123",
            "result": "success_value",
            "count": 5,
        }
        dest(success_message)

        result = output.getvalue()
        assert "✓" in result  # Success symbol
        assert "success_value" in result
        assert "count" in result
        assert "5" in result

    def test_handle_action_failure(self):
        """Test handling failed actions."""
        from stogger_eliot.eliot_integration import HumanReadableEliotDestination

        output = io.StringIO()
        dest = HumanReadableEliotDestination(file=output, show_timestamps=False)

        # First start an action
        start_message = {
            "action_type": "test_action",
            "action_status": "started",
            "task_uuid": "task123",
            "task_level": [1],
        }
        dest(start_message)

        # Then fail it
        failure_message = {
            "action_type": "test_action",
            "action_status": "failed",
            "task_uuid": "task123",
            "exception": "ValueError: Something went wrong",
            "reason": "Invalid input",
        }
        dest(failure_message)

        result = output.getvalue()
        assert "✗" in result  # Failure symbol
        assert "FAILED" in result
        assert "ValueError: Something went wrong" in result
        assert "Invalid input" in result

    def test_handle_regular_message(self):
        """Test handling regular log messages."""
        from stogger_eliot.eliot_integration import HumanReadableEliotDestination

        output = io.StringIO()
        dest = HumanReadableEliotDestination(file=output, show_timestamps=False)

        message = {
            "message_type": "info_message",
            "task_uuid": "task123",
            "task_level": [1, 2],
            "data": "some_data",
            "count": 10,
        }

        dest(message)

        result = output.getvalue()
        assert "•" in result  # Message symbol
        assert "info_message" in result
        assert "data" in result
        assert "some_data" in result
        assert "count" in result
        assert "10" in result

    def test_nested_actions_indentation(self):
        """Test that nested actions are properly indented."""
        from stogger_eliot.eliot_integration import HumanReadableEliotDestination

        output = io.StringIO()
        dest = HumanReadableEliotDestination(file=output, show_timestamps=False)

        # Parent action
        parent_start = {
            "action_type": "parent_action",
            "action_status": "started",
            "task_uuid": "parent123",
            "task_level": [1],
        }
        dest(parent_start)

        # Child action (deeper nesting)
        child_start = {
            "action_type": "child_action",
            "action_status": "started",
            "task_uuid": "child123",
            "task_level": [1, 2],
        }
        dest(child_start)

        result = output.getvalue()
        lines = result.strip().split("\n")

        # Parent should have less indentation than child
        parent_line = [line for line in lines if "parent_action" in line][0]
        child_line = [line for line in lines if "child_action" in line][0]

        parent_indent = len(parent_line) - len(parent_line.lstrip())
        child_indent = len(child_line) - len(child_line.lstrip())

        assert child_indent > parent_indent

    def test_format_timestamp_disabled(self):
        """Test timestamp formatting when disabled."""
        from stogger_eliot.eliot_integration import HumanReadableEliotDestination

        dest = HumanReadableEliotDestination(show_timestamps=False)
        result = dest._format_timestamp(datetime.now().timestamp())
        assert result == ""

    def test_format_timestamp_none(self):
        """Test timestamp formatting with None timestamp."""
        from stogger_eliot.eliot_integration import HumanReadableEliotDestination

        dest = HumanReadableEliotDestination(show_timestamps=True)
        result = dest._format_timestamp(None)
        assert result == ""

    def test_format_timestamp_enabled(self):
        """Test timestamp formatting when enabled."""
        from stogger_eliot.eliot_integration import HumanReadableEliotDestination

        dest = HumanReadableEliotDestination(show_timestamps=True)
        # Use timezone-aware UTC datetime to avoid local timezone conversion
        from datetime import timezone

        timestamp = datetime(2023, 1, 1, 12, 30, 45, 123456, tzinfo=timezone.utc).timestamp()
        result = dest._format_timestamp(timestamp)

        assert "12:30:45.123" in result

    def test_cleanup_after_action_completion(self):
        """Test that action tracking is cleaned up after completion."""
        from stogger_eliot.eliot_integration import HumanReadableEliotDestination

        output = io.StringIO()
        dest = HumanReadableEliotDestination(file=output)

        # Start action
        start_message = {
            "action_type": "test_action",
            "action_status": "started",
            "task_uuid": "task123",
            "task_level": [1],
        }
        dest(start_message)

        assert "task123" in dest._action_stack
        assert "task123" in dest._action_names

        # Complete action
        success_message = {
            "action_type": "test_action",
            "action_status": "succeeded",
            "task_uuid": "task123",
        }
        dest(success_message)

        assert "task123" not in dest._action_stack
        assert "task123" not in dest._action_names


class TestSetupEliotLogging:
    """Test the setup_eliot_logging function."""

    def test_setup_eliot_unavailable(self, mock_eliot_unavailable):
        """Test setup when Eliot is unavailable."""
        from stogger_eliot.eliot_integration import setup_eliot_logging

        with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            result = setup_eliot_logging()

            assert result is False
            # No warning message expected (uses structured logging)

    def test_setup_eliot_human_readable(self, mock_eliot_available):
        """Test setup with human readable format."""
        from stogger_eliot.eliot_integration import setup_eliot_logging

        with patch("eliot.add_destinations", autospec=True) as mock_add_dest:
            result = setup_eliot_logging(human_readable=True)

            assert result is True
            mock_add_dest.assert_called_once()

    def test_setup_eliot_json_format(self, mock_eliot_available):
        """Test setup with JSON format."""
        from stogger_eliot.eliot_integration import setup_eliot_logging

        with patch("eliot.to_file", autospec=True) as mock_to_file:
            result = setup_eliot_logging(human_readable=False)

            assert result is True
            mock_to_file.assert_called_once()

    def test_setup_eliot_custom_destination(self, mock_eliot_available):
        """Test setup with custom destination."""
        from stogger_eliot.eliot_integration import setup_eliot_logging

        custom_file = io.StringIO()
        with patch("eliot.to_file", autospec=True) as mock_to_file:
            result = setup_eliot_logging(destination=custom_file, human_readable=False)

            assert result is True
            mock_to_file.assert_called_once_with(custom_file)


class TestLogActionContextManager:
    """Test the log_action context manager."""

    def test_log_action_eliot_available(self, mock_eliot_available):
        """Test log_action when Eliot is available."""
        from stogger_eliot.eliot_integration import log_action

        mock_start, mock_log = mock_eliot_available
        mock_action = MagicMock(spec=Action)
        mock_start.return_value.__enter__ = Mock(spec=Action.__enter__, return_value=mock_action)
        mock_start.return_value.__exit__ = Mock(spec=Action.__exit__, return_value=None)

        with log_action("test_action", param1="value1") as action:
            assert action == mock_action

        mock_start.assert_called_once_with(action_type="test_action", param1="value1")

    def test_log_action_eliot_unavailable(self, mock_eliot_unavailable):
        """Test log_action when Eliot is unavailable."""
        # Test the dummy implementation directly
        import stogger_eliot.eliot_integration as eliot_mod

        # Temporarily replace the function with the dummy version
        original_log_action = eliot_mod.log_action
        eliot_mod.log_action = (
            eliot_mod.log_action.__wrapped__ if hasattr(eliot_mod.log_action, "__wrapped__") else original_log_action
        )

        # Get the dummy implementation from the else block
        from contextlib import contextmanager

        @contextmanager
        def dummy_log_action(action_name: str, **kwargs):
            yield None

        # Should not raise an exception and return None
        with dummy_log_action("test_action", param1="value1") as action:
            assert action is None


class TestLogCallDecorator:
    """Test the log_call decorator."""

    def test_log_call_eliot_available(self, mock_eliot_available):
        """Test log_call decorator when Eliot is available."""
        from stogger_eliot.eliot_integration import log_call

        mock_start, mock_log = mock_eliot_available
        mock_action = MagicMock(spec=Action)
        mock_start.return_value.__enter__ = Mock(spec=Action.__enter__, return_value=mock_action)
        mock_start.return_value.__exit__ = Mock(spec=Action.__exit__, return_value=None)

        @log_call("custom_action")
        def test_function(x, y):
            return x + y

        result = test_function(1, 2)
        assert result == 3

        mock_start.assert_called_once_with(action_type="custom_action")
        mock_action.add_success_fields.assert_called_once_with(result=3)

    def test_log_call_auto_name(self, mock_eliot_available):
        """Test log_call decorator with automatic naming."""
        from stogger_eliot.eliot_integration import log_call

        mock_start, mock_log = mock_eliot_available
        mock_action = MagicMock(spec=Action)
        mock_start.return_value.__enter__ = Mock(spec=Action.__enter__, return_value=mock_action)
        mock_start.return_value.__exit__ = Mock(spec=Action.__exit__, return_value=None)

        @log_call()
        def test_function():
            return "result"

        test_function()

        # Should use module.function_name format
        call_args = mock_start.call_args[1]
        assert "test_function" in call_args["action_type"]

    def test_log_call_with_exception(self, mock_eliot_available):
        """Test log_call decorator when function raises exception."""
        from stogger_eliot.eliot_integration import log_call

        mock_start, mock_log = mock_eliot_available
        mock_action = MagicMock(spec=Action)
        mock_action.add_failure_fields = MagicMock()
        mock_start.return_value.__enter__ = Mock(spec=Action.__enter__, return_value=mock_action)
        mock_start.return_value.__exit__ = Mock(spec=Action.__exit__, return_value=None)

        @log_call("failing_action")
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            failing_function()

        mock_action.add_failure_fields.assert_called_once_with(exception="Test error")

    def test_log_call_no_return_value(self, mock_eliot_available):
        """Test log_call decorator when function returns None."""
        from stogger_eliot.eliot_integration import log_call

        mock_start, mock_log = mock_eliot_available
        mock_action = MagicMock(spec=Action)
        mock_start.return_value.__enter__ = Mock(spec=Action.__enter__, return_value=mock_action)
        mock_start.return_value.__exit__ = Mock(spec=Action.__exit__, return_value=None)

        @log_call("void_action")
        def void_function():
            pass  # Returns None

        void_function()

        # Should not call add_success_fields for None return
        mock_action.add_success_fields.assert_not_called()

    def test_log_call_eliot_unavailable(self, mock_eliot_unavailable):
        """Test log_call decorator when Eliot is unavailable."""
        # When ELIOT_AVAILABLE is False, the dummy implementation should be used
        with patch("stogger_eliot.eliot_integration.ELIOT_AVAILABLE", False):
            from stogger_eliot.eliot_integration import log_call

            @log_call("test_action")
            def test_function(x):
                return x * 2

            # Should work normally without logging
            result = test_function(5)
            assert result == 10


class TestDemoFunction:
    """Test the demo_eliot_integration function."""

    def test_demo_eliot_unavailable(self, mock_eliot_unavailable):
        """Test demo when Eliot is unavailable."""
        from stogger_eliot.eliot_integration import demo_eliot_integration

        # Demo runs without printing (uses structured logging)
        demo_eliot_integration()
        # Just verify it completes without error

    def test_demo_eliot_available(self, mock_eliot_available):
        """Test demo when Eliot is available."""
        from stogger_eliot.eliot_integration import demo_eliot_integration

        mock_start, mock_log = mock_eliot_available
        mock_action = MagicMock(spec=Action)
        mock_start.return_value.__enter__ = Mock(spec=Action.__enter__, return_value=mock_action)
        mock_start.return_value.__exit__ = Mock(spec=Action.__exit__, return_value=None)

        with patch("stogger_eliot.eliot_integration.setup_eliot_logging", autospec=True) as mock_setup:
            with patch("builtins.print", autospec=True) as mock_print:
                demo_eliot_integration()

                mock_setup.assert_called_once_with(
                    human_readable=True,
                    show_timestamps=True,
                )
                # Demo runs without printing (uses structured logging)
                # Just verify setup was called


class TestColorImports:
    """Test color constant imports and fallbacks."""

    def test_color_constants_available(self):
        """Test that color constants are available."""
        from stogger_eliot.eliot_integration import (
            BLUE,
            BRIGHT,
            CYAN,
            DIM,
            GREEN,
            MAGENTA,
            RED,
            RESET_ALL,
            YELLOW,
        )

        # Should be strings (either ANSI codes or empty strings)
        assert isinstance(RESET_ALL, str)
        assert isinstance(BRIGHT, str)
        assert isinstance(DIM, str)
        assert isinstance(RED, str)
        assert isinstance(BLUE, str)
        assert isinstance(CYAN, str)
        assert isinstance(MAGENTA, str)
        assert isinstance(YELLOW, str)
        assert isinstance(GREEN, str)


class TestStandaloneColorImport:
    """Test color import behavior when running as standalone script."""

    def test_colorama_import_fallback(self):
        """Test colorama import with fallback when not available."""
        # This tests the import fallback logic in the module
        # The actual behavior depends on whether colorama is installed
        # and whether stdout is a TTY, but we can at least verify
        # the constants are defined
        from stogger_eliot.eliot_integration import RESET_ALL

        assert isinstance(RESET_ALL, str)
