"""Spec validation tests for raw-output.

These tests verify the contracts from the spec decisions:
  - raw-output-rendering: _raw_output rendered without DIM/RESET_ALL, with optional prefix
  - skip-list-cleanup: KEYS_TO_SKIP_IN_JOURNAL_MESSAGE contains all required keys
  - test-strategy: ANSI-containing _raw_output preserves ANSI in console, strips from file

Spec: .agents/impl_specs/raw-output.md
"""

import io

import pytest
import structlog

from stogger._colors import DIM, RESET_ALL
from stogger.core import (
    KEYS_TO_SKIP_IN_JOURNAL_MESSAGE,
    ConsoleFileRenderer,
)


@pytest.fixture(autouse=True)
def _reset_structlog():
    """Reset structlog configuration after each test to avoid state leakage."""
    yield
    structlog.reset_defaults()


# ---------------------------------------------------------------------------
# Decision: raw-output-rendering
# ---------------------------------------------------------------------------


class TestRawOutputRendering:
    """_raw_output renders through write_fn() without DIM/RESET_ALL wrapping."""

    def test_raw_output_popped_from_event_dict(self):
        """_raw_output and _raw_output_prefix are popped, not left in event_dict."""
        renderer = ConsoleFileRenderer()
        buf = io.StringIO()
        event_dict = {
            "_raw_output": "some content",
            "_raw_output_prefix": "ty",
        }
        renderer._render_output_sections(event_dict, buf.write)

        assert "_raw_output" not in event_dict
        assert "_raw_output_prefix" not in event_dict

    def test_raw_output_no_dim_wrapping(self):
        """_raw_output content is NOT wrapped with DIM/RESET_ALL."""
        renderer = ConsoleFileRenderer()
        buf = io.StringIO()
        event_dict = {"_raw_output": "plain content"}
        renderer._render_output_sections(event_dict, buf.write)
        output = buf.getvalue()

        assert "plain content" in output
        if DIM:
            assert DIM not in output
        if RESET_ALL:
            # The raw output section itself should not add RESET_ALL after content
            assert output.endswith("plain content\n")

    def test_raw_output_with_prefix(self):
        """_raw_output_prefix wraps content with prefix()."""
        renderer = ConsoleFileRenderer()
        buf = io.StringIO()
        event_dict = {
            "_raw_output": "line1\nline2",
            "_raw_output_prefix": "ty",
        }
        renderer._render_output_sections(event_dict, buf.write)
        output = buf.getvalue()

        assert "ty: line1" in output
        assert "ty: line2" in output

    def test_raw_output_without_prefix(self):
        """_raw_output without prefix renders content directly."""
        renderer = ConsoleFileRenderer()
        buf = io.StringIO()
        event_dict = {"_raw_output": "bare output"}
        renderer._render_output_sections(event_dict, buf.write)
        output = buf.getvalue()

        assert "bare output" in output
        # No prefix marker in output
        assert ": bare output" not in output

    def test_raw_output_rendered_after_output_before_stdout(self):
        """_raw_output renders after _output and before stdout."""
        renderer = ConsoleFileRenderer()
        buf = io.StringIO()
        event_dict = {
            "_output": "first",
            "_raw_output": "middle",
            "stdout": "last",
        }
        renderer._render_output_sections(event_dict, buf.write)
        output = buf.getvalue()

        pos_output = output.index("first")
        pos_raw = output.index("middle")
        pos_stdout = output.index("last")
        assert pos_output < pos_raw < pos_stdout

    def test_raw_output_none_skipped(self):
        """_raw_output=None produces no output for that section."""
        renderer = ConsoleFileRenderer()
        buf = io.StringIO()
        event_dict = {"_raw_output": None}
        renderer._render_output_sections(event_dict, buf.write)
        output = buf.getvalue()

        # _raw_output is None, so nothing is rendered (the if-check guards)
        assert output == "" or "None" not in output


# ---------------------------------------------------------------------------
# Decision: skip-list-cleanup
# ---------------------------------------------------------------------------


class TestSkipListCleanup:
    """KEYS_TO_SKIP_IN_JOURNAL_MESSAGE contains all required keys, sorted."""

    def test_required_keys_present(self):
        """All required output-rendering keys are in the skip list."""
        required = {"_output", "_raw_output", "_raw_output_prefix", "stderr", "stdout"}
        skip_set = set(KEYS_TO_SKIP_IN_JOURNAL_MESSAGE)
        for key in required:
            assert key in skip_set, f"{key!r} missing from KEYS_TO_SKIP_IN_JOURNAL_MESSAGE"

    def test_skip_list_sorted_alphabetically(self):
        """KEYS_TO_SKIP_IN_JOURNAL_MESSAGE is sorted alphabetically."""
        assert sorted(KEYS_TO_SKIP_IN_JOURNAL_MESSAGE) == KEYS_TO_SKIP_IN_JOURNAL_MESSAGE


# ---------------------------------------------------------------------------
# Decision: test-strategy
# ---------------------------------------------------------------------------


class TestRawOutputAnsiPassthrough:
    """ANSI-containing _raw_output preserves ANSI in console, strips from file."""

    def test_ansi_preserved_in_console_stripped_from_file(self):
        """Full __call__ path: ANSI in _raw_output appears in console, not in file."""
        renderer = ConsoleFileRenderer()

        # Use a synthetic ANSI escape code that the write() closure would strip
        # if the color constants were non-empty. We mock the module-level constants
        # so the stripping branch activates.
        ansi_code = "\x1b[31m"
        ansi_reset = "\x1b[0m"
        ansi_content = f"{ansi_code}error text{ansi_reset}"

        event_dict = {
            "event": "type-errors",
            "_raw_output": ansi_content,
        }

        # Mock _colors constants in the core module so the stripping branch runs
        with (
            pytest.MonkeyPatch.context() as mp,
        ):
            mp.setattr("stogger.core.RED", ansi_code)
            mp.setattr("stogger.core.RESET_ALL", ansi_reset)
            mp.setattr("stogger.core.BRIGHT", "\x1b[1m")
            mp.setattr("stogger.core.DIM", "\x1b[2m")
            mp.setattr("stogger.core.BACKRED", "\x1b[41m")
            mp.setattr("stogger.core.BLUE", "\x1b[34m")
            mp.setattr("stogger.core.CYAN", "\x1b[36m")
            mp.setattr("stogger.core.MAGENTA", "\x1b[35m")
            mp.setattr("stogger.core.YELLOW", "\x1b[33m")
            mp.setattr("stogger.core.GREEN", "\x1b[32m")

            result = renderer(None, "info", event_dict.copy())

        # Console preserves the ANSI codes from _raw_output
        assert ansi_code in result["console"], f"ANSI code missing from console: {result['console']!r}"
        assert ansi_reset in result["console"], f"ANSI reset missing from console: {result['console']!r}"

        # File output has ANSI stripped by the write() closure
        assert ansi_code not in result["file"], f"ANSI code present in file: {result['file']!r}"
        assert ansi_reset not in result["file"], f"ANSI reset present in file: {result['file']!r}"

    def test_raw_output_content_preserved_in_both(self):
        """The actual text content appears in both console and file output."""
        renderer = ConsoleFileRenderer()
        event_dict = {
            "event": "type-errors",
            "_raw_output": "error: mismatch\nnote: see declaration",
        }
        result = renderer(None, "info", event_dict)

        assert "error: mismatch" in result["console"]
        assert "note: see declaration" in result["console"]
        assert "error: mismatch" in result["file"]
        assert "note: see declaration" in result["file"]

    def test_raw_output_with_prefix_through_full_call(self):
        """_raw_output_prefix wraps content through the full __call__ path."""
        renderer = ConsoleFileRenderer()
        event_dict = {
            "event": "component-errors",
            "_raw_output": "error: bad type",
            "_raw_output_prefix": "ty",
        }
        result = renderer(None, "info", event_dict)

        assert "ty: error: bad type" in result["console"]
        assert "ty: error: bad type" in result["file"]
