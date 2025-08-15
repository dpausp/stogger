"""
Tests for the renderers.
"""

import pytest
import json
from nicestlog.core import ConsoleFileRenderer, JSONRenderer


def test_console_renderer_output():
    """Test the output of the ConsoleFileRenderer."""
    renderer = ConsoleFileRenderer(min_level="info")
    event_dict = {
        "event": "test-event",
        "level": "info",
        "timestamp": "2025-01-01T00:00:00Z",
        "some_key": "some_value",
    }
    output = renderer(None, "info", event_dict.copy())
    assert "test-event" in output["console"]
    assert "some_value" in output["console"]
    assert "\x1b" not in output["file"]  # No ANSI codes in file output


def test_json_renderer_output():
    """Test the output of the JSONRenderer."""
    renderer = JSONRenderer()
    event_dict = {
        "event": "test-event",
        "level": "info",
        "timestamp": "2025-01-01T00:00:00Z",
        "some_key": "some_value",
    }
    output = renderer(None, "info", event_dict.copy())

    # Both console and file outputs should be valid JSON
    console_json = json.loads(output["console"])
    file_json = json.loads(output["file"])

    assert console_json["event"] == "test-event"
    assert console_json["some_key"] == "some_value"
    assert file_json["level"] == "info"


if __name__ == "__main__":
    pytest.main([__file__])
