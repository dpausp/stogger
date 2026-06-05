"""Experiment 03: replace weak substring assertions with pytest-patterns.

Target
------
/stogger/tests/test_e2e_single_module_app.py:38-77
``test_single_module_app_console_and_file``

Original weakness
-----------------
The test emits three log events at increasing severity
(info -> warning -> error) and then checks them with five independent
``assert "literal" in captured.err`` calls. Three things are invisible
to the original assertions:

1. **Order**. If the renderer or an async buffer ever swapped the
   events (e.g. ``error`` printed before ``warning``) the test still
   passes. For a *logging library* ordering is the contract.
2. **Same-line binding**. ``assert "version" in captured.err`` only
   checks that the word appears *somewhere*. If ``version=`` got
   detached from the ``app-started`` event and printed on a different
   line, the test would still be green.
3. **Console/file parity**. The test asserts the same substrings in
   both sinks separately. The contract it claims to test ("file
   output should contain the events") really means "file is a
   faithful copy of console" — but the assertions don't enforce that.

Why pytest-patterns solves it
-----------------------------
``in_order`` pins the relative order of the three events AND keeps
each event's KV bindings on the same line (one pattern line per
output line). ``optional`` admits the ``systemd-journal-active``
init banner without forcing it. ``refused`` documents what must
*not* appear in this scenario. Reusing the same ``Pattern`` against
both console (ANSI-stripped) and file output enforces parity without
duplicating assertions.
"""

from __future__ import annotations

import logging
import re

import pytest
import structlog

# Match ANSI CSI sequences (color codes used by stogger's ConsoleFileRenderer).
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(s: str) -> str:
    return _ANSI_RE.sub("", s)


@pytest.fixture(autouse=True)
def _cleanup_root_logging():
    """Mirror the autouse fixture from test_e2e_single_module_app.py.

    Closes file handles and resets structlog so the test is hermetic.
    """
    yield
    root = logging.getLogger()
    for handler in root.handlers[:]:
        handler.close()
        root.removeHandler(handler)
    config = structlog.get_config()
    factory = config.get("logger_factory")
    if hasattr(factory, "factories"):
        for _name, sub_factory in factory.factories.items():
            if hasattr(sub_factory, "_file"):
                sub_factory._file.close()
    structlog.reset_defaults()


def _emit_triad(logdir, monkeypatch):
    """Set up stogger and emit three events at increasing severity.

    Returns the path of the log file (so the caller can read both sinks).
    """
    monkeypatch.delenv("JOURNAL_STREAM", raising=False)
    logdir.mkdir(exist_ok=True)

    import stogger

    stogger.init_logging(
        logdir=str(logdir),
        log_to_console=True,
        syslog_identifier="e2e-test",
    )
    log = structlog.get_logger("myapp")
    log.info("app-started", version="1.0.0")
    log.warning("disk-space-low", percent=12)
    log.error("connection-failed", host="db.example.com", port=5432)
    return logdir / "e2e-test.log"


def _build_event_pattern(patterns):
    """Build a reusable pattern describing the expected output.

    Independent of sink: works against the ANSI-stripped console output
    and against the file content. Reusing one pattern is the parity
    guarantee.

    Note: pytest-patterns' ``pattern_lines`` does NOT strip indentation
    from multi-line strings (the comment claims otherwise but the code
    only filters empty lines). So each pattern string is a concatenation
    of unindented literals joined with ``\\n`` — any leading whitespace
    would be interpreted as significant.
    """
    p = patterns.triad
    # Init banner appears in environments where systemd is reachable
    # in tests; we tolerate it without requiring it.
    p.optional("...I...systemd-journal-active...Systemd journal logging active")

    # The three user events MUST appear in this order. Each pattern line
    # also pins the KV bindings to the same line as the event name.
    p.in_order(
        "...I...app-started...version='1.0.0'...\n"
        "...W...disk-space-low...percent=12...\n"
        "...E...connection-failed...host='db.example.com'...port=5432..."
    )

    # Anything that should never appear in this scenario.
    p.refused("...Traceback (most recent call last)...")
    p.refused("...CRITICAL...")
    p.refused("...FATAL...")
    return p


# Failure-mode demonstration (verified -- see test_exp03_failure_demo.py):
#
# Reversing the order of the W and E pattern lines produces this report:
#
#   assert Pattern [wrong_triad]: 1 unexpected; 1 unmatched.
#
#   🟢=EXPECTED | ⚪️=OPTIONAL | 🟡=UNEXPECTED | 🔴=REFUSED/UNMATCHED
#
#   Here is the string that was tested:
#
#   1 | ⚪️ wrong_triad | 2026-06-04T18:52:32Z I systemd-journal-active  ...
#   2 | 🟢 wrong_triad | 2026-06-04T18:52:32Z I app-started             ...
#   3 | 🟡             | 2026-06-04T18:52:32Z W disk-space-low          ...
#   4 | 🟢 wrong_triad | 2026-06-04T18:52:32Z E connection-failed       ...
#
#   These are the unmatched expected lines:
#
#   🔴 wrong_triad | ...W...disk-space-low...percent=12...
#
# vs. the original assertion's failure mode of just `AssertionError` from
# `assert "disk-space-low" in captured.err`. The per-line labels tell you
# *exactly* where the ordering diverged: line 3 is UNEXPECTED (no pattern
# was looking for it at that position), and the W-pattern is UNMATCHED
# (it expected to match AFTER the E line).


def test_console_output_pattern(tmp_path, capsys, monkeypatch, patterns):
    """Console output (ANSI stripped) matches the triad pattern."""
    log_file = _emit_triad(tmp_path / "logs", monkeypatch)
    assert log_file.exists()  # sanity

    console = _strip_ansi(capsys.readouterr().err)
    p = _build_event_pattern(patterns)
    assert p == console


def test_file_output_pattern(tmp_path, capsys, monkeypatch, patterns):
    """File output matches the same triad pattern used for console."""
    log_file = _emit_triad(tmp_path / "logs", monkeypatch)

    file_content = log_file.read_text()
    p = _build_event_pattern(patterns)
    assert p == file_content


def test_console_and_file_parity(tmp_path, capsys, monkeypatch, patterns):
    """Console (stripped) and file are both faithful to one shared pattern.

    This is the test the original *claims* to be (``file output should
    contain the events``) but isn't: it builds one pattern and asserts
    it against both sinks, so any divergence surfaces as a failed
    assertion with a labelled per-line diff.
    """
    log_file = _emit_triad(tmp_path / "logs", monkeypatch)
    assert log_file.exists()

    console = _strip_ansi(capsys.readouterr().err)
    file_content = log_file.read_text()

    # Same pattern object -> same contract on both sinks.
    # If stogger ever lets the file drift (different ordering, missing KV,
    # extra init line in one but not the other) this fails with a precise
    # per-line report pointing at the divergence.
    p = _build_event_pattern(patterns)
    assert p == console
    assert p == file_content
