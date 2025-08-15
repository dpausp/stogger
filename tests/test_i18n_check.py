import textwrap
from pathlib import Path

import pytest

from nicestlog.i18n_check import (
    find_required_translation_keys,
    load_translation_keys,
    check_translations,
    run_i18n_check_cli,
)


def write(p: Path, content: str) -> Path:
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


def test_find_required_translation_keys_detects_events_and_msg_keys(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()

    # File with various logging invocations
    write(
        src / "a.py",
        """
        import structlog
        log = structlog.get_logger()
        log.info("event-a", _replace_msg="A {val}", val=1)
        log.warning("event-b", something=1, _replace_msg="B")
        # Explicit _msg_key usage (should be detected)
        log.info("ignored-event", _msg_key="custom.key")
        """,
    )

    events, msg_keys = find_required_translation_keys([src])

    assert "event-a" in events
    assert "event-b" in events
    # The plain event without _replace_msg should not be in events
    assert "ignored-event" not in events

    # _msg_key should be detected
    assert "custom.key" in msg_keys


def test_load_translation_keys_ignores_sections(tmp_path: Path):
    trans_dir = tmp_path / "translations"
    trans_dir.mkdir()
    tfile = trans_dir / "en.toml"

    write(
        tfile,
        """
        app-startup = "Start app"
        request-complete = "Done"

        [setup]
        welcome = "hi"
        """,
    )

    keys = load_translation_keys(tfile)
    assert "app-startup" in keys
    assert "request-complete" in keys
    # Section keys should not be considered TranslationProcessor entries
    assert "setup" not in keys


def test_check_translations_reports_missing_and_extra(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    write(
        src / "app.py",
        """
        import structlog
        log = structlog.get_logger()
        log.info("event-x", _replace_msg="x")
        log.info("event-y", _replace_msg="y {n}", n=1)
        log.info("e", _msg_key="msg.special")
        """,
    )

    trans_dir = tmp_path / "translations"
    trans_dir.mkdir()
    tfile = trans_dir / "en.toml"
    # Intentionally miss event-y and msg.special; add an extra key
    write(
        tfile,
        """
        event-x = "Alpha"
        extra-unused = "Z"
        """,
    )

    report = check_translations([src], trans_dir, language="en")

    assert "missing_keys" in report
    missing = set(report["missing_keys"])  # type: ignore[index]
    extra = set(report["extra_keys"])  # type: ignore[index]

    assert {"event-y", "msg.special"}.issubset(missing)
    assert "extra-unused" in extra


def test_run_i18n_check_cli_strict_exit_code(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    write(
        src / "main.py",
        """
        import structlog
        log = structlog.get_logger()
        log.info("event-a", _replace_msg="a")
        log.info("event-b", _replace_msg="b")
        """,
    )

    trans_dir = tmp_path / "translations"
    trans_dir.mkdir()
    tfile = trans_dir / "en.toml"

    # Missing event-b
    write(tfile, "event-a = \"A\"\n")

    code = run_i18n_check_cli(path=str(src), translation_dir=str(trans_dir), language="en", strict=True)
    assert code == 1

    # Now make it complete
    write(tfile, "event-a = \"A\"\nevent-b = \"B\"\n")
    code2 = run_i18n_check_cli(path=str(src), translation_dir=str(trans_dir), language="en", strict=True)
    assert code2 == 0
