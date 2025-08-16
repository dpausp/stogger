import textwrap
from pathlib import Path
from typer.testing import CliRunner

import nicestlog.cli as cli

runner = CliRunner()


def test_translator_uses_pyproject_translation_dir(tmp_path, monkeypatch):
    # Setup temp project with pyproject and custom translations dir
    proj = tmp_path
    trans = proj / "my_trans"
    trans.mkdir()

    # Create pyproject.toml pointing to our custom translations
    (proj / "pyproject.toml").write_text(
        textwrap.dedent(
            f"""
            [tool.nicestlog]
            translation_dir = "{trans.as_posix()}"
            language = "en"
            """
        ),
        encoding="utf-8",
    )

    # Provide minimal en.toml with a recognizable value
    (trans / "en.toml").write_text(
        textwrap.dedent(
            """
            [setup]
            welcome = "Hello from custom dir"
            """
        ),
        encoding="utf-8",
    )

    # Change into temp project
    monkeypatch.chdir(proj)

    # Import here to pick up the cwd-config
    from nicestlog.i18n import NicestlogTranslator

    t = NicestlogTranslator("en")
    assert t.get("welcome", "setup") == "Hello from custom dir"


def test_run_i18n_demo_passes_config_to_init(tmp_path, monkeypatch):
    # Setup temp project with pyproject (translation_dir + language)
    proj = tmp_path
    trans = proj / "trans"
    trans.mkdir()

    (proj / "pyproject.toml").write_text(
        textwrap.dedent(
            f"""
            [tool.nicestlog]
            translation_dir = "{trans.as_posix()}"
            language = "at"
            """
        ),
        encoding="utf-8",
    )

    # Minimal en/at toml to avoid noisy warnings in demo
    (trans / "en.toml").write_text("[setup]\nwelcome=\"EN\"\n", encoding="utf-8")
    (trans / "at.toml").write_text("[setup]\nwelcome=\"AT\"\n", encoding="utf-8")

    # Capture args provided to nicestlog.init_logging
    called = {"kwargs": None}

    def fake_init_logging(**kwargs):
        called["kwargs"] = kwargs
        # no-op
        return None

    monkeypatch.setattr(cli, "time", type("T", (), {"sleep": staticmethod(lambda *_: None)})())
    monkeypatch.setattr(cli.nicestlog, "init_logging", fake_init_logging)

    # Change into temp project and invoke CLI
    monkeypatch.chdir(proj)
    result = runner.invoke(cli.app, ["demo", "i18n"])  # should succeed
    assert result.exit_code == 0

    # Verify kwargs include our config
    assert called["kwargs"] is not None
    assert called["kwargs"].get("translation_dir") == trans.as_posix()
    assert called["kwargs"].get("language") == "at"
