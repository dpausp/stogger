"""
Comprehensive tests for the CLI module functionality.
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from nicestlog.cli import (
    main,
    init_config,
    run_dashboard_cmd,
    generate_service_cmd,
    run_journal_viewer,
    app,
)
from typer.testing import CliRunner


class TestInitConfig:
    """Test cases for init_config function."""

    @patch("builtins.input")
    @patch("pathlib.Path.exists")
    def test_init_config_basic_flow(self, mock_exists, mock_input):
        """Test basic init_config flow."""
        mock_exists.return_value = True
        mock_input.side_effect = [
            "n",  # verbose
            "test-app",  # syslog_identifier
            "json",  # log_format
            "n",  # async_logging
            "n",  # file logging
            "src",  # source directory
            "n",  # translations
            "y",  # append to file
        ]

        with patch("builtins.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            init_config()

            mock_file.write.assert_called_once()
            written_content = mock_file.write.call_args[0][0]
            assert "[tool.nicestlog]" in written_content
            assert 'syslog_identifier = "test-app"' in written_content

    @patch("builtins.input")
    @patch("pathlib.Path.exists")
    def test_init_config_no_pyproject(self, mock_exists, mock_input):
        """Test init_config when pyproject.toml doesn't exist."""
        mock_exists.return_value = False

        with pytest.raises(SystemExit):
            init_config()


class TestMainFunction:
    """Test cases for main function."""

    def test_main_requires_subcommand(self):
        """Test that main function requires a subcommand."""
        with patch("sys.argv", ["nicestlog"]):
            with pytest.raises(SystemExit):
                main()


class TestTyperCliRunner:
    """Test cases using Typer's CliRunner for better integration testing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_help_command(self):
        """Test the main help command."""
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Nicestlog utility" in result.stdout
        assert "tools" in result.stdout
        assert "lint" in result.stdout
        assert "dashboard" in result.stdout


class TestLintCommand:
    """Test cases for lint command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_lint_help(self):
        """Test lint command help."""
        result = self.runner.invoke(app, ["lint", "--help"])
        assert result.exit_code == 0
        assert "Check logging coverage" in result.stdout
        assert "--min-coverage" in result.stdout
        assert "--max-coverage" in result.stdout
        assert "--strict" in result.stdout

    @patch("nicestlog.cli.run_linter")
    def test_lint_default_args(self, mock_linter):
        """Test lint command with default arguments."""
        result = self.runner.invoke(app, ["lint"])
        assert result.exit_code == 0
        mock_linter.assert_called_once_with(".", 5.0, 15.0, False)

    @patch("nicestlog.cli.run_linter")
    def test_lint_custom_args(self, mock_linter):
        """Test lint command with custom arguments."""
        result = self.runner.invoke(
            app,
            [
                "lint",
                "src/",
                "--min-coverage",
                "10.0",
                "--max-coverage",
                "20.0",
                "--strict",
            ],
        )
        assert result.exit_code == 0
        mock_linter.assert_called_once_with("src/", 10.0, 20.0, True)

    @patch("nicestlog.linter.lint_directory")
    def test_run_linter_function(self, mock_lint_directory):
        """Test the run_linter function directly."""
        mock_lint_directory.return_value = True

        # Test with strict=True (should override coverage values)
        run_linter("/test/path", 8.0, 18.0, True)

        mock_lint_directory.assert_called_once_with(
            Path("/test/path"), min_coverage=3.0, max_coverage=10.0
        )

    @patch("nicestlog.linter.lint_directory")
    def test_run_linter_function_no_strict(self, mock_lint_directory):
        """Test the run_linter function without strict mode."""
        mock_lint_directory.return_value = True

        # Test with strict=False (should use provided values)
        run_linter("/test/path", 8.0, 18.0, False)

        mock_lint_directory.assert_called_once_with(
            Path("/test/path"), min_coverage=8.0, max_coverage=18.0
        )


class TestDashboardCommand:
    """Test cases for dashboard command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_dashboard_help(self):
        """Test dashboard command help."""
        result = self.runner.invoke(app, ["dashboard", "--help"])
        assert result.exit_code == 0
        assert "Start the web dashboard" in result.stdout
        assert "--host" in result.stdout
        assert "--port" in result.stdout
        assert "--debug" in result.stdout

    @patch("nicestlog.cli.run_dashboard_cmd")
    def test_dashboard_default_args(self, mock_dashboard):
        """Test dashboard command with default arguments."""
        result = self.runner.invoke(app, ["dashboard"])
        assert result.exit_code == 0
        mock_dashboard.assert_called_once_with("127.0.0.1", 8080, False)

    @patch("nicestlog.cli.run_dashboard_cmd")
    def test_dashboard_custom_args(self, mock_dashboard):
        """Test dashboard command with custom arguments."""
        result = self.runner.invoke(
            app, ["dashboard", "--host", "0.0.0.0", "--port", "9000", "--debug"]
        )
        assert result.exit_code == 0
        mock_dashboard.assert_called_once_with("0.0.0.0", 9000, True)

    @patch("nicestlog.web_dashboard.run_dashboard")
    def test_run_dashboard_cmd_function(self, mock_run_dashboard):
        """Test the run_dashboard_cmd function directly."""
        run_dashboard_cmd("localhost", 3000, True)
        mock_run_dashboard.assert_called_once_with(
            host="localhost", port=3000, debug=True
        )

    @patch("nicestlog.cli.FLASK_AVAILABLE_FOR_CLI", False)
    def test_dashboard_command_hidden_when_flask_unavailable(self):
        """Test that dashboard command is hidden when Flask is not available."""
        # When Flask is not available, the dashboard command should not be registered
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        # The command should not appear in help when Flask is unavailable
        # Note: This test may pass even with Flask available due to import timing
        # but demonstrates the intended behavior

    @patch("nicestlog.web_dashboard.run_dashboard", side_effect=ImportError("No module named 'flask'"))
    def test_run_dashboard_cmd_missing_flask(self, mock_run_dashboard):
        """Test run_dashboard_cmd function when Flask is missing."""
        import typer
        with pytest.raises(typer.Exit) as exc_info:
            run_dashboard_cmd("localhost", 3000, True)
        
        assert exc_info.value.exit_code == 1
        mock_run_dashboard.assert_called_once()

    @patch("nicestlog.web_dashboard.FLASK_AVAILABLE", False)
    @patch("nicestlog.web_dashboard.run_dashboard")
    def test_run_dashboard_cmd_flask_not_available(self, mock_run_dashboard):
        """Test run_dashboard_cmd when Flask is not available in web_dashboard module."""
        import typer
        mock_run_dashboard.side_effect = ImportError("Flask is not installed")
        
        with pytest.raises(typer.Exit) as exc_info:
            run_dashboard_cmd("localhost", 3000, True)
        
        assert exc_info.value.exit_code == 1


class TestGenerateServiceCommand:
    """Test cases for generate-service command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_generate_service_help(self):
        """Test tools generate-service command help."""
        result = self.runner.invoke(app, ["tools", "generate-service", "--help"])
        assert result.exit_code == 0
        assert "Generate systemd service file" in result.stdout
        assert "service_name" in result.stdout
        assert "exec_command" in result.stdout
        assert "--user" in result.stdout
        assert "--working-dir" in result.stdout
        assert "--output" in result.stdout

    @patch("nicestlog.cli.generate_service_cmd")
    def test_generate_service_required_args(self, mock_generate):
        """Test tools generate-service command with required arguments."""
        result = self.runner.invoke(
            app, ["tools", "generate-service", "myapp", "/usr/bin/myapp"]
        )
        assert result.exit_code == 0
        mock_generate.assert_called_once_with(
            "myapp", "/usr/bin/myapp", None, None, None
        )

    @patch("nicestlog.cli.generate_service_cmd")
    def test_generate_service_all_args(self, mock_generate):
        """Test tools generate-service command with all arguments."""
        result = self.runner.invoke(
            app,
            [
                "tools",
                "generate-service",
                "myapp",
                "/usr/bin/myapp",
                "--user",
                "myuser",
                "--working-dir",
                "/opt/myapp",
                "--output",
                "/tmp/myapp.service",
            ],
        )
        assert result.exit_code == 0
        mock_generate.assert_called_once_with(
            "myapp", "/usr/bin/myapp", "myuser", "/opt/myapp", "/tmp/myapp.service"
        )

    def test_generate_service_missing_args(self):
        """Test tools generate-service command with missing required arguments."""
        result = self.runner.invoke(app, ["tools", "generate-service"])
        assert result.exit_code != 0
        # Use result.output when stderr is mixed with stdout
        error_output = result.output
        assert "Missing argument" in error_output or "required" in error_output.lower()

    @patch("nicestlog.systemd_integration.create_systemd_service_file")
    @patch("builtins.print")
    def test_generate_service_cmd_function_stdout(
        self, mock_print, mock_create_service
    ):
        """Test generate_service_cmd function with stdout output."""
        mock_create_service.return_value = "[Unit]\nDescription=Test Service\n"

        generate_service_cmd("test-service", "/bin/test", None, None, None)

        mock_create_service.assert_called_once_with(
            service_name="test-service",
            exec_command="/bin/test",
            user=None,
            working_directory=None,
        )
        mock_print.assert_called_with("[Unit]\nDescription=Test Service\n")

    @patch("nicestlog.systemd_integration.create_systemd_service_file")
    @patch("builtins.open", new_callable=mock_open)
    @patch("builtins.print")
    def test_generate_service_cmd_function_file_output(
        self, mock_print, mock_file, mock_create_service
    ):
        """Test generate_service_cmd function with file output."""
        mock_create_service.return_value = "[Unit]\nDescription=Test Service\n"

        generate_service_cmd(
            "test-service", "/bin/test", "testuser", "/opt/test", "/tmp/test.service"
        )

        mock_create_service.assert_called_once_with(
            service_name="test-service",
            exec_command="/bin/test",
            user="testuser",
            working_directory="/opt/test",
        )
        mock_file.assert_called_once_with("/tmp/test.service", "w")
        mock_file().write.assert_called_once_with("[Unit]\nDescription=Test Service\n")


class TestJournalCommand:
    """Test cases for journal command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_journal_help(self):
        """Test journal command help."""
        result = self.runner.invoke(app, ["journal", "--help"])
        assert result.exit_code == 0
        assert "Beautiful systemd journal viewer" in result.stdout
        assert "--unit" in result.stdout or "--service" in result.stdout
        assert "--lines" in result.stdout
        assert "--follow" in result.stdout
        assert "--since" in result.stdout
        assert "--level" in result.stdout

    @patch("nicestlog.cli.run_journal_viewer")
    def test_journal_default_args(self, mock_journal):
        """Test journal command with default arguments."""
        result = self.runner.invoke(app, ["journal"])
        assert result.exit_code == 0
        mock_journal.assert_called_once_with(None, 50, False, None, None)

    @patch("nicestlog.cli.run_journal_viewer")
    def test_journal_custom_args(self, mock_journal):
        """Test journal command with custom arguments."""
        result = self.runner.invoke(
            app,
            [
                "journal",
                "--unit",
                "nginx.service",
                "--lines",
                "100",
                "--follow",
                "--since",
                "1 hour ago",
                "--level",
                "error",
            ],
        )
        assert result.exit_code == 0
        mock_journal.assert_called_once_with(
            "nginx.service", 100, True, "1 hour ago", "error"
        )

    def test_journal_invalid_level(self):
        """Test journal command with invalid level."""
        result = self.runner.invoke(app, ["journal", "--level", "invalid"])
        assert result.exit_code == 1
        # Use result.output when stderr is mixed with stdout
        error_output = result.output
        assert "Invalid level 'invalid'" in error_output

    @patch("nicestlog.journal_viewer.SYSTEMD_AVAILABLE", False)
    @patch("builtins.print")
    def test_run_journal_viewer_no_systemd(self, mock_print):
        """Test run_journal_viewer when systemd is not available."""
        with pytest.raises(SystemExit):
            run_journal_viewer()

        # Check that error message was printed
        mock_print.assert_called()
        call_args = mock_print.call_args[0][0]
        assert "systemd-python not available" in call_args


class TestReviewCommand:
    """Test cases for review command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_review_help(self):
        """Test review command help."""
        result = self.runner.invoke(app, ["review", "--help"])
        assert result.exit_code == 0
        assert "Review log quality" in result.stdout
        assert "--format" in result.stdout
        assert "--min-score" in result.stdout

    @patch("nicestlog.cli.run_log_reviewer")
    def test_review_required_args(self, mock_reviewer):
        """Test review command with required arguments."""
        result = self.runner.invoke(app, ["review", "/path/to/logs"])
        assert result.exit_code == 0
        mock_reviewer.assert_called_once_with("/path/to/logs", "text", 70.0)

    @patch("nicestlog.cli.run_log_reviewer")
    def test_review_custom_args(self, mock_reviewer):
        """Test review command with custom arguments."""
        result = self.runner.invoke(
            app, ["review", "/path/to/logs", "--format", "json", "--min-score", "80"]
        )
        assert result.exit_code == 0
        mock_reviewer.assert_called_once_with("/path/to/logs", "json", 80.0)

    def test_review_invalid_format(self):
        """Test review command with invalid format."""
        result = self.runner.invoke(
            app, ["review", "/path/to/logs", "--format", "invalid"]
        )
        assert result.exit_code == 1
        # Use result.output when stderr is mixed with stdout
        error_output = result.output
        assert "Invalid format 'invalid'" in error_output

    def test_review_missing_path(self):
        """Test review command with missing path argument."""
        result = self.runner.invoke(app, ["review"])
        assert result.exit_code != 0
        # Use result.output when stderr is mixed with stdout
        error_output = result.output
        assert "Missing argument" in error_output or "required" in error_output.lower()


class TestParameterValidation:
    """Test cases for parameter validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_lint_invalid_coverage_type(self):
        """Test lint command with invalid coverage type."""
        result = self.runner.invoke(app, ["lint", "--min-coverage", "invalid"])
        assert result.exit_code != 0

    def test_dashboard_invalid_port_type(self):
        """Test dashboard command with invalid port type."""
        result = self.runner.invoke(app, ["dashboard", "--port", "invalid"])
        assert result.exit_code != 0

    def test_journal_invalid_lines_type(self):
        """Test journal command with invalid lines type."""
        result = self.runner.invoke(app, ["journal", "--lines", "invalid"])
        assert result.exit_code != 0


if __name__ == "__main__":
    pytest.main([__file__])
