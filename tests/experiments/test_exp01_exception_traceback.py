"""Experiment 01 — Convert weak substring assertions in the exception rendering test
to a pytest-patterns assertion that pins the full rendered shape.

Replaces
---------
/stogger/tests/test_e2e_user_perspective.py:239-260  ``test_exception_renders_traceback_on_stderr``

Original weakness
-----------------
The original test only checks four disjoint substrings::

    assert "db-connect-failed" in captured.err
    assert "ConnectionError" in captured.err
    assert "database connection refused" in captured.err
    assert "db.example.com" in captured.err

None of these pin the *renderer*'s job: that ``log.exception()`` actually
emits a Python-style traceback (header, frame lines, ``Type: message``)
on stderr. A regression that dropped the human-readable traceback and
left only the ``exception_class`` / ``exception_msg`` key-value fields
would still pass the test — exactly the "renderer drift invisible"
failure mode.

Why pytest-patterns solves it
-----------------------------
A single ``patterns.full == captured.err`` assertion pins the event's
ordering (KV line before traceback), the traceback header, the frame
shape, and the final ``ConnectionError: …`` line, while still
tolerating variable timestamps and source line numbers via ``...``
wildcards.

Failure-mode demonstration
--------------------------
A regression that changed the ``exception:`` prefix on the human-readable
traceback lines to ``[ERROR]`` (or dropped it entirely) would silently
pass the original substring assertions: the four substrings still appear
in the KV line. With the pattern assertion, the failure report is::

    assert Pattern [human_readable_traceback, kv_event, maybe_journal]:
           4 unexpected; [human_readable_traceback] - 4 unmatched.

    1 | ⚪️ maybe_journal     | 2026-... I systemd-journal-active  ...
    2 | 🟢 kv_event          | 2026-... E db-connect-failed       ...
    3 | 🟡                   | exception: Traceback (most recent call last):
    4 | 🟡                   | exception:   File "...", line ..., in ...
    5 | 🟡                   | exception:     raise ConnectionError(...)
    6 | 🟡                   | exception: ConnectionError: database connection refused

    These are the unmatched expected lines:

    🔴 human_readable_ | [ERROR] Traceback (most recent call last):
    🔴 human_readable_ | [ERROR]   File "...", line ..., in ...
    🔴 human_readable_ | [ERROR]     raise ConnectionError(...)
    🔴 human_readable_ | [ERROR] ConnectionError: database connection refused

Each rendered line is tagged with the responsible pattern name, so the
diagnosis time is seconds rather than minutes.
"""

import re

import pytest
import structlog

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(s: str) -> str:
    return _ANSI_RE.sub("", s)


@pytest.mark.e2e
def test_exception_renders_traceback_on_stderr_patterns(patterns, capsys, monkeypatch):
    """log.exception() emits KV line + full human-readable traceback on stderr."""
    monkeypatch.delenv("JOURNAL_STREAM", raising=False)

    import stogger

    stogger.init_logging(logdir=None, log_to_console=True, syslog_identifier="user-exc")
    log = structlog.get_logger("myapp")

    try:
        msg = "database connection refused"
        raise ConnectionError(msg)
    except ConnectionError:
        log.exception("db-connect-failed", host="db.example.com")

    captured = capsys.readouterr()
    output = _strip_ansi(captured.err)

    # Optional: a journal-active info event may or may not appear depending on
    # whether stogger detects a running systemd journal. Tolerate both.
    p = patterns.maybe_journal
    p.optional("...I...systemd-journal-active...Systemd journal logging active")

    # The single KV line for the error event. The event name and all four KV
    # pairs must appear on one line, in this order. ``...`` swallows the
    # variable padding spaces stogger inserts to align KV columns, and the
    # escaped-newline content of ``exception_traceback``.
    p = patterns.kv_event
    p.in_order(
        "...E...db-connect-failed..."
        "exception_class='builtins.ConnectionError'..."
        "exception_msg='database connection refused'..."
        "exception_traceback='Traceback (most recent call last):..."
        "ConnectionError: database connection refused'..."
        "host='db.example.com'..."
    )

    # The human-readable traceback rendering — this is what the original test
    # does NOT check. Continuous match: header, then at least one frame,
    # then the final ``Type: message`` line, with no gaps.
    p = patterns.human_readable_traceback
    p.continuous("""\

exception: Traceback (most recent call last):
exception:   File "...", line ..., in test_exception_renders_traceback_on_stderr_patterns
exception:     raise ConnectionError(msg)
exception: ConnectionError: database connection refused
""")

    full = patterns.full
    full.merge("maybe_journal", "kv_event", "human_readable_traceback")

    assert full == output
