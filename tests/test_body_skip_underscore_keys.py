"""Tests for body-skip-underscore-keys spec.

SPEC: .agents/impl_specs/body-skip-underscore-keys.md

Covers two decisions:

1. underscore-keys-excluded-from-body
   The fallback KV body renderer in ConsoleFileRenderer MUST skip all
   event_dict keys whose name starts with `_`. Output-section stages that
   consume those keys remain unchanged.

2. underscore-keys-excluded-from-replace-msg-interpolation
   When building the keyword arguments for the replace-message formatter,
   keys whose name starts with `_` MUST be excluded — internal fields must
   not be reachable from user-controlled format strings.

Tests exercise the full ConsoleFileRenderer pipeline via __call__ (the
public processor entry point) and use the ``file`` target which has ANSI
escape codes stripped, leaving the bare key=value structure matchable.
"""

from stogger.core import ConsoleFileRenderer

# Marker strings used in event dicts. Chosen to be unique so that substring
# matches on rendered output cannot collide with keys, values, or labels
# emitted by other render stages.
_BODY_MARKER_KEY = "_internal_marker_xyz"
_BODY_MARKER_VAL = "value_should_not_render_xyz"
_OUTPUT_VAL = "program_output_marker_abc"


class TestUnderscoreKeysExcludedFromBody:
    """SPEC: body-skip-underscore-keys::underscore-keys-excluded-from-body.

    The fallback KV body renderer MUST skip all event_dict keys whose name
    starts with `_`. The dedicated render stages that consume these keys
    remain unchanged.
    """

    def test_custom_underscore_key_silently_dropped_from_body(self):
        """User-supplied _-prefixed key disappears from fallback body.

        SPEC consequence: "A caller passing a custom `_foo` key without
        `_replace_msg` will see that key silently dropped from the body."
        """
        renderer = ConsoleFileRenderer()
        event_dict = {
            "event": "test-event",
            "level": "info",
            "timestamp": "2025-01-01T00:00:00Z",
            _BODY_MARKER_KEY: _BODY_MARKER_VAL,
            "regular_key": "regular_value",
        }
        result = renderer(None, "info", event_dict)

        # The body renders keys as ``key='value'``. Neither the key nor its
        # value must appear in the rendered output.
        assert f"{_BODY_MARKER_KEY}=" not in result["file"]
        assert _BODY_MARKER_VAL not in result["file"]
        assert _BODY_MARKER_KEY not in result["console"]
        assert _BODY_MARKER_VAL not in result["console"]

    def test_output_section_key_not_duplicated_in_body(self):
        """``_output`` is consumed only by the output-section stage.

        SPEC: "renders underscore-prefixed event_dict keys twice when no
        `_replace_msg` is provided: once as generic key=value pairs in the
        fallback body, and again in the dedicated output-section stage".

        After impl, ``_output='...'`` MUST NOT appear in the body section,
        but the output section MUST still render the value on its own line.
        """
        renderer = ConsoleFileRenderer()
        event_dict = {
            "event": "test-event",
            "level": "info",
            "timestamp": "2025-01-01T00:00:00Z",
            "_output": _OUTPUT_VAL,
        }
        result = renderer(None, "info", event_dict)

        # Body would render this as ``_output='program_output_marker_abc'``;
        # that substring must be absent.
        assert "_output=" not in result["file"]
        # The output-section stage still emits the value on its own line,
        # indented and surrounded by blank lines.
        assert _OUTPUT_VAL in result["file"]

    def test_raw_output_section_key_not_in_body(self):
        """``_raw_output`` and ``_raw_output_prefix`` also excluded from body."""
        renderer = ConsoleFileRenderer()
        event_dict = {
            "event": "test-event",
            "level": "info",
            "timestamp": "2025-01-01T00:00:00Z",
            "_raw_output": "raw_chunk_xyz",
            "_raw_output_prefix": "pfx",
        }
        result = renderer(None, "info", event_dict)

        assert "_raw_output=" not in result["file"]
        assert "_raw_output_prefix=" not in result["file"]
        # Output section still consumes both keys.
        assert "raw_chunk_xyz" in result["file"]
        assert "pfx" in result["file"]

    def test_output_value_appears_exactly_once(self):
        """No duplication: the output value occurs only via the output-section.

        Before the spec fix, ``_output='X'`` shows up once in the body and
        again in the output section (count = 2). After the fix, the value
        appears only via the output-section stage (count = 1).
        """
        renderer = ConsoleFileRenderer()
        event_dict = {
            "event": "test-event",
            "level": "info",
            "timestamp": "2025-01-01T00:00:00Z",
            "_output": _OUTPUT_VAL,
        }
        result = renderer(None, "info", event_dict)

        assert result["file"].count(_OUTPUT_VAL) == 1, (
            f"Expected {_OUTPUT_VAL!r} to appear exactly once in rendered "
            f"output (consumed only by output-section stage), found "
            f"{result['file'].count(_OUTPUT_VAL)} times.\n"
            f"Output was:\n{result['file']}"
        )

    def test_regular_keys_still_rendered_in_body(self):
        """Regression: non-underscore keys still appear in fallback body."""
        renderer = ConsoleFileRenderer()
        event_dict = {
            "event": "test-event",
            "level": "info",
            "timestamp": "2025-01-01T00:00:00Z",
            "user_id": 42,
            "session": "abc",
        }
        result = renderer(None, "info", event_dict)

        assert "user_id=42" in result["file"]
        assert "session='abc'" in result["file"]

    def test_only_underscore_keys_remaining_yields_empty_body(self):
        """Body produces no KV pairs when all remaining keys are _-prefixed.

        Header (timestamp/level/event) is still emitted; output section
        still consumes its keys. But the body region between them is empty.
        """
        renderer = ConsoleFileRenderer()
        event_dict = {
            "event": "test-event",
            "level": "info",
            "timestamp": "2025-01-01T00:00:00Z",
            "_output": _OUTPUT_VAL,
        }
        result = renderer(None, "info", event_dict)

        # Header is present.
        assert "test-event" in result["file"]
        assert "2025-01-01T00:00:00Z" in result["file"]
        # Output section value still emitted.
        assert _OUTPUT_VAL in result["file"]
        # No body fragment of the form ``key=`` exists for _-prefixed keys.
        # The first line must not contain ``=`` outside of the timestamp
        # (which contains ``:`` and ``-``, not ``=``). Look at the first
        # line specifically — that is where the body would render.
        first_line = result["file"].split("\n", 1)[0]
        # ``=`` is the body's separator. After the fix, the first line is
        # only header + padded event, no ``key=`` body fragment.
        assert "=" not in first_line, (
            f"First line should be header-only when all body keys are "
            f"_-prefixed, but found '=' indicating body KV rendering.\n"
            f"First line: {first_line!r}"
        )


class TestUnderscoreKeysExcludedFromReplaceMsg:
    """SPEC: body-skip-underscore-keys::underscore-keys-excluded-from-replace-msg-interpolation.

    When building the keyword arguments for the replace-message formatter,
    keys whose name starts with `_` MUST be excluded.
    """

    def test_replace_msg_does_not_interpolate_output_key(self, log):
        """``{ _output }`` in format string falls back to <missing>.

        Internal output-section keys must not be reachable from user-
        controlled format strings. The PartialFormatter logs
        ``format-field-missing`` when it cannot resolve a field.
        """
        renderer = ConsoleFileRenderer()
        event_dict = {
            "event": "test-event",
            "level": "info",
            "timestamp": "2025-01-01T00:00:00Z",
            "_replace_msg": "got {_output}",
            "_output": _OUTPUT_VAL,
        }
        result = renderer(None, "info", event_dict)

        # The body shows the formatted _replace_msg. ``_output`` must NOT
        # have been interpolated — the formatter reports ``<missing>``.
        assert "got <missing>" in result["file"]
        assert f"got {_OUTPUT_VAL}" not in result["file"]
        # The output-section stage still consumes ``_output`` normally.
        assert _OUTPUT_VAL in result["file"]
        # Formatter emitted the diagnostic event with the field name.
        assert log.has("format-field-missing")

    def test_replace_msg_does_not_interpolate_custom_underscore_key(self):
        """Any user-supplied ``_foo`` is unreachable from _replace_msg."""
        renderer = ConsoleFileRenderer()
        event_dict = {
            "event": "test-event",
            "level": "info",
            "timestamp": "2025-01-01T00:00:00Z",
            "_replace_msg": "value is {_custom_internal}",
            "_custom_internal": "leaked_via_format",
        }
        result = renderer(None, "info", event_dict)

        assert "value is <missing>" in result["file"]
        assert "leaked_via_format" not in result["file"]

    def test_replace_msg_still_interpolates_regular_keys(self):
        """Regression: non-underscore keys still work in _replace_msg."""
        renderer = ConsoleFileRenderer()
        event_dict = {
            "event": "test-event",
            "level": "info",
            "timestamp": "2025-01-01T00:00:00Z",
            "_replace_msg": "user={user_id} session={session}",
            "user_id": 42,
            "session": "abc",
        }
        result = renderer(None, "info", event_dict)

        assert "user=42" in result["file"]
        assert "session=abc" in result["file"]

    def test_replace_msg_with_mixed_underscore_and_regular_keys(self):
        """Mixed format string: regular keys interpolate, _-prefixed do not.

        Verifies that filtering applies per-key, not all-or-nothing.
        """
        renderer = ConsoleFileRenderer()
        event_dict = {
            "event": "test-event",
            "level": "info",
            "timestamp": "2025-01-01T00:00:00Z",
            "_replace_msg": "ok={ok} internal={_internal}",
            "ok": "yes",
            "_internal": "should_not_leak",
        }
        result = renderer(None, "info", event_dict)

        assert "ok=yes" in result["file"]
        assert "internal=<missing>" in result["file"]
        assert "should_not_leak" not in result["file"]
