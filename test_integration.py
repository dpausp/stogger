#!/usr/bin/env python3
"""Integration test for the enhanced ConsoleFileRenderer with SimpleFormatSettings."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from nicestlog.config import SimpleFormatSettings
from nicestlog.core import ConsoleFileRenderer


def test_console_file_renderer_with_simple_settings():
    """Test ConsoleFileRenderer with SimpleFormatSettings."""
    print("Testing ConsoleFileRenderer with SimpleFormatSettings...")

    # Test 1: Default settings
    print("\n1. Testing default settings:")
    renderer = ConsoleFileRenderer(min_level="debug")
    result = renderer(
        None,
        "info",
        {
            "event": "test_event",
            "timestamp": "2023-01-01T00:00:00Z",
            "level": "info",
        },
    )
    print(f"   Console output: {result['console']!r}")
    print(f"   File output: {result['file']!r}")

    # Test 2: With show_pid=True
    print("\n2. Testing with show_pid=True:")
    settings = SimpleFormatSettings(show_pid=True)
    renderer = ConsoleFileRenderer(min_level="debug", settings=settings)
    result = renderer(
        None,
        "info",
        {
            "event": "test_event",
            "timestamp": "2023-01-01T00:00:00Z",
            "level": "info",
            "pid": 12345,
        },
    )
    print(f"   Console output: {result['console']!r}")
    assert "[12345]" in result["console"]

    # Test 3: With show_logger_brackets=True
    print("\n3. Testing with show_logger_brackets=True:")
    settings = SimpleFormatSettings(show_logger_brackets=True)
    renderer = ConsoleFileRenderer(min_level="debug", settings=settings)
    result = renderer(
        None,
        "info",
        {
            "event": "test_event",
            "timestamp": "2023-01-01T00:00:00Z",
            "level": "info",
            "logger": "test_logger",
        },
    )
    print(f"   Console output: {result['console']!r}")
    assert "[test_logger]" in result["console"]

    # Test 4: With timestamp_format="iso_no_z"
    print("\n4. Testing with timestamp_format='iso_no_z':")
    settings = SimpleFormatSettings(timestamp_format="iso_no_z")
    renderer = ConsoleFileRenderer(min_level="debug", settings=settings)
    result = renderer(
        None,
        "info",
        {
            "event": "test_event",
            "timestamp": "2023-01-01T00:00:00Z",
            "level": "info",
        },
    )
    print(f"   Console output: {result['console']!r}")
    assert "2023-01-01T00:00:00 " in result["console"]
    assert "2023-01-01T00:00:00Z" not in result["console"]

    # Test 5: With custom pad_event_width
    print("\n5. Testing with custom pad_event_width:")
    settings = SimpleFormatSettings(pad_event_width=20)
    renderer = ConsoleFileRenderer(min_level="debug", settings=settings)
    result = renderer(
        None,
        "info",
        {
            "event": "test_event",
            "timestamp": "2023-01-01T00:00:00Z",
            "level": "info",
        },
    )
    print(f"   Console output: {result['console']!r}")

    print("\nAll tests passed!")


if __name__ == "__main__":
    test_console_file_renderer_with_simple_settings()
