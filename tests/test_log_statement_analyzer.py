"""Tests for log_statement_analyzer.py module.

This module tests AST-based log statement analysis functionality.
"""

import ast
import logging
from pathlib import Path
import tempfile

from stoggertools.log_statement_analyzer import (
    LogAnalysisResult,
    LogStatement,
    LogStatementAnalyzer,
    LogStatementOptions,
    analyze_file,
    print_analysis_summary,
)


class TestLogStatement:
    """Test LogStatement dataclass."""

    def test_log_statement_creation(self):
        """Test creating a LogStatement instance."""
        statement = LogStatement(
            line_number=10,
            method="info",
            event_id="user-login",
            has_event_id=True,
            event_id_format="dash-case",
            arguments=["'user-login'"],
            keyword_args={"user_id": "123"},
            magic_args={"_replace_msg"},
            raw_call="log.info('user-login', user_id=123, _replace_msg='User logged in')",
            issues=[],
        )

        assert statement.line_number == 10
        assert statement.method == "info"
        assert statement.event_id == "user-login"
        assert statement.has_event_id is True
        assert statement.event_id_format == "dash-case"
        assert statement.arguments == ["'user-login'"]
        assert statement.keyword_args == {"user_id": "123"}
        assert statement.magic_args == {"_replace_msg"}
        assert "user-login" in statement.raw_call
        assert statement.issues == []


class TestElementCounting:
    """Test event ID element counting functionality."""

    def test_count_event_id_elements(self):
        """Test the _count_event_id_elements method."""
        analyzer = LogStatementAnalyzer()

        # Test basic cases
        assert analyzer._count_event_id_elements("user-login") == 2
        assert analyzer._count_event_id_elements("simple") == 1
        assert analyzer._count_event_id_elements("") == 0

        # Test the problematic case from the issue
        assert (
            analyzer._count_event_id_elements(
                "debug-logging-is-enabled-check-logs-above-for-http-details",
            )
            == 10
        )

        # Test camelCase
        assert analyzer._count_event_id_elements("userLoginSuccess") == 3
        assert analyzer._count_event_id_elements("HTTPResponseError") == 3

        # Test snake_case
        assert analyzer._count_event_id_elements("user_login_failed") == 3

        # Test threshold cases
        assert analyzer._count_event_id_elements("a-b-c-d-e") == 5  # warning threshold
        assert analyzer._count_event_id_elements("a-b-c-d-e-f-g") == 7  # error threshold

        # Test mixed cases
        assert analyzer._count_event_id_elements("api-key-validation-failed-retry-needed") == 6

    def test_element_count_issues_detection(self):
        """Test that element count issues are properly detected."""
        analyzer = LogStatementAnalyzer()

        # Test warning threshold (5+ elements)
        issues_5 = analyzer._detect_issues(
            LogStatementOptions(
                method="info",
                args=["'a-b-c-d-e'"],
                kwargs={},
                magic_args=set(),
                event_id="a-b-c-d-e",
                event_id_format="dash-case",
            ),
        )
        assert any("event_id_many_elements" in issue for issue in issues_5)
        assert any("5>=5, warning" in issue for issue in issues_5)

        # Test error threshold (7+ elements)
        issues_7 = analyzer._detect_issues(
            LogStatementOptions(
                method="info",
                args=["'a-b-c-d-e-f-g'"],
                kwargs={},
                magic_args=set(),
                event_id="a-b-c-d-e-f-g",
                event_id_format="dash-case",
            ),
        )
        assert any("event_id_too_many_elements" in issue for issue in issues_7)
        assert any("7>=7, wtf!" in issue for issue in issues_7)

        # Test the problematic case
        issues_10 = analyzer._detect_issues(
            LogStatementOptions(
                method="debug",
                args=["'debug-logging-is-enabled-check-logs-above-for-http-details'"],
                kwargs={},
                magic_args=set(),
                event_id="debug-logging-is-enabled-check-logs-above-for-http-details",
                event_id_format="dash-case",
            ),
        )
        assert any("event_id_too_many_elements" in issue for issue in issues_10)
        assert any("10>=7, wtf!" in issue for issue in issues_10)

        # Test that short event IDs don't trigger issues
        issues_short = analyzer._detect_issues(
            LogStatementOptions(
                method="info",
                args=["'user-login'"],
                kwargs={},
                magic_args=set(),
                event_id="user-login",
                event_id_format="dash-case",
            ),
        )
        element_issues = [
            issue
            for issue in issues_short
            if "event_id_many_elements" in issue or "event_id_too_many_elements" in issue
        ]
        assert len(element_issues) == 0


class TestLogAnalysisResult:
    """Test LogAnalysisResult dataclass."""

    def test_log_analysis_result_creation(self):
        """Test creating a LogAnalysisResult instance."""
        statement = LogStatement(
            line_number=5,
            method="debug",
            event_id="test-event",
            has_event_id=True,
            event_id_format="dash-case",
            arguments=["'test-event'"],
            keyword_args={},
            magic_args=set(),
            raw_call="log.debug('test-event')",
            issues=["no_structured_data"],
        )

        result = LogAnalysisResult(
            file_path=Path("test.py"),
            statements=[statement],
            total_statements=1,
            statements_with_event_id=1,
            statements_without_event_id=0,
            dash_case_violations=0,
            single_string_args=1,
            magic_args_usage={},
        )

        assert result.file_path == Path("test.py")
        assert len(result.statements) == 1
        assert result.total_statements == 1
        assert result.statements_with_event_id == 1
        assert result.statements_without_event_id == 0
        assert result.dash_case_violations == 0
        assert result.single_string_args == 1
        assert result.magic_args_usage == {}


class TestLogStatementAnalyzer:
    """Test LogStatementAnalyzer AST visitor."""

    def test_analyzer_initialization(self):
        """Test analyzer initialization with default settings."""
        analyzer = LogStatementAnalyzer()

        assert analyzer.prefer_dash_case is True
        assert "info" in analyzer.log_methods
        assert "debug" in analyzer.log_methods
        assert "error" in analyzer.log_methods
        assert "_replace_msg" in analyzer.magic_args
        assert "exc_info" in analyzer.magic_args
        assert len(analyzer.statements) == 0
        assert len(analyzer.logging_imports) == 0
        assert len(analyzer.logger_variables) == 0

    def test_analyzer_initialization_custom_settings(self):
        """Test analyzer initialization with custom settings."""
        analyzer = LogStatementAnalyzer(prefer_dash_case=False)

        assert analyzer.prefer_dash_case is False
        assert "structlog" in analyzer.logging_modules
        assert "get_logger" in analyzer.logger_factory_patterns

    def test_visit_import_logging_modules(self):
        """Test detection of logging module imports."""
        code = """
import structlog
import logging
import unrelated_module
"""
        tree = ast.parse(code)
        analyzer = LogStatementAnalyzer()
        analyzer.visit(tree)

        assert "structlog" in analyzer.logging_imports
        assert "logging" in analyzer.logging_imports
        assert "unrelated_module" not in analyzer.logging_imports

    def test_visit_import_with_aliases(self):
        """Test detection of logging imports with aliases."""
        code = """
import structlog as slog
import logging as log_module
"""
        tree = ast.parse(code)
        analyzer = LogStatementAnalyzer()
        analyzer.visit(tree)

        assert "slog" in analyzer.logging_imports
        assert "log_module" in analyzer.logging_imports
        assert "structlog" not in analyzer.logging_imports
        assert "logging" not in analyzer.logging_imports

    def test_visit_importfrom_logging_modules(self):
        """Test detection of from imports from logging modules."""
        code = """
from structlog import get_logger
from logging import getLogger as get_log
"""
        tree = ast.parse(code)
        analyzer = LogStatementAnalyzer()
        analyzer.visit(tree)

        assert "get_logger" in analyzer.logging_imports
        assert "get_log" in analyzer.logging_imports

    def test_visit_assign_logger_variables(self):
        """Test detection of logger variable assignments."""
        code = """
import structlog
log = structlog.get_logger()
logger = structlog.get_logger(__name__)
my_log = get_logger()
"""
        tree = ast.parse(code)
        analyzer = LogStatementAnalyzer()
        analyzer.visit(tree)

        assert "log" in analyzer.logger_variables
        assert "logger" in analyzer.logger_variables
        assert "my_log" in analyzer.logger_variables

    def test_is_logger_factory_call_detection(self):
        """Test detection of logger factory calls."""
        analyzer = LogStatementAnalyzer()

        # Test structlog.get_logger()
        code = "structlog.get_logger()"
        tree = ast.parse(code, mode="eval")
        analyzer.logging_imports.add("structlog")
        assert analyzer._is_logger_factory_call(tree.body) is True

        # Test direct get_logger()
        code = "get_logger()"
        tree = ast.parse(code, mode="eval")
        assert analyzer._is_logger_factory_call(tree.body) is True

        # Test non-factory call
        code = "some_function()"
        tree = ast.parse(code, mode="eval")
        assert analyzer._is_logger_factory_call(tree.body) is False

    def test_is_log_call_detection(self):
        """Test detection of log method calls."""
        analyzer = LogStatementAnalyzer()
        analyzer.logger_variables.add("log")

        # Test valid log call
        code = "log.info('test')"
        tree = ast.parse(code, mode="eval")
        assert analyzer._is_log_call(tree.body) is True

        # Test invalid method name
        code = "log.invalid_method('test')"
        tree = ast.parse(code, mode="eval")
        assert analyzer._is_log_call(tree.body) is False

        # Test non-logger object
        code = "other.info('test')"
        tree = ast.parse(code, mode="eval")
        assert analyzer._is_log_call(tree.body) is False

        # Test common logger names fallback
        code = "logger.debug('test')"
        tree = ast.parse(code, mode="eval")
        assert analyzer._is_log_call(tree.body) is True

    def test_check_event_id_format_dash_case(self):
        """Test event ID format detection for dash-case."""
        analyzer = LogStatementAnalyzer()

        assert analyzer._check_event_id_format("user-login") == "dash-case"
        assert analyzer._check_event_id_format("data-processing-complete") == "dash-case"
        assert analyzer._check_event_id_format("test123-event") == "dash-case"
        assert analyzer._check_event_id_format("simple") == "dash-case"

    def test_check_event_id_format_snake_case(self):
        """Test event ID format detection for snake_case."""
        analyzer = LogStatementAnalyzer()

        assert analyzer._check_event_id_format("user_login") == "snake_case"
        assert analyzer._check_event_id_format("data_processing_complete") == "snake_case"
        assert analyzer._check_event_id_format("simple_event") == "snake_case"

    def test_check_event_id_format_camel_case(self):
        """Test event ID format detection for camelCase."""
        analyzer = LogStatementAnalyzer()

        assert analyzer._check_event_id_format("userLogin") == "camelCase"
        assert analyzer._check_event_id_format("dataProcessingComplete") == "camelCase"
        assert analyzer._check_event_id_format("simpleEvent") == "camelCase"

    def test_check_event_id_format_pascal_case(self):
        """Test event ID format detection for PascalCase."""
        analyzer = LogStatementAnalyzer()

        assert analyzer._check_event_id_format("UserLogin") == "PascalCase"
        assert analyzer._check_event_id_format("DataProcessingComplete") == "PascalCase"
        assert analyzer._check_event_id_format("SimpleEvent") == "PascalCase"

    def test_check_event_id_format_invalid(self):
        """Test event ID format detection for invalid formats."""
        analyzer = LogStatementAnalyzer()

        assert analyzer._check_event_id_format("user-Login") == "invalid"
        assert analyzer._check_event_id_format("user_Login") == "invalid"
        # Note: "123invalid" actually matches dash-case regex (numbers allowed)
        assert analyzer._check_event_id_format("123invalid") == "dash-case"
        assert analyzer._check_event_id_format("user@login") == "invalid"
        assert analyzer._check_event_id_format("") == "none"
        assert analyzer._check_event_id_format(None) == "none"

    def test_convert_to_dash_case(self):
        """Test conversion of event IDs to dash-case."""
        analyzer = LogStatementAnalyzer()

        assert analyzer._convert_to_dash_case("user_login") == "user-login"
        assert analyzer._convert_to_dash_case("userLogin") == "user-login"
        assert analyzer._convert_to_dash_case("UserLogin") == "user-login"
        assert analyzer._convert_to_dash_case("DataProcessingComplete") == "data-processing-complete"
        assert analyzer._convert_to_dash_case("already-dash-case") == "already-dash-case"
        assert analyzer._convert_to_dash_case("") == ""

    def test_detect_issues_missing_event_id(self):
        """Test detection of missing event ID issue."""
        analyzer = LogStatementAnalyzer()

        issues = analyzer._detect_issues(
            LogStatementOptions(
                method="info",
                args=[],
                kwargs={},
                magic_args=set(),
                event_id=None,
                event_id_format="none",
            ),
        )

        assert "missing_event_id" in issues

    def test_detect_issues_event_id_format_violations(self):
        """Test detection of event ID format violations."""
        analyzer = LogStatementAnalyzer()

        # Test snake_case when dash-case preferred
        issues = analyzer._detect_issues(
            LogStatementOptions(
                method="info",
                args=["'user_login'"],
                kwargs={"user_id": "123"},
                magic_args=set(),
                event_id="user_login",
                event_id_format="snake_case",
                prefer_dash_case=True,
            ),
        )

        assert any("event_id_not_dash_case" in issue for issue in issues)
        assert any("user-login" in issue for issue in issues)

    def test_detect_issues_single_string_argument(self):
        """Test detection of single string argument anti-pattern."""
        analyzer = LogStatementAnalyzer()

        issues = analyzer._detect_issues(
            LogStatementOptions(
                method="info",
                args=["'simple message'"],
                kwargs={},
                magic_args=set(),
                event_id="simple message",
                event_id_format="invalid",
            ),
        )

        assert "single_string_argument" in issues

    def test_detect_issues_fstring_in_event_id(self):
        """Test detection of f-string in event ID."""
        analyzer = LogStatementAnalyzer()

        issues = analyzer._detect_issues(
            LogStatementOptions(
                method="info",
                args=["f'user-{user_id}-login'"],
                kwargs={},
                magic_args=set(),
                event_id="user-{user_id}-login",
                event_id_format="invalid",
            ),
        )

        assert "fstring_in_event_id" in issues

    def test_detect_issues_debug_with_replace_msg(self):
        """Test detection of debug with _replace_msg issue."""
        analyzer = LogStatementAnalyzer()

        issues = analyzer._detect_issues(
            LogStatementOptions(
                method="debug",
                args=["'debug-event'"],
                kwargs={},
                magic_args={"_replace_msg"},
                event_id="debug-event",
                event_id_format="dash-case",
            ),
        )

        assert "debug_with_replace_msg" in issues

    def test_detect_issues_too_many_kwargs(self):
        """Test detection of too many keyword arguments."""
        analyzer = LogStatementAnalyzer()

        many_kwargs = {f"arg{i}": f"value{i}" for i in range(10)}

        issues = analyzer._detect_issues(
            LogStatementOptions(
                method="info",
                args=["'complex-event'"],
                kwargs=many_kwargs,
                magic_args=set(),
                event_id="complex-event",
                event_id_format="dash-case",
            ),
        )

        assert any("too_many_kwargs" in issue for issue in issues)

    def test_detect_issues_no_structured_data(self):
        """Test detection of missing structured data."""
        analyzer = LogStatementAnalyzer()

        issues = analyzer._detect_issues(
            LogStatementOptions(
                method="info",
                args=["'user-login'"],
                kwargs={},
                magic_args=set(),
                event_id="user-login",
                event_id_format="dash-case",
            ),
        )

        assert "no_structured_data" in issues

    def test_detect_issues_log_level_mismatch(self):
        """Test detection of log level and event severity mismatch."""
        analyzer = LogStatementAnalyzer()

        # Debug level with error event
        issues = analyzer._detect_issues(
            LogStatementOptions(
                method="debug",
                args=["'critical-error-occurred'"],
                kwargs={"error_code": "500"},
                magic_args=set(),
                event_id="critical-error-occurred",
                event_id_format="dash-case",
            ),
        )

        assert "debug_for_error_event" in issues

        # Error level with debug event
        issues = analyzer._detect_issues(
            LogStatementOptions(
                method="error",
                args=["'debug-info-collected'"],
                kwargs={"data": "test"},
                magic_args=set(),
                event_id="debug-info-collected",
                event_id_format="dash-case",
            ),
        )

        assert "error_level_for_info_event" in issues

    def test_detect_issues_potential_secret_leak(self):
        """Test detection of potential secret leakage."""
        analyzer = LogStatementAnalyzer()

        issues = analyzer._detect_issues(
            LogStatementOptions(
                method="info",
                args=["'user-authenticated'"],
                kwargs={"password": "secret123", "api_key": "abc123"},
                magic_args=set(),
                event_id="user-authenticated",
                event_id_format="dash-case",
            ),
        )

        secret_issues = [issue for issue in issues if "potential_secret_leak" in issue]
        assert len(secret_issues) == 2
        assert any("password" in issue for issue in secret_issues)
        assert any("api_key" in issue for issue in secret_issues)

    def test_detect_issues_event_id_too_long(self):
        """Test detection of overly long event IDs."""
        analyzer = LogStatementAnalyzer()

        long_event_id = "this-is-a-very-long-event-id-that-exceeds-fifty-characters-and-should-trigger-warning"

        issues = analyzer._detect_issues(
            LogStatementOptions(
                method="info",
                args=[f"'{long_event_id}'"],
                kwargs={"data": "test"},
                magic_args=set(),
                event_id=long_event_id,
                event_id_format="dash-case",
            ),
        )

        assert any("event_id_too_long" in issue for issue in issues)


class TestLogStatementParsing:
    """Test complete log statement parsing functionality."""

    def test_parse_simple_log_statement(self):
        """Test parsing a simple log statement."""
        code = """
import structlog
log = structlog.get_logger()
log.info("user-login", user_id=123)
"""
        tree = ast.parse(code)
        analyzer = LogStatementAnalyzer()
        analyzer.visit(tree)

        assert len(analyzer.statements) == 1
        stmt = analyzer.statements[0]
        assert stmt.method == "info"
        assert stmt.event_id == "user-login"
        assert stmt.has_event_id is True
        assert stmt.event_id_format == "dash-case"
        assert stmt.keyword_args == {"user_id": "123"}
        assert len(stmt.issues) == 0  # Should be a good log statement

    def test_parse_log_statement_with_magic_args(self):
        """Test parsing log statement with magic arguments."""
        code = """
import structlog
log = structlog.get_logger()
log.error("database-error", error_code=500, _replace_msg="Database connection failed", exc_info=True)
"""
        tree = ast.parse(code)
        analyzer = LogStatementAnalyzer()
        analyzer.visit(tree)

        assert len(analyzer.statements) == 1
        stmt = analyzer.statements[0]
        assert stmt.method == "error"
        assert stmt.event_id == "database-error"
        assert "_replace_msg" in stmt.magic_args
        assert "exc_info" in stmt.magic_args
        assert stmt.keyword_args["error_code"] == "500"

    def test_parse_log_statement_without_event_id(self):
        """Test parsing log statement without event ID."""
        code = """
import structlog
log = structlog.get_logger()
log.warning()
"""
        tree = ast.parse(code)
        analyzer = LogStatementAnalyzer()
        analyzer.visit(tree)

        assert len(analyzer.statements) == 1
        stmt = analyzer.statements[0]
        assert stmt.method == "warning"
        assert stmt.event_id is None
        assert stmt.has_event_id is False
        assert "missing_event_id" in stmt.issues

    def test_parse_multiple_log_statements(self):
        """Test parsing multiple log statements in one file."""
        code = """
import structlog
log = structlog.get_logger()

def process_user(user_id):
    log.info("user-processing-started", user_id=user_id)
    try:
        # Some processing
        log.debug("user-data-validated", user_id=user_id)
        log.info("user-processing-completed", user_id=user_id)
    except Exception:
        log.error("user-processing-failed", user_id=user_id, exc_info=True)
"""
        tree = ast.parse(code)
        analyzer = LogStatementAnalyzer()
        analyzer.visit(tree)

        assert len(analyzer.statements) == 4
        methods = [stmt.method for stmt in analyzer.statements]
        assert "info" in methods
        assert "debug" in methods
        assert "error" in methods

        event_ids = [stmt.event_id for stmt in analyzer.statements]
        assert "user-processing-started" in event_ids
        assert "user-data-validated" in event_ids
        assert "user-processing-completed" in event_ids
        assert "user-processing-failed" in event_ids

    def test_parse_chained_logger_call(self):
        """Test parsing chained logger calls like structlog.get_logger().info()."""
        code = """
import structlog
structlog.get_logger().info("direct-call", data="test")
"""
        tree = ast.parse(code)
        analyzer = LogStatementAnalyzer()
        analyzer.visit(tree)

        assert len(analyzer.statements) == 1
        stmt = analyzer.statements[0]
        assert stmt.method == "info"
        assert stmt.event_id == "direct-call"
        assert stmt.keyword_args == {"data": "'test'"}

    def test_parse_self_logger_attribute(self):
        """Test parsing self.logger.info() style calls."""
        code = """
class MyClass:
    def __init__(self):
        import structlog
        self.logger = structlog.get_logger()
    
    def process(self):
        self.logger.info("method-called", class_name="MyClass")
"""
        tree = ast.parse(code)
        analyzer = LogStatementAnalyzer()
        analyzer.visit(tree)

        assert len(analyzer.statements) == 1
        stmt = analyzer.statements[0]
        assert stmt.method == "info"
        assert stmt.event_id == "method-called"

    def test_parse_complex_expressions_in_args(self):
        """Test parsing log statements with complex expressions."""
        code = """
import structlog
log = structlog.get_logger()
log.info("complex-data", 
         computed_value=len(some_list) + 10,
         formatted_string=f"User {user.name}",
         dict_access=config["database"]["host"])
"""
        tree = ast.parse(code)
        analyzer = LogStatementAnalyzer()
        analyzer.visit(tree)

        assert len(analyzer.statements) == 1
        stmt = analyzer.statements[0]
        assert stmt.method == "info"
        assert stmt.event_id == "complex-data"
        assert "computed_value" in stmt.keyword_args
        assert "formatted_string" in stmt.keyword_args
        assert "dict_access" in stmt.keyword_args


class TestAnalyzeFileFunction:
    """Test the analyze_file function."""

    def test_analyze_file_with_valid_python(self):
        """Test analyzing a valid Python file."""
        code = """
import structlog
log = structlog.get_logger()

def main():
    log.info("application-started", version="1.0")
    log.debug("debug-info", data={"key": "value"})
    log.warning("potential-issue", severity="low")
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            result = analyze_file(temp_file)

            assert result.file_path == temp_file
            assert result.total_statements == 3
            assert result.statements_with_event_id == 3
            assert result.statements_without_event_id == 0
            assert result.dash_case_violations == 0
            assert len(result.statements) == 3

            # Check individual statements
            event_ids = [stmt.event_id for stmt in result.statements]
            assert "application-started" in event_ids
            assert "debug-info" in event_ids
            assert "potential-issue" in event_ids

        finally:
            temp_file.unlink()

    def test_analyze_file_with_issues(self):
        """Test analyzing a file with various logging issues."""
        code = """
import structlog
log = structlog.get_logger()

def problematic_logging():
    log.info()  # Missing event ID
    log.debug("user_login", user_id=123)  # snake_case event ID
    log.error("Simple message")  # Single string argument
    log.info("user-authenticated", password="secret123")  # Potential secret leak
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            result = analyze_file(temp_file)

            assert result.total_statements == 4
            assert result.statements_with_event_id == 3
            assert result.statements_without_event_id == 1
            # "Simple message" has spaces so it's invalid format, "user_login" is snake_case
            assert result.dash_case_violations == 2  # Both "user_login" and "Simple message"
            assert result.single_string_args == 1

            # Check that issues were detected
            all_issues = []
            for stmt in result.statements:
                all_issues.extend(stmt.issues)

            assert any("missing_event_id" in issue for issue in all_issues)
            assert any("event_id_not_dash_case" in issue for issue in all_issues)
            assert any("single_string_argument" in issue for issue in all_issues)
            assert any("potential_secret_leak" in issue for issue in all_issues)

        finally:
            temp_file.unlink()

    def test_analyze_file_with_syntax_error(self):
        """Test analyzing a file with syntax errors."""
        invalid_code = """
import structlog
log = structlog.get_logger()

def invalid_function(
    # Missing closing parenthesis and colon
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(invalid_code)
            temp_file = Path(f.name)

        try:
            result = analyze_file(temp_file)

            # Should return empty result on syntax error
            assert result.file_path == temp_file
            assert result.total_statements == 0
            assert result.statements_with_event_id == 0
            assert result.statements_without_event_id == 0
            assert len(result.statements) == 0

        finally:
            temp_file.unlink()

    def test_analyze_file_nonexistent(self):
        """Test analyzing a non-existent file."""
        nonexistent_file = Path("nonexistent_file.py")

        result = analyze_file(nonexistent_file)

        # Should return empty result on file not found
        assert result.file_path == nonexistent_file
        assert result.total_statements == 0
        assert result.statements_with_event_id == 0
        assert result.statements_without_event_id == 0
        assert len(result.statements) == 0

    def test_analyze_file_prefer_snake_case(self):
        """Test analyzing with snake_case preference."""
        code = """
import structlog
log = structlog.get_logger()
log.info("user_login", user_id=123)  # snake_case should be OK
log.debug("user-logout", user_id=123)  # dash-case should still be OK
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            result = analyze_file(temp_file, prefer_dash_case=False)

            assert result.total_statements == 2
            # dash_case_violations counts non-dash-case formats regardless of preference
            assert result.dash_case_violations == 1  # "user_login" is snake_case

            # Check that snake_case doesn't trigger format violation
            snake_case_stmt = next(stmt for stmt in result.statements if stmt.event_id == "user_login")
            format_issues = [issue for issue in snake_case_stmt.issues if "event_id_not_dash_case" in issue]
            assert len(format_issues) == 0

        finally:
            temp_file.unlink()


class TestPrintAnalysisSummary:
    """Test the print_analysis_summary function."""

    def test_print_analysis_summary_basic(self, caplog):
        """Test basic analysis summary printing."""
        statements = [
            LogStatement(
                line_number=5,
                method="info",
                event_id="test-event",
                has_event_id=True,
                event_id_format="dash-case",
                arguments=["'test-event'"],
                keyword_args={"data": "123"},
                magic_args=set(),
                raw_call="log.info('test-event', data=123)",
                issues=[],
            ),
        ]

        result = LogAnalysisResult(
            file_path=Path("test.py"),
            statements=statements,
            total_statements=1,
            statements_with_event_id=1,
            statements_without_event_id=0,
            dash_case_violations=0,
            single_string_args=0,
            magic_args_usage={},
        )

        caplog.set_level(logging.INFO)
        print_analysis_summary(result)

        assert "📁 test.py" in caplog.text
        assert "Total log statements: 1" in caplog.text
        assert "With event ID: 1" in caplog.text
        assert "Without event ID: 0" in caplog.text

    def test_print_analysis_summary_with_issues(self, caplog):
        """Test analysis summary printing with issues."""
        statements = [
            LogStatement(
                line_number=5,
                method="info",
                event_id=None,
                has_event_id=False,
                event_id_format="none",
                arguments=[],
                keyword_args={},
                magic_args=set(),
                raw_call="log.info()",
                issues=["missing_event_id"],
            ),
        ]

        result = LogAnalysisResult(
            file_path=Path("problematic.py"),
            statements=statements,
            total_statements=1,
            statements_with_event_id=0,
            statements_without_event_id=1,
            dash_case_violations=0,
            single_string_args=1,
            magic_args_usage={},
        )

        caplog.set_level(logging.INFO)
        print_analysis_summary(result)

        assert "📁 problematic.py" in caplog.text
        assert "❌ Single string arguments: 1" in caplog.text

    def test_print_analysis_summary_empty_file(self, capsys):
        """Test analysis summary for file with no log statements."""
        result = LogAnalysisResult(
            file_path=Path("empty.py"),
            statements=[],
            total_statements=0,
            statements_with_event_id=0,
            statements_without_event_id=0,
            dash_case_violations=0,
            single_string_args=0,
            magic_args_usage={},
        )

        print_analysis_summary(result)
        captured = capsys.readouterr()

        # Should print nothing for empty files
        assert captured.out == ""

    def test_print_analysis_summary_verbose(self, caplog):
        """Test verbose analysis summary printing."""
        statements = [
            LogStatement(
                line_number=10,
                method="error",
                event_id="test-error",
                has_event_id=True,
                event_id_format="dash-case",
                arguments=["'test-error'"],
                keyword_args={"error_code": "500"},
                magic_args={"exc_info"},
                raw_call="log.error('test-error', error_code=500, exc_info=True)",
                issues=["some_issue"],
            ),
        ]

        result = LogAnalysisResult(
            file_path=Path("detailed.py"),
            statements=statements,
            total_statements=1,
            statements_with_event_id=1,
            statements_without_event_id=0,
            dash_case_violations=0,
            single_string_args=0,
            magic_args_usage={"exc_info": 1},
        )

        caplog.set_level(logging.INFO)
        print_analysis_summary(result, verbose=True)

        assert "📁 detailed.py" in caplog.text
        assert "🪄 Magic args: exc_info:1" in caplog.text
        assert "Detailed statements:" in caplog.text
        assert "L10: error('test-error')" in caplog.text
        assert "magic:['exc_info']" in caplog.text
        assert "❌ some_issue" in caplog.text
