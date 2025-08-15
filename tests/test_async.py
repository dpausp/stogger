"""
Tests for the asynchronous logging functionality.
"""

import pytest
import logging
from unittest.mock import patch, MagicMock

from nicestlog.config import NicestLogConfig
from nicestlog.factory import configure_stdlib_logging, build_shared_processors


@patch("logging.basicConfig")
def test_sync_logging_setup(mock_basic_config):
    """Test that synchronous logging sets up basicConfig directly."""
    config = NicestLogConfig(async_logging=False, log_to_console=True)
    processors = build_shared_processors(config)
    configure_stdlib_logging(config, processors)

    mock_basic_config.assert_called_once()
    assert "handlers" in mock_basic_config.call_args.kwargs
    assert any(
        isinstance(h, logging.StreamHandler)
        for h in mock_basic_config.call_args.kwargs["handlers"]
    )


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
        mock_root_logger.addHandler.call_args[0][0], logging.handlers.QueueHandler
    )


if __name__ == "__main__":
    pytest.main([__file__])
