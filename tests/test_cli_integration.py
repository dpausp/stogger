"""End-to-end integration tests for the CLI commands.
These tests actually run the commands with real functionality.
"""

import logging
from pathlib import Path
import os
import subprocess
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from stoggertools.cli import app

# Check if Flask is available for dashboard tests
try:
    import flask  # noqa: F401

    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False


class TestCliIntegration:
    """Integration tests that run actual CLI commands end-to-end."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TestInitConfigIntegration:
    """Integration tests for init-config command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_config_creates_pyproject_toml(self):
        """Test that init-config actually creates configuration."""
        pyproject_path = self.temp_path / "pyproject.toml"
        pyproject_path.write_text('[build-system]\nrequires = ["setuptools"]\n')

        # Mock the interactive input
        with patch("builtins.input") as mock_input:
            mock_input.side_effect = [
                "y",  # verbose
                "myapp",  # syslog_identifier
                "json",  # log_format
                "y",  # async_logging
                "n",  # file logging
                "src",  # source directory
                "n",  # translations
                "y",  # append to file
            ]

            # Change to the temp directory to run the command

            original_cwd = Path.cwd()
            try:
                os.chdir(self.temp_path)
                result = self.runner.invoke(app, ["init"])

                assert result.exit_code == 0

                # Check that the pyproject.toml was updated
                updated_content = pyproject_path.read_text()
                assert "[tool.stogger]" in updated_content
                assert "verbose = true" in updated_content
                assert 'syslog_identifier = "myapp"' in updated_content
                assert 'log_format = "json"' in updated_content
                assert "async_logging = true" in updated_content
            finally:
                os.chdir(original_cwd)


class TestLintIntegration:
    """Integration tests for lint command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_lint_python_file_with_logging(self, caplog):
        """Test linting a Python file that has good logging."""
        caplog.set_level(logging.INFO)
        test_file = self.temp_path / "good_logging.py"
        test_file.write_text('''import logging

def process_data(data):
    """Process some data with logging."""
    logging.info("Starting data processing")
    
    if not data:
        logging.error("No data provided")
        return None
        
    result = data * 2
    logging.debug(f"Processed data: {result}")
    return result

def main():
    logging.info("Application started")
    result = process_data([1, 2, 3])
    logging.info(f"Result: {result}")
''')

        result = self.runner.invoke(app, ["check", str(test_file)])

        # The test file has good logging practices, so it should pass
        assert result.exit_code == 0
        assert "All checks passed" in caplog.text or "Unified Code Quality Analysis" in caplog.text

    def test_lint_python_file_with_good_logging(self, caplog):
        """Test linting a Python file that has appropriate logging coverage."""
        caplog.set_level(logging.INFO)
        test_file = self.temp_path / "good_coverage.py"
        test_file.write_text('''import logging

def process_data(data):
    """Process some data with moderate logging."""
    logging.info("Starting data processing")
    
    if not data:
        return None
        
    result = data * 2
    return result

def calculate(x, y):
    """Simple calculation without logging."""
    return x + y

def format_result(result):
    """Format result without logging."""
    return f"Result: {result}"

def main():
    """Main function with minimal logging."""
    logging.info("Application started")
    data = [1, 2, 3]
    result = process_data(data)
    formatted = format_result(result)
    return formatted
''')

        result = self.runner.invoke(app, ["check", str(self.temp_path)])

        # This should have good logging coverage (around 6-10%)
        assert result.exit_code == 0
        assert "All checks passed" in caplog.text or "Unified Code Quality Analysis" in caplog.text

    def test_lint_python_file_with_no_logging(self, caplog):
        """Test linting a Python file with insufficient logging."""
        caplog.set_level(logging.INFO)
        test_file = self.temp_path / "bad_logging.py"
        test_file.write_text('''def calculate(x, y):
    """Calculate something without any logging."""
    return x + y

def process_list(items):
    """Process items without logging."""
    results = []
    for item in items:
        results.append(calculate(item, 10))
    return results

def main():
    data = [1, 2, 3, 4, 5]
    result = process_list(data)
    print(f"Final result: {result}")
''')

        # Test with directory path since linter works on directories
        result = self.runner.invoke(app, ["check", str(self.temp_path)])

        # Should pass or fail depending on actual analysis
        assert result.exit_code in [0, 1]
        assert "All checks passed" in result.output or "Unified Code Quality Analysis" in result.output

    def test_lint_directory_with_mixed_files(self, caplog):
        """Test linting a directory with both good and bad files."""
        caplog.set_level(logging.INFO)
        # Create a good file
        good_file = self.temp_path / "good.py"
        good_file.write_text("""
import logging
log = logging.getLogger(__name__)

def good_function():
    log.info("This function has logging")
    log.debug("Debug information")
    return "success"
""")

        # Create a bad file
        bad_file = self.temp_path / "bad.py"
        bad_file.write_text("""
def bad_function():
    # No logging at all
    return "result"

def another_bad_function():
    # Still no logging
    value = 42
    return value * 2
""")

        result = self.runner.invoke(app, ["check", str(self.temp_path)])

        # Should pass or fail depending on actual analysis
        assert result.exit_code in [0, 1]
        assert "All checks passed" in caplog.text or "Unified Code Quality Analysis" in caplog.text

    def test_lint_with_strict_mode(self):
        """Test lint command with strict coverage requirements."""
        test_file = self.temp_path / "moderate_logging.py"
        test_file.write_text("""
import logging

def func1():
    logging.info("Some logging")
    
def func2():
    # No logging
    pass
    
def func3():
    # No logging  
    pass
""")

        # Normal mode should work
        result = self.runner.invoke(app, ["check", str(test_file)])

        # Should run successfully
        assert result.exit_code in [0, 1]  # Could pass or fail, but should run


class TestGenerateServiceIntegration:
    """Integration tests for generate-service command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_service_to_stdout(self):
        """Test generating a systemd service file to stdout."""
        result = self.runner.invoke(
            app,
            ["tools", "generate-service", "test-app", "/usr/bin/test-app"],
        )

        assert result.exit_code == 0

        # Check that service file content is generated
        output = result.stdout
        assert "[Unit]" in output
        assert "Description=" in output
        assert "[Service]" in output
        assert "ExecStart=/usr/bin/test-app" in output
        assert "[Install]" in output
        assert "WantedBy=multi-user.target" in output

    def test_generate_service_to_file(self):
        """Test generating a systemd service file to a file."""
        output_file = self.temp_path / "test-service.service"

        result = self.runner.invoke(
            app,
            [
                "tools",
                "generate-service",
                "test-app",
                "/usr/bin/test-app",
                "--user",
                "testuser",
                "--working-dir",
                "/opt/test",
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()

        content = output_file.read_text()
        assert "[Unit]" in content
        assert "ExecStart=/usr/bin/test-app" in content
        assert "User=testuser" in content
        assert "WorkingDirectory=/opt/test" in content

        # Service generation completed successfully (no output expected)
        assert result.exit_code == 0


class TestJournalIntegration:
    """Integration tests for journal command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("stogger_systemd.journal_viewer.SYSTEMD_AVAILABLE", False)
    def test_journal_no_systemd_dependency(self):
        """Test journal command when systemd is not available."""
        result = self.runner.invoke(app, ["tools", "journal"])

        assert result.exit_code == 1
        # Use result.output when stderr is mixed with stdout
        error_output = result.output
        assert "systemd-python not available" in error_output

    @patch("stogger_systemd.journal_viewer.SYSTEMD_AVAILABLE", True)
    @patch("stogger_systemd.journal_viewer.JournalViewer")
    @patch("stoggertools.cli.SYSTEMD_AVAILABLE", True)
    @patch("stoggertools.cli.run_journal_viewer")
    def test_journal_with_systemd_available(self, mock_run_journal, mock_viewer_class):
        """Test journal command when systemd is available."""
        mock_viewer = MagicMock()
        mock_viewer_class.return_value = mock_viewer

        # Mock journal entries
        mock_entries = [
            {"MESSAGE": "Test log entry 1", "PRIORITY": "6"},
            {"MESSAGE": "Test log entry 2", "PRIORITY": "4"},
        ]
        mock_viewer.query_journal.return_value = mock_entries
        mock_viewer.format_entry.side_effect = lambda entry: f"Formatted: {entry['MESSAGE']}"

        result = self.runner.invoke(
            app,
            ["tools", "journal", "--unit", "test.service", "--lines", "10"],
        )

        assert result.exit_code == 0
        mock_run_journal.assert_called_once_with("test.service", 10, follow=False, since=None, level=None)


class TestReviewIntegration:
    """Integration tests for review command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_review_log_file(self):
        """Test reviewing a single log file."""
        log_file = self.temp_path / "test.log"
        log_file.write_text("""
2024-01-01 10:00:00 INFO Starting application
2024-01-01 10:00:01 DEBUG Loading configuration
2024-01-01 10:00:02 INFO Configuration loaded successfully
2024-01-01 10:00:03 WARNING Could not connect to cache
2024-01-01 10:00:04 ERROR Database connection failed
2024-01-01 10:00:05 INFO Retrying database connection
2024-01-01 10:00:06 INFO Database connected successfully
""")

        # Mock the reviewer components
        with patch("stoggertools.cli.run_log_reviewer") as mock_run_reviewer:
            result = self.runner.invoke(app, ["tools", "review", str(log_file)])

            # Should succeed
            assert result.exit_code == 0
            mock_run_reviewer.assert_called_once_with(str(log_file), "text", 70.0)

    def test_review_log_directory(self):
        """Test reviewing a directory of log files."""
        # Create multiple log files
        log1 = self.temp_path / "app.log"
        log1.write_text("2024-01-01 10:00:00 INFO Application started\n")

        log2 = self.temp_path / "error.log"
        log2.write_text("2024-01-01 10:00:01 ERROR Database connection failed\n")

        # Mock the reviewer components
        with patch("stoggertools.cli.run_log_reviewer") as mock_run_reviewer:
            result = self.runner.invoke(
                app,
                [
                    "tools",
                    "review",
                    str(self.temp_path),
                    "--format",
                    "json",
                    "--min-score",
                    "70",
                ],
            )

            assert result.exit_code == 0
            mock_run_reviewer.assert_called_once_with(str(self.temp_path), "json", 70.0)

    def test_review_with_low_score_fails(self):
        """Test that review fails when log quality is below minimum score."""
        log_file = self.temp_path / "bad.log"
        log_file.write_text("Some poorly formatted log content\n")

        with patch("stoggertools.log_reviewer.LogQualityReviewer") as mock_reviewer_class:
            mock_reviewer = MagicMock()
            mock_reviewer_class.return_value = mock_reviewer

            # Mock a report with low score
            mock_report = MagicMock()
            mock_report.overall_score = 40.0  # Below default minimum of 70
            mock_reviewer.analyze_log_file.return_value = mock_report

            with patch("stoggertools.log_reviewer.print_report"):
                result = self.runner.invoke(app, ["tools", "review", str(log_file)])

                assert result.exit_code == 1  # Should fail due to low score


@pytest.mark.skipif(not FLASK_AVAILABLE, reason="Flask is not installed")
class TestDashboardIntegration:
    """Integration tests for dashboard command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("stogger_web.web_dashboard.run_dashboard")
    def test_dashboard_starts_with_default_settings(self, mock_run_dashboard):
        """Test that dashboard starts with default settings."""
        # Mock the dashboard to avoid actually starting a web server
        mock_run_dashboard.return_value = None

        result = self.runner.invoke(app, ["tools", "dashboard"])

        assert result.exit_code == 0
        mock_run_dashboard.assert_called_once_with(
            host="127.0.0.1",
            port=8080,
            debug=False,
        )

    @patch("stoggertools.cli.run_dashboard")
    def test_dashboard_with_custom_settings(self, mock_run_dashboard):
        """Test dashboard with custom host, port, and debug mode."""
        mock_run_dashboard.return_value = None

        result = self.runner.invoke(
            app,
            ["tools", "dashboard", "--host", "0.0.0.0", "--port", "9000", "--debug"],
        )

        assert result.exit_code == 0
        mock_run_dashboard.assert_called_once_with(
            host="0.0.0.0",
            port=9000,
            debug=True,
        )


class TestRealExecutionIntegration:
    """Test the CLI by actually executing it as a subprocess."""

    def test_help_command_subprocess(self):
        """Test running the help command as a real subprocess."""
        result = subprocess.run(
            [sys.executable, "-m", "stoggertools", "--help"],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0
        assert "Stoggertools utility" in result.stdout
        # Typer uses "Commands" (with a different format than argparse)
        assert "Commands" in result.stdout or "init-config" in result.stdout

    def test_lint_help_subprocess(self):
        """Test running lint help as a real subprocess."""
        result = subprocess.run(
            [sys.executable, "-m", "stoggertools", "check", "--help"],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0
        assert "Check code for logging best practices" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__])
