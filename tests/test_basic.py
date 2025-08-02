"""
Basic tests for nicestlog functionality.
"""

import pytest
from pathlib import Path
import tempfile

import nicestlog


def test_basic_logging_setup():
    """Test basic logging setup works."""
    log = nicestlog.setup_basic_logging(verbose=True, app_name="test")
    
    assert log is not None
    assert hasattr(log, 'info')
    assert hasattr(log, 'debug')
    assert hasattr(log, 'error')


def test_file_logging_setup():
    """Test file logging setup works."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logdir = Path(tmpdir)
        log = nicestlog.setup_file_logging(
            logdir=logdir,
            verbose=True,
            app_name="test"
        )
        
        assert log is not None
        
        # Test that log files are created when we log something
        log.info("test message", test_field="test_value")
        
        log_files = list(logdir.glob("*.log"))
        assert len(log_files) > 0


def test_structured_logging():
    """Test structured logging with template messages."""
    log = nicestlog.setup_basic_logging(verbose=True, app_name="test")
    
    # This should not raise any exceptions
    log.info(
        "test-event",
        _replace_msg="Test message with {field}",
        field="value",
        additional_data=123
    )


def test_bound_logger():
    """Test bound logger functionality."""
    log = nicestlog.setup_basic_logging(verbose=True, app_name="test")
    
    bound_log = log.bind(session_id="test-session", user_id=123)
    
    # This should not raise any exceptions
    bound_log.info("test message")


def test_error_logging():
    """Test error logging with exceptions."""
    log = nicestlog.setup_basic_logging(verbose=True, app_name="test")
    
    try:
        raise ValueError("Test error")
    except ValueError as e:
        # This should not raise any exceptions
        log.error(
            "test-error",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )


def test_get_logger():
    """Test get_logger function."""
    # Should auto-initialize if not already done
    log = nicestlog.get_logger("test_component")
    
    assert log is not None
    assert hasattr(log, 'info')


if __name__ == "__main__":
    pytest.main([__file__])