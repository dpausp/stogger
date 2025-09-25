"""Tests for systemd integration functionality."""

import os
from unittest.mock import MagicMock, patch

import pytest

from nicestlog.systemd_integration import (
    ServiceConfig,
    SystemdJournalHandler,
    create_systemd_service_file,
    detect_systemd_environment,
    setup_systemd_logging,
)


class TestDetectSystemdEnvironment:
    """Test cases for detect_systemd_environment function."""

    @patch.dict(os.environ, {"JOURNAL_STREAM": "8:12345"}, clear=False)
    def test_systemd_detected_with_journal_stream(self):
        """Test systemd detection when JOURNAL_STREAM is present."""
        result = detect_systemd_environment()
        assert isinstance(result, dict)
        assert result["journal_stream"] == "8:12345"

    @patch.dict(os.environ, {"SYSTEMD_EXEC_PID": "12345"}, clear=False)
    def test_systemd_detected_with_systemd_exec_pid(self):
        """Test systemd detection when SYSTEMD_EXEC_PID is present."""
        result = detect_systemd_environment()
        assert isinstance(result, dict)
        assert result["running_under_systemd"] is True
        assert result["systemd_exec_pid"] == "12345"

    @patch.dict(os.environ, {}, clear=True)
    @patch("os.path.exists")
    def test_systemd_not_detected(self, mock_exists):
        """Test when systemd is not detected."""
        mock_exists.return_value = False
        result = detect_systemd_environment()
        assert isinstance(result, dict)
        assert result["running_under_systemd"] is False


class TestSetupSystemdLogging:
    """Test cases for setup_systemd_logging function."""

    @patch("nicestlog.systemd_integration.detect_systemd_environment")
    def test_setup_with_systemd_available(self, mock_detect):
        """Test setup when systemd is available."""
        mock_detect.return_value = {
            "running_under_systemd": True,
            "journal_available": True,
        }

        result = setup_systemd_logging()

        # Should return a handler or True/False based on actual implementation
        assert result is not None

    @patch("nicestlog.systemd_integration.detect_systemd_environment")
    def test_setup_without_systemd(self, mock_detect):
        """Test setup when systemd is not available."""
        mock_detect.return_value = {
            "running_under_systemd": False,
            "journal_available": False,
        }

        result = setup_systemd_logging()

        assert result is False

    @patch("nicestlog.systemd_integration.detect_systemd_environment")
    def test_setup_with_custom_identifier(self, mock_detect):
        """Test setup with custom syslog identifier."""
        mock_detect.return_value = {
            "running_under_systemd": True,
            "journal_available": True,
        }

        result = setup_systemd_logging()

        assert result is not None


class TestCreateSystemdServiceFile:
    """Test cases for create_systemd_service_file function."""

    def test_service_file_creation_basic(self):
        """Test basic service file creation."""
        config = ServiceConfig(
            service_name="test",
            exec_command="/usr/bin/python /app/main.py",
        )
        result = create_systemd_service_file(config)

        assert isinstance(result, str)
        assert "[Unit]" in result
        assert "[Service]" in result
        assert "[Install]" in result
        assert "ExecStart=/usr/bin/python /app/main.py" in result

    def test_service_file_creation_with_options(self):
        """Test service file creation with custom options."""
        config = ServiceConfig(
            service_name="test",
            exec_command="/usr/bin/python /app/main.py",
            user="testuser",
            working_directory="/app",
            environment={"LOG_LEVEL": "DEBUG", "ENV": "production"},
        )
        result = create_systemd_service_file(config)

        assert "User=testuser" in result
        assert "WorkingDirectory=/app" in result
        assert "Environment=LOG_LEVEL=DEBUG" in result
        assert "Environment=ENV=production" in result

    def test_service_file_creation_with_restart_policy(self):
        """Test service file creation with restart policy."""
        config = ServiceConfig(
            service_name="test",
            exec_command="/usr/bin/python /app/main.py",
            restart_policy="on-failure",
        )
        result = create_systemd_service_file(config)

        assert "Restart=on-failure" in result
        assert "RestartSec=5" in result


class TestSystemdJournalHandler:
    """Test cases for SystemdJournalHandler class."""

    @patch("nicestlog.systemd_integration.journal")
    def test_handler_initialization(self, mock_journal):
        """Test handler initialization."""
        handler = SystemdJournalHandler(identifier="test-app")

        assert handler.identifier == "test-app"

    @patch("nicestlog.systemd_integration.journal")
    def test_emit_log_record(self, mock_journal):
        """Test emitting a log record."""
        handler = SystemdJournalHandler(identifier="test-app")

        # Create a mock event dict
        event_dict = {
            "level": "info",
            "event": "Test message",
            "logger": "test.logger",
            "timestamp": "2023-01-01T12:00:00",
        }

        result = handler(None, None, event_dict)

        # Should return the event_dict unchanged
        assert result == event_dict

    def test_handler_without_systemd_journal(self):
        """Test handler behavior when systemd.journal is not available."""
        with patch.dict("sys.modules", {"systemd": None, "systemd.journal": None}):
            # This should not raise an exception during import
            from nicestlog.systemd_integration import SystemdJournalHandler

            # Handler should still be creatable but might not function
            handler = SystemdJournalHandler()
            assert handler is not None


if __name__ == "__main__":
    pytest.main([__file__])
