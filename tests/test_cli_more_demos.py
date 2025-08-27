import types
from unittest.mock import Mock
from typer.testing import CliRunner

import nicestlog.cli as cli

runner = CliRunner()


def _nosleep(*args, **kwargs):
    return None


def test_cli_demo_async_invokes_function(monkeypatch):
    called = {"count": 0}

    def stub():
        called["count"] += 1

    monkeypatch.setattr(cli, "run_async_demo", stub)
    result = runner.invoke(cli.app, ["tools", "demo", "async"])
    assert result.exit_code == 0
    assert called["count"] == 1


def test_cli_demo_complete_invokes_function(monkeypatch):
    called = {"count": 0}

    def stub():
        called["count"] += 1

    monkeypatch.setattr(cli, "run_complete_demo", stub)
    result = runner.invoke(cli.app, ["tools", "demo", "complete"])
    assert result.exit_code == 0
    assert called["count"] == 1


def test_run_async_demo_behavior(monkeypatch, capsys):
    # speed up sleeps and control time progression
    times = iter([0.0, 0.1, 0.2, 0.25])
    monkeypatch.setattr(
        cli, "time", types.SimpleNamespace(sleep=_nosleep, time=lambda: next(times))
    )

    # mock nicestlog init
    monkeypatch.setattr(cli.nicestlog, "init_logging", lambda **kwargs: None)

    # mock structlog logger
    mock_log = Mock()
    monkeypatch.setattr(cli.structlog, "get_logger", lambda: mock_log)

    cli.run_async_demo()
    out = capsys.readouterr().out

    # should print durations
    assert "Sync logging:" in out
    assert "Async logging:" in out
    assert "Speedup:" in out

    # logger.info should be called in both loops
    assert any(
        call.args and call.args[0] in ("sync-message", "async-message")
        for call in mock_log.info.call_args_list
    )


def test_run_complete_demo_smoke(monkeypatch, capsys):
    # Avoid real sleeps
    monkeypatch.setattr(cli, "time", types.SimpleNamespace(sleep=_nosleep))

    # Prevent real logging initialization
    monkeypatch.setattr(cli.nicestlog, "init_logging", lambda **kwargs: None)

    # Mock logger
    mock_log = Mock()
    monkeypatch.setattr(cli.structlog, "get_logger", lambda: mock_log)

    cli.run_complete_demo()
    out = capsys.readouterr().out

    # Should print these section headers and bullet list
    assert "Complete Application Example" in out
    assert "This demonstrates:" in out

    # Should have logged startup/request messages
    assert mock_log.info.called
