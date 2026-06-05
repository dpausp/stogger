"""Experiment 02 — pytest-patterns adoption candidate.

Replaces the weak assertion block at:
    /stogger/tests/test_core.py:305-335
    TestRenderOutputSections.test_render_output_sections_all_types

Original weakness:
    13 individual `assert "..." in output` checks, ~half tautological.
    Specific gaps:
      - "ty" in output      — substring appears in many words; not the prefix label.
      - "out" in output     — tautological: "out" appears in "stdout", "out: ",
                               "program output", and even the test event_dict itself.
      - "err" in output     — tautological: "err" appears in "stderr".
      - "stack" in output   — weak substring; not pinned to "stack: " label.
      - "exception" in output — weak; not pinned to "exception: " label.
      - Order of sections NOT asserted — renderer could swap stdout/stderr or
        move the separator "="*79 anywhere and the test would still pass.
      - "=" * 79 in output  — separator existence asserted but NOT its position
                               between stack and exception_traceback.

Why pytest-patterns solves it:
    Declarative `in_order` pins the exact section sequence end-to-end, and
    section-label lines (`out: standard out`, `stack: stack trace here`,
    `exception: traceback details`) are now structurally required, not
    reduced to substrings that happen to live elsewhere in the output.

Failure-mode demonstration:
    With an intentionally broken pattern (err/out swapped, separator omitted,
    exception label missing), pytest-patterns produces this report — note how
    each line is annotated with its match status and which pattern matched it:

        1 | 🟢 sections        | > cmd> ls -la
        2 | ⚪️ sections        |
        3 | 🟡                 | program output
        4 | ⚪️ sections        |
        5 | 🟡                 | ty: raw ansi output
        6 | ⚪️ sections        |
        7 | ⚪️ sections        | out:
        8 | ⚪️ sections        | out: standard out
        9 | ⚪️ sections        | out:
       10 | ⚪️ sections        | err:
       11 | 🟢 sections        | err: standard error
       12 | ⚪️ sections        | err:
       13 | 🟡                 | stack: stack trace here
       14 | 🟡                 | ===============================================================================
       15 | ⚪️ sections        |
       16 | 🟡                 | exception: traceback details

       These are the unmatched expected lines:

       🔴 sections        | out: standard out
       🔴 sections        | stack: stack trace here

    The original 13-substring test would have PASSED on this broken renderer
    output, because every substring ("out", "err", "stack", "exception", "="*79,
    "traceback details", ...) is still present. pytest-patterns makes the
    structural breakage immediately legible.
"""

import io
import re

from stogger.core import ConsoleFileRenderer

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(s: str) -> str:
    """Remove ANSI SGR escape sequences so line structure is matchable."""
    return _ANSI_RE.sub("", s)


def test_render_output_sections_all_types(patterns):
    """All output section types rendered in the correct order with labels.

    This is the pytest-patterns version of
    TestRenderOutputSections.test_render_output_sections_all_types.
    """
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
    output = _strip_ansi(buf.getvalue())

    # Tolerate (do not require) things the renderer adds around the content:
    #   - blank lines between sections
    #   - the `prefix()` wrapper lines (`out: `, `err: `) that surround each
    #     multi-line stdout/stderr block
    p = patterns.sections
    p.optional("<empty-line>")
    p.optional("out: ...")
    p.optional("err: ...")

    # Pin the strict order of section content AND the position of the
    # "="*79 separator between the stack and exception sections (which the
    # original substring test left completely unpinned).
    p.in_order(
        """\
> cmd> ls -la
program output
ty: raw ansi output
out: standard out
err: standard error
stack: stack trace here
===============================================================================
exception: traceback details
"""
    )

    assert p == output
