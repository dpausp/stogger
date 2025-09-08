"""Tests for core logging functionality."""

import datetime
import io
import json
import logging
import os
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


# Weitere Tests...