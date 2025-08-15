
"""
Tests for the NicestLogConfig class, specifically for the src_dir configuration.
"""

import pytest
from pathlib import Path
import tempfile
from unittest.mock import patch

from nicestlog.config import NicestLogConfig

def test_config_defaults_when_no_file():
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
[tool.nicestlog]
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
[tool.nicestlog]
src_dir = "custom_src"
""")
        with patch("pathlib.Path.cwd", return_value=config_dir):
            config = NicestLogConfig(src_dir="override_src")
            assert config.src_dir == "override_src"

if __name__ == "__main__":
    pytest.main([__file__])
