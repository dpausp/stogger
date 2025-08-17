from pathlib import Path
import subprocess
import sys
import textwrap


def run_cli(args, cwd=None):
    exe = [sys.executable, "-m", "nicestlog", "i18n", "check"]
    return subprocess.run(exe + args, cwd=cwd, capture_output=True, text=True)


def test_cli_i18n_list_missing_and_strict(tmp_path: Path):
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
        log.info("event-b", _replace_msg="B")
        log.debug("ignored-debug", _replace_msg="dbg")
        """
        ),
        encoding="utf-8",
    )

    (trans / "en.toml").write_text('event-a = "A"\n', encoding="utf-8")

    # list-missing should output event-b only (event-a present), and return 0 (not strict)
    # Use -m nicestlog through current project by invoking python -m nicestlog within repo; in test env
    r = run_cli(
        [str(src), "--translation-dir", str(trans), "-l", "en", "--list-missing"],
        cwd=str(Path.cwd()),
    )
    assert r.returncode == 0
    missing = [line for line in r.stdout.splitlines() if line.strip()]
    assert missing == ["event-b"]

    # strict should return 1
    r2 = run_cli(
        [
            str(src),
            "--translation-dir",
            str(trans),
            "-l",
            "en",
            "--list-missing",
            "--strict",
        ],
        cwd=str(Path.cwd()),
    )
    assert r2.returncode == 1

    # Complete translations
    (trans / "en.toml").write_text('event-a = "A"\nevent-b = "B"\n', encoding="utf-8")

    # list-missing now prints nothing and returns 0
    r3 = run_cli(
        [str(src), "--translation-dir", str(trans), "-l", "en", "--list-missing"],
        cwd=str(Path.cwd()),
    )
    assert r3.returncode == 0
    assert r3.stdout.strip() == ""

    # Non-listing run should print a report and return 0
    r4 = run_cli(
        [str(src), "--translation-dir", str(trans), "-l", "en"], cwd=str(Path.cwd())
    )
    assert r4.returncode == 0
    assert "No missing keys" in r4.stdout
    # and should mention debug warning section if present
    assert "Debug events using _replace_msg" in r4.stdout
