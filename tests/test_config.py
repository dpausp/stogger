"""
Tests for the NicestLogConfig class.
"""
import pytest
from pathlib import Path
import tempfile
from unittest.mock import patch

from nicestlog.config import NicestLogConfig

@pytest.fixture
def create_pyproject_toml():
    """A pytest fixture to create a temporary pyproject.toml for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)
        pyproject_path = config_dir / "pyproject.toml"
        with open(pyproject_path, "w") as f:
            f.write("""
[tool.nicestlog]
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
        log_to_console=False
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
            assert config.syslog_identifier == "nicestlog"
            assert config.language == "en"

if __name__ == "__main__":
    pytest.main([__file__])
