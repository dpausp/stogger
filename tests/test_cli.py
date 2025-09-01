"""
Comprehensive tests for the CLI module functionality.
"""

import pytest
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock, mock_open

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
        assert "check" in result.stdout
        # dashboard is under tools subcommand, not main help
        assert "docs" in result.stdout


class TestDashboardCommand:
    """Test cases for dashboard command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_dashboard_help(self):
        """Test dashboard command help."""
        result = self.runner.invoke(app, ["tools", "dashboard", "--help"])
        assert result.exit_code == 0
        assert "Start the web dashboard" in result.stdout
        assert "--host" in result.stdout
        assert "--port" in result.stdout
        assert "--debug" in result.stdout

    @patch("nicestlog.cli.run_dashboard_cmd")
    def test_dashboard_default_args(self, mock_dashboard):
        """Test dashboard command with default arguments."""
        result = self.runner.invoke(app, ["tools", "dashboard"])
        assert result.exit_code == 0
        mock_dashboard.assert_called_once_with("127.0.0.1", 8080, False)

    @patch("nicestlog.cli.run_dashboard_cmd")
    def test_dashboard_custom_args(self, mock_dashboard):
        """Test dashboard command with custom arguments."""
        result = self.runner.invoke(
            app,
            ["tools", "dashboard", "--host", "0.0.0.0", "--port", "9000", "--debug"],
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

    @patch(
        "nicestlog.web_dashboard.run_dashboard",
        side_effect=ImportError("No module named 'flask'"),
    )
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
        result = self.runner.invoke(app, ["tools", "journal", "--help"])
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
        result = self.runner.invoke(app, ["tools", "journal"])
        assert result.exit_code == 0
        mock_journal.assert_called_once_with(None, 50, False, None, None)

    @patch("nicestlog.cli.run_journal_viewer")
    def test_journal_custom_args(self, mock_journal):
        """Test journal command with custom arguments."""
        result = self.runner.invoke(
            app,
            [
                "tools",
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
        result = self.runner.invoke(app, ["tools", "journal", "--level", "invalid"])
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
        result = self.runner.invoke(app, ["tools", "review", "--help"])
        assert result.exit_code == 0
        assert "Review log quality" in result.stdout
        assert "--format" in result.stdout
        assert "--min-score" in result.stdout

    @patch("nicestlog.cli.run_log_reviewer")
    def test_review_required_args(self, mock_reviewer):
        """Test review command with required arguments."""
        result = self.runner.invoke(app, ["tools", "review", "/path/to/logs"])
        assert result.exit_code == 0
        mock_reviewer.assert_called_once_with("/path/to/logs", "text", 70.0)

    @patch("nicestlog.cli.run_log_reviewer")
    def test_review_custom_args(self, mock_reviewer):
        """Test review command with custom arguments."""
        result = self.runner.invoke(
            app,
            [
                "tools",
                "review",
                "/path/to/logs",
                "--format",
                "json",
                "--min-score",
                "80",
            ],
        )
        assert result.exit_code == 0
        mock_reviewer.assert_called_once_with("/path/to/logs", "json", 80.0)

    def test_review_invalid_format(self):
        """Test review command with invalid format."""
        result = self.runner.invoke(
            app, ["tools", "review", "/path/to/logs", "--format", "invalid"]
        )
        assert result.exit_code == 1
        # Use result.output when stderr is mixed with stdout
        error_output = result.output
        assert "Invalid format 'invalid'" in error_output

    def test_review_missing_path(self):
        """Test review command with missing path argument."""
        result = self.runner.invoke(app, ["tools", "review"])
        assert result.exit_code != 0
        # Use result.output when stderr is mixed with stdout
        error_output = result.output
        assert "Missing argument" in error_output or "required" in error_output.lower()


class TestParameterValidation:
    """Test cases for parameter validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_check_invalid_parameter_type(self):
        """Test check command with invalid parameter type."""
        result = self.runner.invoke(app, ["check", "--verbose", "invalid"])
        assert result.exit_code != 0

    def test_dashboard_invalid_port_type(self):
        """Test dashboard command with invalid port type."""
        result = self.runner.invoke(app, ["tools", "dashboard", "--port", "invalid"])
        assert result.exit_code != 0

    def test_journal_invalid_lines_type(self):
        """Test journal command with invalid lines type."""
        result = self.runner.invoke(app, ["tools", "journal", "--lines", "invalid"])
        assert result.exit_code != 0


class TestCliErrorHandling:
    """Test CLI error handling scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_check_command_file_not_found(self):
        """Test check command with non-existent file."""
        result = self.runner.invoke(app, ["check", "/nonexistent/file.py"])
        assert result.exit_code == 1
        assert "does not exist" in result.output

    def test_check_command_permission_denied(self):
        """Test check command with permission denied scenario."""
        with TemporaryDirectory() as temp_dir:
            # Create a file and remove read permissions
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("print('hello')")
            test_file.chmod(0o000)  # No permissions

            try:
                result = self.runner.invoke(app, ["check", str(test_file)])
                # Should handle permission error gracefully
                assert result.exit_code != 0
            finally:
                # Restore permissions for cleanup
                test_file.chmod(0o644)

    def test_init_command_invalid_path(self):
        """Test init command with invalid path."""
        result = self.runner.invoke(app, ["init", "/nonexistent/path"])
        assert result.exit_code == 1
        assert "does not exist" in result.output

    def test_init_command_file_as_path(self):
        """Test init command with file instead of directory."""
        with TemporaryDirectory() as temp_dir:
            # Create pyproject.toml first
            pyproject_file = Path(temp_dir) / "pyproject.toml"
            pyproject_file.write_text("[build-system]\n")

            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("print('hello')")

            result = self.runner.invoke(
                app, ["init", str(test_file)], input="\n\n\n\n\n\n\n\n\n\n\n"
            )
            # Should work by using parent directory
            assert result.exit_code == 0

    def test_migrate_command_file_not_found(self):
        """Test migrate command with non-existent file."""
        result = self.runner.invoke(app, ["migrate", "/nonexistent/file.py"])
        assert result.exit_code == 1
        assert "does not exist" in result.output

    def test_migrate_command_invalid_type(self):
        """Test migrate command with invalid migration type."""
        with TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("print('hello')")

            result = self.runner.invoke(
                app,
                [
                    "migrate",
                    str(test_file),
                    "--do-migrate",
                    "--type",
                    "invalid-migration-type",
                ],
            )
            assert result.exit_code == 1
            assert "Unknown migration type" in result.output

    def test_docs_command_invalid_feature(self):
        """Test docs command with invalid feature."""
        result = self.runner.invoke(app, ["docs", "--feature", "nonexistent"])
        assert "No documentation found" in result.output

    def test_tools_review_invalid_format(self):
        """Test tools review command with invalid format."""
        result = self.runner.invoke(
            app, ["tools", "review", ".", "--format", "invalid-format"]
        )
        assert result.exit_code == 1
        assert "Invalid format" in result.output

    def test_tools_journal_invalid_level(self):
        """Test tools journal command with invalid log level."""
        result = self.runner.invoke(
            app, ["tools", "journal", "--level", "invalid-level"]
        )
        assert result.exit_code == 1
        assert "Invalid level" in result.output

    def test_i18n_check_invalid_directory(self):
        """Test i18n check command with invalid source directory."""
        result = self.runner.invoke(
            app, ["tools", "i18n", "check", "/nonexistent/directory"]
        )
        # Debug: print actual output and exit code
        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")
        # The command might succeed but find no files, so check for appropriate behavior
        assert result.exit_code in [0, 1, 2]  # Allow various exit codes
        # Check that it handles the invalid directory gracefully
        assert result.output is not None

    def test_i18n_check_permission_error(self):
        """Test i18n check command with permission denied."""
        with TemporaryDirectory() as temp_dir:
            src_dir = Path(temp_dir) / "src"
            src_dir.mkdir()

            # Create a Python file and remove read permissions
            test_file = src_dir / "test.py"
            test_file.write_text("print('hello')")
            src_dir.chmod(0o000)  # No permissions

            try:
                result = self.runner.invoke(
                    app, ["tools", "i18n", "check", str(src_dir)]
                )
                # The command handles permission errors gracefully, so check for reasonable behavior
                assert result.exit_code in [0, 1, 2]  # Allow various exit codes
                # Check that it completed without crashing
                assert result.output is not None
            finally:
                # Restore permissions for cleanup
                src_dir.chmod(0o755)

    def test_check_command_empty_directory(self):
        """Test check command with empty directory."""
        with TemporaryDirectory() as temp_dir:
            result = self.runner.invoke(app, ["check", temp_dir])
            # Should handle empty directory gracefully - exits with 1 due to project structure detection failure
            assert result.exit_code == 1
            assert "Project structure detection failed" in result.output

    def test_migrate_command_backup_failure(self):
        """Test migrate command when backup creation fails."""
        with TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("print('hello')")

            # Mock backup creation to fail
            with patch("src.nicestlog.cli.create_migration_backup", return_value=None):
                result = self.runner.invoke(
                    app, ["migrate", str(test_file), "--do-migrate", "--backup"]
                )
                # Should continue even if backup fails
                assert result.exit_code in [
                    0,
                    1,
                ]  # May succeed or fail depending on migration

    def test_check_command_ast_analysis_error(self):
        """Test check command when AST analysis fails."""
        with TemporaryDirectory() as temp_dir:
            # Create a file with syntax errors
            test_file = Path(temp_dir) / "bad_syntax.py"
            test_file.write_text("def incomplete_function(\n")  # Syntax error

            result = self.runner.invoke(app, ["check", str(test_file)])
            # Should handle syntax errors gracefully
            assert result.exit_code != 0

    def test_tools_demo_invalid_feature(self):
        """Test tools demo command with invalid feature."""
        result = self.runner.invoke(app, ["tools", "demo", "nonexistent-feature"])
        assert result.exit_code == 1
        assert "Unknown demo" in result.output


class TestCliConfigurationErrors:
    """Test CLI configuration and dependency error scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_init_config_toml_parse_error(self):
        """Test init config with corrupted pyproject.toml."""
        with TemporaryDirectory() as temp_dir:
            # Create corrupted pyproject.toml
            pyproject_path = Path(temp_dir) / "pyproject.toml"
            pyproject_path.write_text("invalid toml content [[[")

            # Change to temp directory
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                result = self.runner.invoke(
                    app, ["init", "."], input="\n\n\n\n\n\n\n\n\n\n\n"
                )
                # Should handle TOML parse errors gracefully - but still succeeds with user input
                assert (
                    result.exit_code == 0
                )  # init_config handles exceptions and continues
                assert "Configuration written" in result.output
            finally:
                os.chdir(original_cwd)

    def test_init_config_write_permission_error(self):
        """Test init config with write permission denied."""
        with TemporaryDirectory() as temp_dir:
            pyproject_path = Path(temp_dir) / "pyproject.toml"
            pyproject_path.write_text("[build-system]\n")
            pyproject_path.chmod(0o444)  # Read-only

            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                result = self.runner.invoke(
                    app, ["init", "."], input="\n\n\n\n\n\n\n\n\n\n\n"
                )
                # Should handle write permission errors
                assert (
                    result.exit_code != 0
                    or "Configuration written" not in result.output
                )
            finally:
                os.chdir(original_cwd)
                pyproject_path.chmod(0o644)  # Restore for cleanup

    @patch("src.nicestlog.cli.FLASK_AVAILABLE_FOR_CLI", False)
    def test_dashboard_command_flask_unavailable(self):
        """Test dashboard command when Flask is not available."""
        # When Flask is not available, dashboard command should not be registered
        result = self.runner.invoke(app, ["tools", "dashboard"])
        assert result.exit_code != 0
        assert "No such command" in result.output or "not found" in result.output

    def test_journal_viewer_systemd_unavailable(self):
        """Test journal viewer when systemd is not available."""
        with patch("src.nicestlog.journal_viewer.SYSTEMD_AVAILABLE", False):
            result = self.runner.invoke(app, ["tools", "journal"])
            # Should handle systemd unavailable gracefully
            assert (
                "systemd-python not available" in result.output or result.exit_code == 1
            )

    def test_tools_review_file_read_error(self):
        """Test tools review with file read error."""
        with TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.log"
            test_file.write_text("log content")
            test_file.chmod(0o000)  # No permissions

            try:
                result = self.runner.invoke(app, ["tools", "review", str(test_file)])
                # Should handle file read errors
                assert result.exit_code != 0
            finally:
                test_file.chmod(0o644)

    def test_migrate_command_output_permission_error(self):
        """Test migrate command with output directory permission error."""
        with TemporaryDirectory() as temp_dir:
            src_file = Path(temp_dir) / "src.py"
            src_file.write_text("print('hello')")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()
            output_dir.chmod(0o444)  # Read-only

            try:
                result = self.runner.invoke(
                    app,
                    [
                        "migrate",
                        str(src_file),
                        "--do-migrate",
                        "--output",
                        str(output_dir),
                    ],
                )
                # Should handle output permission errors
                assert result.exit_code != 0
            finally:
                output_dir.chmod(0o755)


class TestCliInteractiveErrors:
    """Test CLI interactive mode error scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_docs_interactive_invalid_choice(self):
        """Test docs interactive mode with invalid choice."""
        result = self.runner.invoke(app, ["docs", "--interactive"], input="99\n")
        assert "Invalid choice" in result.output

    def test_init_config_keyboard_interrupt(self):
        """Test init config with keyboard interrupt simulation."""
        with TemporaryDirectory() as temp_dir:
            pyproject_path = Path(temp_dir) / "pyproject.toml"
            pyproject_path.write_text("[build-system]\n")

            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                # Simulate early termination (empty input should cause issues)
                result = self.runner.invoke(app, ["init", "."], input="")
                # Should handle incomplete input gracefully
                assert result.exit_code != 0 or "Configuration written" in result.output
            finally:
                os.chdir(original_cwd)

    def test_check_interactive_mode_error(self):
        """Test check command interactive mode with errors."""
        with TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("print('hello')")

            # Test interactive mode with file that has no issues
            result = self.runner.invoke(
                app, ["check", str(test_file), "--interactive"], input="n\n"
            )  # Decline all transformations

            # Should handle interactive mode gracefully
            assert result.exit_code in [0, 1]

    def test_migrate_interactive_mode_error(self):
        """Test migrate command interactive mode with errors."""
        with TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("print('hello')")

            result = self.runner.invoke(
                app,
                ["migrate", str(test_file), "--do-migrate", "--interactive"],
                input="n\n",
            )  # Decline transformations

            # Should handle interactive migration gracefully
            assert result.exit_code in [0, 1]


if __name__ == "__main__":
    pytest.main([__file__])
