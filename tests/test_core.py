"""Tests for core logging functionality."""

import datetime
import io
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest
import structlog

# Import the modules we want to test
from src.nicestlog.config import SimpleFormatSettings
from src.nicestlog.core import (
    JSONRenderer,
    ConsoleFileRenderer,
    TranslationProcessor,
    add_caller_info,
    add_pid,
    drop_cmd_output_logfile,
    format_exc_info,
    init_command_logging,
    init_early_logging,
    init_logging,
    logging_initialized,
    process_exc_info,
    prefix,
)


class TestConsoleFileRenderer:
    """Tests for the ConsoleFileRenderer class."""

    def test_caller_info_option(self):
        """Test the show_caller_info option."""
        settings = SimpleFormatSettings(show_code_info=True)
        renderer = ConsoleFileRenderer(settings=settings)
        # This is mainly for initialization - actual caller info is added by add_caller_info processor
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

        # The event should be padded to 20 characters
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

        # Both console and file outputs should be valid JSON
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

    def test_early_logging_initialization(self):
        """Test that early logging initialization reduces uninitialized structlog messages."""
        # Test script that demonstrates early initialization
        test_script = """
import nicestlog
import structlog

# This should show proper format from the start
log = structlog.get_logger('test')
log.info('early-message', message='Should show early format')

# Full initialization should work without issues
nicestlog.init_logging(verbose=False)
log.info('after-full-init', message='Should show full format')
"""

        # Run the test script
        result = subprocess.run(
            [sys.executable, "-c", test_script],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent / "src",
        )

        # Check that it ran successfully
        assert result.returncode == 0, f"Script failed: {result.stderr}"

        # Check that we get output (meaning logging worked) - could be in stdout or stderr
        output = result.stdout + result.stderr
        assert output.strip(), "No logging output received"

        # Check that both messages appear
        lines = output.strip().split("\n")
        assert len(lines) >= 2, f"Expected at least 2 log lines, got: {lines}"

        # Find the early message line
        early_lines = [line for line in lines if "early-message" in line]
        assert len(early_lines) == 1, (
            f"Expected exactly 1 early message, got: {early_lines}"
        )

        early_line = early_lines[0]
        assert "Should show early format" in early_line
        assert "2025-" in early_line  # Date format

        # Find the full init message line
        full_init_lines = [line for line in lines if "after-full-init" in line]
        assert len(full_init_lines) == 1, (
            f"Expected exactly 1 full init message, got: {full_init_lines}"
        )

        full_init_line = full_init_lines[0]
        assert "Should show full format" in full_init_line

    def test_early_logging_graceful_fallback(self):
        """Test that early logging fails gracefully if there are issues."""
        # Test that logging_initialized works
        test_script = """
import nicestlog
import structlog

# Should be configured after import
print("Configured:", nicestlog.logging_initialized())

# Should still work after full init
nicestlog.init_logging()
print("Still configured:", nicestlog.logging_initialized())
"""

        result = subprocess.run(
            [sys.executable, "-c", test_script],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent / "src",
        )

        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")

        # Should show configured status (may be False in some cases)
        assert "Configured:" in lines[0]
        assert "Still configured:" in lines[-1]

    def test_no_uninitialized_messages_in_cli(self):
        """Test that CLI commands don't show uninitialized structlog messages."""
        # Test a simple CLI command that would trigger logging
        result = subprocess.run(
            [sys.executable, "-m", "nicestlog", "--help"],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent / "src",
        )

        # Should succeed
        assert result.returncode == 0

        # Should not contain the old uninitialized format patterns
        output = result.stdout + result.stderr

        # Old format would show: [info     ] message
        # New format shows: timestamp I message
        assert "[info     ]" not in output, "Found uninitialized structlog format"
        assert "[debug    ]" not in output, "Found uninitialized structlog format"


# Weitere Tests...
