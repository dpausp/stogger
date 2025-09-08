from pathlib import Path
import subprocess
import sys
import textwrap


def run_cli(args, cwd=None):
    exe = [sys.executable, "-m", "nicestlog", "tools", "i18n", "check"]
    return subprocess.run(
        exe + args,
        check=False,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def test_cli_fail_on_extra_in_list_and_full(tmp_path: Path):
    src = tmp_path / "src"
    trans = tmp_path / "translations"
    src.mkdir()
    trans.mkdir()

    (src / "m.py").write_text(
        textwrap.dedent(
            """
        import structlog
        log = structlog.get_logger()
        log.info("event-a")
        """,
        ),
        encoding="utf-8",
    )

    # event-a present, but extra key exists
    (trans / "en.toml").write_text(
        'event-a = "A"\nextra-unused = "Z"\n',
        encoding="utf-8",
    )

    # list-missing mode: prints nothing, but with --fail-on-extra should return 1
    r = run_cli(
        [
            str(src),
            "--translation-dir",
            str(trans),
            "-l",
            "en",
            "--list-missing",
            "--fail-on-extra",
        ],
        cwd=str(Path.cwd()),
    )
    assert r.returncode == 1
    assert r.stdout.strip() == ""

    # full report: should mention extra keys and return 1 when --fail-on-extra
    r2 = run_cli(
        [str(src), "--translation-dir", str(trans), "-l", "en", "--fail-on-extra"],
        cwd=str(Path.cwd()),
    )
    assert r2.returncode == 1
    assert "Extra keys" in r2.stdout
