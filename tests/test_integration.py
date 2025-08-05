"""
Integration tests for the nicestlog library.
"""
import pytest
from unittest.mock import patch
from pathlib import Path
import tempfile
import structlog

from nicestlog import init_logging, logging_initialized
from nicestlog.core import MultiOptimisticLoggerFactory

def test_init_logging_e2e():
    """End-to-end test for a simple init_logging call."""
    with patch("structlog.configure") as mock_configure:
        init_logging(verbose=True, log_to_console=True)
        
        mock_configure.assert_called_once()
        args, kwargs = mock_configure.call_args
        
        assert "processors" in kwargs
        assert "logger_factory" in kwargs
        assert isinstance(kwargs["logger_factory"], MultiOptimisticLoggerFactory)
        assert "console" in kwargs["logger_factory"].factories
        assert logging_initialized()

def test_init_logging_with_file_e2e():
    """End-to-end test for file logging."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir)
        with patch("structlog.configure") as mock_configure:
            init_logging(logdir=log_dir, syslog_identifier="e2e-test")
            
            log_file = log_dir / "e2e-test.log"
            assert log_file.exists()
            
            # Clean up the created file handle
            factory = mock_configure.call_args.kwargs['logger_factory']
            file_logger = factory.factories.get('file')
            if file_logger and hasattr(file_logger, '_file'):
                file_logger._file.close()

if __name__ == "__main__":
    pytest.main([__file__])
