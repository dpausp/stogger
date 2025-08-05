"""
Tests for the factory functions that build logging components.
"""
import pytest
from unittest.mock import patch, mock_open
import toml

from nicestlog.config import NicestLogConfig
from nicestlog.factory import build_processors, build_loggers
from nicestlog.core import TranslationProcessor, MultiRenderer, ConsoleFileRenderer

def test_build_processors_basic():
    """Test building a basic set of processors."""
    config = NicestLogConfig(verbose=False)
    processors = build_processors(config)
    
    assert any(isinstance(p, MultiRenderer) for p in processors)
    assert not any(isinstance(p, TranslationProcessor) for p in processors)

@patch("builtins.open", new_callable=mock_open, read_data='test-key = "Test Message"')
@patch("toml.load")
def test_build_processors_with_translation(mock_toml_load, mock_file):
    """Test that the TranslationProcessor is added when configured."""
    mock_toml_load.return_value = {"test-key": "Test Message"}
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = NicestLogConfig(translation_dir=tmpdir)
        processors = build_processors(config)
        
        assert any(isinstance(p, TranslationProcessor) for p in processors)

def test_build_loggers_basic():
    """Test building a basic console logger."""
    config = NicestLogConfig(log_to_console=True, logdir=None)
    loggers = build_loggers(config)
    
    assert "console" in loggers
    assert "file" not in loggers
    assert "journal" not in loggers  # Assuming systemd is not available in test env

@patch("nicestlog.factory.journal", new=None)
def test_build_loggers_no_journal():
    """Test that the journal logger is not added if the library is not present."""
    config = NicestLogConfig()
    loggers = build_loggers(config)
    assert "journal" not in loggers

def test_build_loggers_with_file():
    """Test that a file logger is added when a logdir is provided."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = NicestLogConfig(logdir=tmpdir)
        loggers = build_loggers(config)
        assert "file" in loggers

if __name__ == "__main__":
    pytest.main([__file__])
