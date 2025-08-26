"""
Integration tests for AST-enhanced CLI commands.
Tests the new --ast, --interactive, --complexity, and --pattern options.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from nicestlog.cli import app


class TestCheckCommandASTIntegration:
    """Test the enhanced check command with AST features."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_check_with_ast_analysis(self):
        """Test check command with --ast flag."""
        # Create a test Python file
        test_file = self.temp_path / "test.py"
        test_file.write_text("""
import logging

def test_function():
    print("Hello world")
    logging.info("This is a log message")
    return True
""")

        with patch("nicestlog.cli.AdvancedAssistant") as mock_assistant_class:
            mock_assistant = MagicMock()
            mock_assistant_class.return_value = mock_assistant

            # Mock analysis result
            mock_result = MagicMock()
            mock_result.file_path = test_file
            mock_result.lines_of_code = 6
            mock_result.function_count = 1
            mock_result.class_count = 0
            mock_result.complexity_score = 2.5
            mock_result.issues = [
                "Found print statement that could be structured logging"
            ]
            mock_assistant.analyze_file.return_value = mock_result

            result = self.runner.invoke(app, ["check", str(test_file), "--ast"])

            assert result.exit_code == 1  # Issues found
            assert "AST analysis" in result.stdout
            assert "Lines of Code" in result.stdout
            assert mock_assistant.analyze_file.called

    def test_check_with_complexity_analysis(self):
        """Test check command with --complexity flag."""
        test_file = self.temp_path / "complex.py"
        test_file.write_text("""
def complex_function(x):
    if x > 10:
        if x > 20:
            if x > 30:
                return "very high"
            return "high"
        return "medium"
    return "low"
""")

        with patch("nicestlog.cli.AdvancedAssistant") as mock_assistant_class:
            mock_assistant = MagicMock()
            mock_assistant_class.return_value = mock_assistant

            mock_result = MagicMock()
            mock_result.file_path = test_file
            mock_result.complexity_score = 8.5
            mock_result.issues = []
            mock_result.lines_of_code = 8
            mock_result.function_count = 1
            mock_result.class_count = 0
            mock_assistant.analyze_file.return_value = mock_result

            result = self.runner.invoke(app, ["check", str(test_file), "--complexity"])

            assert result.exit_code == 0
            assert "Complexity Score" in result.stdout
            assert "8.5" in result.stdout

    def test_check_with_patterns(self):
        """Test check command with --pattern flag."""
        test_file = self.temp_path / "patterns.py"
        test_file.write_text("""
import logging

def test():
    print("Debug info")
    logging.warning("Something happened")
""")

        with patch("nicestlog.cli.AdvancedAssistant") as mock_assistant_class:
            mock_assistant = MagicMock()
            mock_assistant_class.return_value = mock_assistant

            # Mock patterns
            mock_pattern = MagicMock()
            mock_pattern.name = "logging_quality"
            mock_pattern.enabled = False
            mock_assistant.patterns = [mock_pattern]

            mock_result = MagicMock()
            mock_result.issues = []
            mock_result.file_path = test_file
            mock_result.lines_of_code = 5
            mock_result.function_count = 1
            mock_result.class_count = 0
            mock_result.complexity_score = 1.0
            mock_assistant.analyze_file.return_value = mock_result

            result = self.runner.invoke(
                app, ["check", str(test_file), "--pattern", "logging"]
            )

            assert result.exit_code == 0
            assert mock_pattern.enabled  # Pattern should be enabled

    @patch("nicestlog.cli.InteractiveTransformer")
    def test_check_interactive_mode(self, mock_transformer_class):
        """Test check command with --interactive flag."""
        test_file = self.temp_path / "interactive.py"
        test_file.write_text("""
def test():
    print("Hello")
""")

        mock_transformer = MagicMock()
        mock_transformer_class.return_value = mock_transformer

        with patch("nicestlog.cli.AdvancedAssistant") as mock_assistant_class:
            mock_assistant = MagicMock()
            mock_assistant_class.return_value = mock_assistant

            mock_result = MagicMock()
            mock_result.issues = ["print statement found"]
            mock_result.file_path = test_file
            mock_result.lines_of_code = 2
            mock_result.function_count = 1
            mock_result.class_count = 0
            mock_result.complexity_score = 1.0
            mock_assistant.analyze_file.return_value = mock_result

            result = self.runner.invoke(
                app, ["check", str(test_file), "--interactive", "--ast"]
            )

            assert result.exit_code == 1  # Issues found
            assert "interactive mode" in result.stdout.lower()
            assert mock_transformer.transform_file_interactive.called


class TestFixCommandASTIntegration:
    """Test the new fix command with AST transformations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_fix_with_ast_transforms(self):
        """Test fix command with AST transformations."""
        test_file = self.temp_path / "fix_test.py"
        test_file.write_text("""
def test():
    print("Debug message")
    return True
""")

        with patch("nicestlog.cli.AdvancedAssistant") as mock_assistant_class:
            mock_assistant = MagicMock()
            mock_assistant_class.return_value = mock_assistant

            mock_result = MagicMock()
            mock_result.file_path = test_file
            mock_result.changes_made = True
            mock_result.changes = ["Converted print to log.info"]
            mock_result.transformed_code = 'import structlog\nlog = structlog.get_logger()\n\ndef test():\n    log.info("debug-message", message="Debug message")\n    return True'
            mock_assistant.transform_file.return_value = mock_result

            result = self.runner.invoke(app, ["fix", str(test_file)])

            assert result.exit_code == 0
            assert "AST-based fixes" in result.stdout
            assert mock_assistant.transform_file.called

    def test_fix_dry_run(self):
        """Test fix command with --dry-run flag."""
        test_file = self.temp_path / "dry_run_test.py"
        test_file.write_text("""
print("This should be fixed")
""")

        with patch("nicestlog.cli.AdvancedAssistant") as mock_assistant_class:
            mock_assistant = MagicMock()
            mock_assistant_class.return_value = mock_assistant

            mock_result = MagicMock()
            mock_result.file_path = test_file
            mock_result.changes_made = True
            mock_result.changes = ["Convert print to structured log"]
            mock_result.transformed_code = 'import structlog\nlog = structlog.get_logger()\nlog.info("output", message="This should be fixed")'
            mock_assistant.transform_file.return_value = mock_result

            result = self.runner.invoke(app, ["fix", str(test_file), "--dry-run"])

            assert result.exit_code == 0
            assert "Preview" in result.stdout
            mock_assistant.transform_file.assert_called_with(test_file, dry_run=True)

    @patch("nicestlog.cli.InteractiveTransformer")
    def test_fix_interactive_mode(self, mock_transformer_class):
        """Test fix command with --interactive flag."""
        test_file = self.temp_path / "interactive_fix.py"
        test_file.write_text("""
def test():
    print("Interactive fix test")
""")

        mock_transformer = MagicMock()
        mock_transformer_class.return_value = mock_transformer

        result = self.runner.invoke(app, ["fix", str(test_file), "--interactive"])

        assert result.exit_code == 0
        assert "interactive fixing" in result.stdout.lower()
        assert mock_transformer.transform_file_interactive.called

    def test_fix_with_patterns(self):
        """Test fix command with specific patterns."""
        test_file = self.temp_path / "pattern_fix.py"
        test_file.write_text("""
import logging
logging.info("test")
""")

        with patch("nicestlog.cli.AdvancedAssistant") as mock_assistant_class:
            mock_assistant = MagicMock()
            mock_assistant_class.return_value = mock_assistant

            # Mock patterns
            mock_pattern = MagicMock()
            mock_pattern.name = "logging_calls"
            mock_pattern.enabled = False
            mock_assistant.patterns = [mock_pattern]

            mock_result = MagicMock()
            mock_result.changes_made = False
            mock_result.changes = []
            mock_assistant.transform_file.return_value = mock_result

            result = self.runner.invoke(
                app, ["fix", str(test_file), "--pattern", "logging"]
            )

            assert result.exit_code == 0
            assert mock_pattern.enabled  # Pattern should be enabled


class TestMigrateCommandASTIntegration:
    """Test the enhanced migrate command with AST transformations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_migrate_print_to_structlog(self):
        """Test migrate command for print-to-structlog migration (analysis by default)."""
        test_file = self.temp_path / "migrate_test.py"
        test_file.write_text("""
def hello():
    print("Hello world")
    print(f"User {user_id} logged in")
""")

        with patch(
            "nicestlog.project_analyzer.analyze_project_for_agents"
        ) as mock_analyzer:
            # Create a more complete mock that matches ProjectAnalysisResult structure
            mock_result = MagicMock()
            mock_result.project_path = str(test_file)
            mock_result.to_json.return_value = (
                '{"recommendations": ["Convert print statements"]}'
            )

            # Mock the complexity object
            mock_complexity = MagicMock()
            mock_complexity.total_files = 1
            mock_complexity.python_files = 1
            mock_complexity.total_lines = 4
            mock_complexity.complexity_category = "simple"
            mock_result.complexity = mock_complexity

            # Mock the dependencies object
            mock_deps = MagicMock()
            mock_deps.package_manager = "pip"
            mock_deps.has_logging = False
            mock_deps.has_structlog = False
            mock_deps.has_loguru = False
            mock_deps.has_other_logging = []
            mock_result.dependencies = mock_deps

            # Mock logging patterns
            mock_result.logging_patterns = []

            # Mock recommendation
            mock_rec = MagicMock()
            mock_rec.strategy = "print-to-structlog"
            mock_rec.priority = "high"
            mock_rec.estimated_effort = "low"
            mock_rec.recommended_approach = "automatic"
            mock_rec.risk_level = "low"
            mock_rec.steps = ["Convert print statements", "Add structlog imports"]
            mock_result.recommendation = mock_rec

            # Mock warnings
            mock_result.warnings = []

            mock_analyzer.return_value = mock_result

            result = self.runner.invoke(app, ["migrate", str(test_file)])

            assert result.exit_code == 0
            assert "Project Analysis" in result.stdout
            assert "To apply changes, run:" in result.stdout
            assert "--do-migrate" in result.stdout

    def test_migrate_dry_run(self):
        """Test migrate command with --do-migrate --dry-run flags."""
        test_file = self.temp_path / "migrate_dry.py"
        test_file.write_text("""
print("Test migration")
""")

        # Note: --dry-run is not a valid flag for migrate command in new structure
        # The default behavior is analysis only (safe), so we test that
        with patch(
            "nicestlog.project_analyzer.analyze_project_for_agents"
        ) as mock_analyzer:
            mock_result = MagicMock()
            mock_result.project_path = str(test_file)
            mock_result.to_json.return_value = (
                '{"recommendations": ["Convert print statements"]}'
            )

            # Mock the complexity object
            mock_complexity = MagicMock()
            mock_complexity.total_files = 1
            mock_complexity.python_files = 1
            mock_complexity.total_lines = 4
            mock_complexity.complexity_category = "simple"
            mock_result.complexity = mock_complexity

            # Mock the dependencies object
            mock_deps = MagicMock()
            mock_deps.package_manager = "pip"
            mock_deps.has_logging = False
            mock_deps.has_structlog = False
            mock_deps.has_loguru = False
            mock_deps.has_other_logging = []
            mock_result.dependencies = mock_deps

            # Mock logging patterns
            mock_result.logging_patterns = []

            # Mock recommendation
            mock_rec = MagicMock()
            mock_rec.strategy = "print-to-structlog"
            mock_rec.priority = "high"
            mock_rec.estimated_effort = "low"
            mock_rec.recommended_approach = "automatic"
            mock_rec.risk_level = "low"
            mock_rec.steps = ["Convert print statements", "Add structlog imports"]
            mock_result.recommendation = mock_rec

            # Mock warnings
            mock_result.warnings = []

            mock_analyzer.return_value = mock_result

            result = self.runner.invoke(app, ["migrate", str(test_file)])

            assert result.exit_code == 0
            assert "Project Analysis" in result.stdout
            assert "To apply changes, run:" in result.stdout
            assert "--do-migrate" in result.stdout

    @patch("nicestlog.cli.InteractiveTransformer")
    def test_migrate_interactive_mode(self, mock_transformer_class):
        """Test migrate command with --interactive flag (analysis mode)."""
        test_file = self.temp_path / "migrate_interactive.py"
        test_file.write_text("""
print("Interactive migration test")
""")

        mock_transformer = MagicMock()
        mock_transformer_class.return_value = mock_transformer

        with patch(
            "nicestlog.project_analyzer.analyze_project_for_agents"
        ) as mock_analyzer:
            mock_result = MagicMock()
            mock_result.project_path = str(test_file)
            mock_result.to_json.return_value = (
                '{"recommendations": ["Interactive migration available"]}'
            )

            # Mock the complexity object
            mock_complexity = MagicMock()
            mock_complexity.total_files = 1
            mock_complexity.python_files = 1
            mock_complexity.total_lines = 4
            mock_complexity.complexity_category = "simple"
            mock_result.complexity = mock_complexity

            # Mock the dependencies object
            mock_deps = MagicMock()
            mock_deps.package_manager = "pip"
            mock_deps.has_logging = False
            mock_deps.has_structlog = False
            mock_deps.has_loguru = False
            mock_deps.has_other_logging = []
            mock_result.dependencies = mock_deps

            # Mock logging patterns
            mock_result.logging_patterns = []

            # Mock recommendation
            mock_rec = MagicMock()
            mock_rec.strategy = "print-to-structlog"
            mock_rec.priority = "high"
            mock_rec.estimated_effort = "low"
            mock_rec.recommended_approach = "automatic"
            mock_rec.risk_level = "low"
            mock_rec.steps = ["Convert print statements", "Add structlog imports"]
            mock_result.recommendation = mock_rec

            # Mock warnings
            mock_result.warnings = []

            mock_analyzer.return_value = mock_result

            result = self.runner.invoke(
                app, ["migrate", str(test_file), "--interactive"]
            )

            assert result.exit_code == 0
            assert "Project Analysis" in result.stdout
            # Interactive mode is only available with --do-migrate
            assert "--do-migrate" in result.stdout

    def test_migrate_directory(self):
        """Test migrate command on a directory (analysis mode)."""
        # Create test directory with Python files
        test_dir = self.temp_path / "test_project"
        test_dir.mkdir()

        (test_dir / "file1.py").write_text('print("File 1")')
        (test_dir / "file2.py").write_text('print("File 2")')

        with patch(
            "nicestlog.project_analyzer.analyze_project_for_agents"
        ) as mock_analyzer:
            mock_result = MagicMock()
            mock_result.project_path = str(test_dir)
            mock_result.to_json.return_value = (
                '{"recommendations": ["Convert print statements in multiple files"]}'
            )

            # Mock the complexity object
            mock_complexity = MagicMock()
            mock_complexity.total_files = 2
            mock_complexity.python_files = 2
            mock_complexity.total_lines = 8
            mock_complexity.complexity_category = "simple"
            mock_result.complexity = mock_complexity

            # Mock the dependencies object
            mock_deps = MagicMock()
            mock_deps.package_manager = "pip"
            mock_deps.has_logging = False
            mock_deps.has_structlog = False
            mock_deps.has_loguru = False
            mock_deps.has_other_logging = []
            mock_result.dependencies = mock_deps

            # Mock logging patterns
            mock_result.logging_patterns = []

            # Mock recommendation
            mock_rec = MagicMock()
            mock_rec.strategy = "print-to-structlog"
            mock_rec.priority = "high"
            mock_rec.estimated_effort = "low"
            mock_rec.recommended_approach = "automatic"
            mock_rec.risk_level = "low"
            mock_rec.steps = ["Convert print statements", "Add structlog imports"]
            mock_result.recommendation = mock_rec

            # Mock warnings
            mock_result.warnings = []

            mock_analyzer.return_value = mock_result

            result = self.runner.invoke(app, ["migrate", str(test_dir)])

            assert result.exit_code == 0
            assert "Project Analysis" in result.stdout
            assert mock_analyzer.called

    def test_migrate_with_output_directory(self):
        """Test migrate command with --output flag (analysis mode)."""
        test_file = self.temp_path / "source.py"
        output_dir = self.temp_path / "migrated"

        test_file.write_text('print("Source file")')

        with patch(
            "nicestlog.project_analyzer.analyze_project_for_agents"
        ) as mock_analyzer:
            mock_result = MagicMock()
            mock_result.project_path = str(test_file)
            mock_result.to_json.return_value = (
                '{"recommendations": ["Convert print to structured logging"]}'
            )

            # Mock the complexity object
            mock_complexity = MagicMock()
            mock_complexity.total_files = 1
            mock_complexity.python_files = 1
            mock_complexity.total_lines = 4
            mock_complexity.complexity_category = "simple"
            mock_result.complexity = mock_complexity

            # Mock the dependencies object
            mock_deps = MagicMock()
            mock_deps.package_manager = "pip"
            mock_deps.has_logging = False
            mock_deps.has_structlog = False
            mock_deps.has_loguru = False
            mock_deps.has_other_logging = []
            mock_result.dependencies = mock_deps

            # Mock logging patterns
            mock_result.logging_patterns = []

            # Mock recommendation
            mock_rec = MagicMock()
            mock_rec.strategy = "print-to-structlog"
            mock_rec.priority = "high"
            mock_rec.estimated_effort = "low"
            mock_rec.recommended_approach = "automatic"
            mock_rec.risk_level = "low"
            mock_rec.steps = ["Convert print statements", "Add structlog imports"]
            mock_result.recommendation = mock_rec

            # Mock warnings
            mock_result.warnings = []

            mock_analyzer.return_value = mock_result

            result = self.runner.invoke(
                app, ["migrate", str(test_file), "--output", str(output_dir)]
            )

            assert result.exit_code == 0
            assert "Project Analysis" in result.stdout
            # Output directory is only used when actually migrating with --do-migrate

    def test_migrate_different_types(self):
        """Test migrate command with different migration types (analysis mode)."""
        test_file = self.temp_path / "logging_test.py"
        test_file.write_text("""
import logging
logging.info("Test message")
""")

        with patch(
            "nicestlog.project_analyzer.analyze_project_for_agents"
        ) as mock_analyzer:
            mock_result = MagicMock()
            mock_result.project_path = str(test_file)
            mock_result.to_json.return_value = (
                '{"recommendations": ["Convert logging to structlog"]}'
            )

            # Mock the complexity object
            mock_complexity = MagicMock()
            mock_complexity.total_files = 1
            mock_complexity.python_files = 1
            mock_complexity.total_lines = 4
            mock_complexity.complexity_category = "simple"
            mock_result.complexity = mock_complexity

            # Mock the dependencies object
            mock_deps = MagicMock()
            mock_deps.package_manager = "pip"
            mock_deps.has_logging = True
            mock_deps.has_structlog = False
            mock_deps.has_loguru = False
            mock_deps.has_other_logging = []
            mock_result.dependencies = mock_deps

            # Mock logging patterns
            mock_result.logging_patterns = []

            # Mock recommendation
            mock_rec = MagicMock()
            mock_rec.strategy = "logging-to-structlog"
            mock_rec.priority = "high"
            mock_rec.estimated_effort = "medium"
            mock_rec.recommended_approach = "automatic"
            mock_rec.risk_level = "low"
            mock_rec.steps = ["Convert logging calls", "Add structlog imports"]
            mock_result.recommendation = mock_rec

            # Mock warnings
            mock_result.warnings = []

            mock_analyzer.return_value = mock_result

            result = self.runner.invoke(
                app, ["migrate", str(test_file), "--type", "logging-to-structlog"]
            )

            assert result.exit_code == 0
            assert "Project Analysis" in result.stdout
            # Type is only used when actually migrating with --do-migrate

    def test_migrate_with_wrapper_warnings(self):
        """Test migrate command detects and warns about log wrapper anti-patterns."""
        test_file = self.temp_path / "wrapper_test.py"
        test_file.write_text("""
def log_debug(message):
    print(f"DEBUG: {message}")

def write_info(msg):
    logging.info(msg)

def emit_warning(text):
    logger.warning(text)

def main():
    log_debug("Starting application")
    write_info("Processing data")
    emit_warning("Low disk space")
""")

        with patch(
            "nicestlog.project_analyzer.analyze_project_for_agents"
        ) as mock_analyzer:
            mock_result = MagicMock()
            mock_result.project_path = str(test_file)
            mock_result.to_json.return_value = (
                '{"recommendations": ["Convert wrapper functions to direct logging"]}'
            )

            # Mock the complexity object
            mock_complexity = MagicMock()
            mock_complexity.total_files = 1
            mock_complexity.python_files = 1
            mock_complexity.total_lines = 12
            mock_complexity.complexity_category = "simple"
            mock_result.complexity = mock_complexity

            # Mock the dependencies object
            mock_deps = MagicMock()
            mock_deps.package_manager = "pip"
            mock_deps.has_logging = True
            mock_deps.has_structlog = False
            mock_deps.has_loguru = False
            mock_deps.has_other_logging = []
            mock_result.dependencies = mock_deps

            # Mock logging patterns with wrapper patterns
            from nicestlog.project_analyzer import LoggingPattern
            mock_result.logging_patterns = [
                LoggingPattern(
                    pattern_type="wrapper",
                    file_path=str(test_file),
                    line_number=2,
                    code_snippet="def log_debug(message):",
                    severity="medium",
                    migration_priority=7,
                ),
                LoggingPattern(
                    pattern_type="wrapper",
                    file_path=str(test_file),
                    line_number=5,
                    code_snippet="def write_info(msg):",
                    severity="medium",
                    migration_priority=7,
                ),
                LoggingPattern(
                    pattern_type="wrapper",
                    file_path=str(test_file),
                    line_number=8,
                    code_snippet="def emit_warning(text):",
                    severity="medium",
                    migration_priority=7,
                ),
            ]

            # Mock recommendation
            mock_rec = MagicMock()
            mock_rec.strategy = "logging-to-structlog"
            mock_rec.priority = "high"
            mock_rec.estimated_effort = "medium"
            mock_rec.recommended_approach = "manual"
            mock_rec.risk_level = "medium"
            mock_rec.steps = ["Remove wrapper functions", "Use direct logging calls"]
            mock_result.recommendation = mock_rec

            # Mock warnings including wrapper warning
            mock_result.warnings = [
                "Log wrapper anti-patterns detected (3 functions) - "
                "consider using log.* calls directly instead of wrapper functions"
            ]

            mock_analyzer.return_value = mock_result

            result = self.runner.invoke(app, ["migrate", str(test_file)])

            assert result.exit_code == 0
            assert "Project Analysis" in result.stdout
            # Check that warnings are displayed (the exact format may vary)
            assert "wrapper" in result.stdout.lower() or "Wrapper" in result.stdout
            # Check that the warning count is shown
            assert "3" in result.stdout




class TestBackwardCompatibility:
    """Test that existing functionality still works."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_check_without_ast_still_works(self):
        """Test that check command without AST flags still works."""
        test_file = self.temp_path / "basic_check.py"
        test_file.write_text("""
import structlog
log = structlog.get_logger()

def test():
    log.info("test-message")
""")

        with patch("nicestlog.linter.lint_directory") as mock_lint:
            mock_lint.return_value = True

            result = self.runner.invoke(app, ["check", str(test_file)])

            assert result.exit_code == 0
            assert "basic linting" in result.stdout.lower()
            assert mock_lint.called

    def test_existing_commands_unchanged(self):
        """Test that existing commands like lint, dashboard etc. are unchanged."""
        # Test lint command
        result = self.runner.invoke(app, ["lint", "--help"])
        assert result.exit_code == 0
        assert "Check logging coverage" in result.stdout

        # Test dashboard command
        result = self.runner.invoke(app, ["dashboard", "--help"])
        assert result.exit_code == 0
        assert "Start the web dashboard" in result.stdout

        # Test journal command
        result = self.runner.invoke(app, ["journal", "--help"])
        assert result.exit_code == 0
        assert "Beautiful systemd journal viewer" in result.stdout
