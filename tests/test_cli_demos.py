import types
from unittest.mock import Mock, patch

import pytest
import structlog
import structlog.stdlib
from stoggertools import cli


def _nosleep(*args, **kwargs):
    return None


def test_run_demos_lists_when_no_args(capsys, monkeypatch):
    monkeypatch.setattr(cli, "time", types.SimpleNamespace(sleep=_nosleep))
    cli.run_demos(feature=None, all_features=False)
    out = capsys.readouterr().out
    assert "Available stoggertools demos" in out
    assert "basic" in out


def test_run_demos_unknown_feature_exits(capsys, monkeypatch):
    monkeypatch.setattr(cli, "time", types.SimpleNamespace(sleep=_nosleep))
    with pytest.raises(SystemExit) as e:
        cli.run_demos(feature="unknown-feature", all_features=False)
    assert e.value.code == 1
    out = capsys.readouterr().out
    assert "Unknown demo" in out


@patch("stoggertools.cli.structlog.get_logger", autospec=True)
@patch("stoggertools.cli.stogger.init_logging", autospec=True)
def test_run_demos_basic_invokes_logging(
    mock_init_logging,
    mock_get_logger,
    monkeypatch,
):
    # Speed up header/separator sleeps
    monkeypatch.setattr(cli, "time", types.SimpleNamespace(sleep=_nosleep))

    mock_log = Mock(spec=structlog.stdlib.BoundLogger)
    mock_get_logger.return_value = mock_log

    cli.run_demos(feature="basic", all_features=False)

    # Expect logging across multiple levels
    assert mock_log.info.call_count >= 1  # At least one info call
    mock_log.debug.assert_called()
    mock_log.warning.assert_called()
    mock_log.error.assert_called()


def test_run_demos_all_features_dispatch(monkeypatch):
    # Patch all demo functions to simple call counters
    calls = dict.fromkeys(
        [
            "run_basic_demo",
            "run_i18n_demo",
            "run_pii_demo",
            "run_eliot_demo",
            "run_systemd_demo",
            "run_async_demo",
            "run_complete_demo",
        ],
        0,
    )

    def _mk_stub(name):
        def _stub():
            calls[name] += 1

        return _stub

    monkeypatch.setattr(cli, "time", types.SimpleNamespace(sleep=_nosleep))
    for name in calls:
        monkeypatch.setattr(cli, name, _mk_stub(name))

    cli.run_demos(feature=None, all_features=True)

    for name, count in calls.items():
        assert count == 1, f"{name} should be called once"
