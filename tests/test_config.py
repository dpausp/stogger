"""Tests for the NicestLogConfig class."""

from pathlib import Path
import tempfile
from unittest.mock import MagicMock, patch
import logging

import pytest

from stogger.config import NicestLogConfig
from stogger.factory import build_shared_processors, configure_stdlib_logging


@pytest.fixture
def create_pyproject_toml():
    """A pytest fixture to create a temporary pyproject.toml for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)
        pyproject_path = config_dir / "pyproject.toml"
        with open(pyproject_path, "w") as f:
            f.write("""
[tool.stogger]
verbose = true
logdir = "/tmp/logs"
syslog_identifier = "test-app"
language = "fr"
""")
        with patch("pathlib.Path.cwd", return_value=config_dir):
            yield


def test_config_loading_from_file(create_pyproject_toml):
    """Test that config is correctly loaded from pyproject.toml."""
    config = NicestLogConfig()
    assert config.verbose is True
    assert config.logdir == Path("/tmp/logs")
    assert config.syslog_identifier == "test-app"
    assert config.language == "fr"
    assert config.log_to_console is True  # Default value


def test_config_kwargs_override_file(create_pyproject_toml):
    """Test that kwargs provided to the constructor override file settings."""
    config = NicestLogConfig(
        verbose=False,
        syslog_identifier="override-app",
        log_to_console=False,
    )
    assert config.verbose is False
    assert config.syslog_identifier == "override-app"
    assert config.log_to_console is False
    assert config.logdir == Path("/tmp/logs")  # This should still come from the file


def test_config_defaults_when_no_file():
    """Test that the config falls back to defaults when no file exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("pathlib.Path.cwd", return_value=Path(tmpdir)):
            config = NicestLogConfig()
            assert config.verbose is False
            assert config.logdir is None
            assert config.syslog_identifier == "stogger"
            assert config.language == "en"


@patch("logging.basicConfig")
def test_sync_logging_setup(mock_basic_config):
    """Test that synchronous logging sets up basicConfig directly."""
    config = NicestLogConfig(async_logging=False, log_to_console=True)
    processors = build_shared_processors(config)
    configure_stdlib_logging(config, processors)

    mock_basic_config.assert_called_once()
    assert "handlers" in mock_basic_config.call_args.kwargs
    assert any(isinstance(h, logging.StreamHandler) for h in mock_basic_config.call_args.kwargs["handlers"])


@patch("logging.handlers.QueueListener")
@patch("logging.getLogger")
def test_async_logging_setup(mock_get_logger, mock_listener):
    """Test that asynchronous logging sets up a QueueListener."""
    mock_root_logger = MagicMock()
    mock_get_logger.return_value = mock_root_logger

    config = NicestLogConfig(async_logging=True, log_to_console=True)
    processors = build_shared_processors(config)
    configure_stdlib_logging(config, processors)

    mock_listener.assert_called_once()
    mock_listener.return_value.start.assert_called_once()
    mock_root_logger.addHandler.assert_called_once()
    assert isinstance(
        mock_root_logger.addHandler.call_args[0][0],
        logging.handlers.QueueHandler,
    )


def test_config_src_dir_defaults_when_no_file():
    """Test that the config falls back to defaults when no file exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("pathlib.Path.cwd", return_value=Path(tmpdir)):
            config = NicestLogConfig()
            assert config.src_dir == "src"  # Default source directory


def test_config_src_dir_from_file():
    """Test that the source directory is correctly loaded from pyproject.toml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)
        pyproject_path = config_dir / "pyproject.toml"
        with open(pyproject_path, "w") as f:
            f.write("""
[tool.stogger]
src_dir = "custom_src"
""")
        with patch("pathlib.Path.cwd", return_value=config_dir):
            config = NicestLogConfig()
            assert config.src_dir == "custom_src"


def test_config_src_dir_kwargs_override():
    """Test that src_dir in kwargs overrides the file setting."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)
        pyproject_path = config_dir / "pyproject.toml"
        with open(pyproject_path, "w") as f:
            f.write("""
[tool.stogger]
src_dir = "custom_src"
""")
        with patch("pathlib.Path.cwd", return_value=config_dir):
            config = NicestLogConfig(src_dir="override_src")
            assert config.src_dir == "override_src"


if __name__ == "__main__":
    pytest.main([__file__])
