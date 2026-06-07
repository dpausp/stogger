"""Verify pytest-patterns' failure reporting quality.

Run with: uv run pytest tests/experiments/test_exp03_failure_demo.py -v

This is intentionally broken: pattern expects E before W to demonstrate
the per-line failure report pytest-patterns produces. Marked xfail so
the suite stays green; remove the marker to see the diagnostic output.
"""

from __future__ import annotations

import logging
import re

import pytest
import structlog

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(s: str) -> str:
    return _ANSI_RE.sub("", s)


@pytest.fixture(autouse=True)
def _cleanup_root_logging():
    yield
    root = logging.getLogger()
    for handler in root.handlers[:]:
        handler.close()
        root.removeHandler(handler)
    config = structlog.get_config()
    factory = config.get("logger_factory")
    if hasattr(factory, "factories"):
        for sub_factory in factory.factories.values():
            if hasattr(sub_factory, "_file"):
                sub_factory._file.close()
    structlog.reset_defaults()


@pytest.mark.xfail(
    reason="Intentionally wrong order to demonstrate pytest-patterns reporting",
    strict=True,
)
def test_wrong_order_shows_per_line_diagnostic(tmp_path, capsys, monkeypatch, patterns):
    monkeypatch.delenv("JOURNAL_STREAM", raising=False)
    logdir = tmp_path / "logs"
    logdir.mkdir()

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

    console = _strip_ansi(capsys.readouterr().err)

    p = patterns.wrong_triad
    p.optional("...I...systemd-journal-active...")
    # Intentionally reversed: assert E comes before W, which it does NOT.
    p.in_order(
        "...I...app-started...version='1.0.0'...\n"
        "...E...connection-failed...host='db.example.com'...port=5432...\n"
        "...W...disk-space-low...percent=12..."
    )

    assert p == console
