"""AST-based log statement analyzer for nicestlog.

Analyzes log statements to detect common issues and patterns.
"""

import ast
from dataclasses import dataclass
from pathlib import Path
import re


@dataclass
class LogStatement:
    """Represents a parsed log statement."""

    line_number: int
    method: str  # info, debug, warning, error, etc.
    event_id: str | None
    has_event_id: bool
    event_id_format: str  # "dash-case", "snake_case", "camelCase", "invalid"
    arguments: list[str]
    keyword_args: dict[str, str]
    magic_args: set[str]  # _replace_msg, exc_info, etc.
    raw_call: str
    issues: list[str]


@dataclass
class LogAnalysisResult:
    """Results of analyzing log statements in a file."""

    file_path: Path
    statements: list[LogStatement]
    total_statements: int
    statements_with_event_id: int
    statements_without_event_id: int
    dash_case_violations: int
    single_string_args: int
    magic_args_usage: dict[str, int]


class LogStatementAnalyzer(ast.NodeVisitor):
    """AST visitor that analyzes log statements."""

    def __init__(self, prefer_dash_case: bool = True):
        self.statements: list[LogStatement] = []
        self.prefer_dash_case = prefer_dash_case
        self.log_methods = {
            "info",
            "debug",
            "warning",
            "warn",
            "error",
            "critical",
            "exception",
            "trace",
        }
        self.magic_args = {"_replace_msg", "exc_info", "_structured", "_level", "_name"}

        # Track logging imports and logger variables
        self.logging_imports: set[str] = set()  # e.g., {'logging', 'structlog'}
        self.logger_variables: set[str] = set()  # e.g., {'log', 'logger', 'my_logger'}
        self.logging_modules = {"logging", "structlog", "logbook", "eliot"}
        self.logger_factory_patterns = {
            "get_logger",
            "getLogger",
            "logger",
            "Logger",
            "new",
        }

    def visit_Import(self, node: ast.Import) -> None:
        """Track logging module imports."""
        for alias in node.names:
            if alias.name in self.logging_modules:
                self.logging_imports.add(alias.asname or alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Track logging imports from modules."""
        if node.module in self.logging_modules:
            for alias in node.names:
                self.logging_imports.add(alias.asname or alias.name)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Track logger variable assignments."""
        if isinstance(node.value, ast.Call) and self._is_logger_factory_call(
            node.value,
        ):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.logger_variables.add(target.id)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Visit function calls to detect log statements."""
        if self._is_log_call(node):
            statement = self._parse_log_statement(node, self.prefer_dash_case)
            self.statements.append(statement)

        self.generic_visit(node)

    def _is_logger_factory_call(self, node: ast.Call) -> bool:
        """Check if this is a logger factory call like structlog.get_logger()."""
        try:
            if isinstance(node.func, ast.Attribute):
                # Check for patterns like structlog.get_logger(), logging.getLogger()
                if (
                    isinstance(node.func.value, ast.Name)
                    and node.func.value.id in self.logging_imports
                    and node.func.attr in self.logger_factory_patterns
                ):
                    return True
                # Check for direct factory calls like get_logger()
                if node.func.attr in self.logger_factory_patterns:
                    return True
            elif isinstance(node.func, ast.Name):
                # Check for direct calls like getLogger()
                if node.func.id in self.logger_factory_patterns:
                    return True
            return False
        except AttributeError:
            return False

    def _is_log_call(self, node: ast.Call) -> bool:
        """Check if this is a logging method call on a real logger."""
        try:
            if isinstance(node.func, ast.Attribute):
                # Check if method name is a log method
                if node.func.attr not in self.log_methods:
                    return False

                # Check if the object is a known logger
                if isinstance(node.func.value, ast.Name):
                    # Direct logger variable: logger.info()
                    if node.func.value.id in self.logger_variables:
                        return True
                    # Known logging module: logging.info() (rare but possible)
                    if node.func.value.id in self.logging_imports:
                        return True
                    # Common logger names (fallback for untracked loggers)
                    common_logger_names = {"log", "logger", "LOG", "LOGGER"}
                    if node.func.value.id in common_logger_names:
                        return True

                # Check for attribute access like self.logger.info()
                elif isinstance(node.func.value, ast.Attribute):
                    if isinstance(node.func.value.attr, str) and "logger" in node.func.value.attr.lower():
                        return True

                # Check for chained calls like structlog.get_logger().info()
                if isinstance(node.func.value, ast.Call):
                    if self._is_logger_factory_call(node.func.value):
                        return True

            return False
        except AttributeError:
            return False

    def _parse_log_statement(
        self,
        node: ast.Call,
        prefer_dash_case: bool = True,
    ) -> LogStatement:
        """Parse a log statement node into a LogStatement object."""
        method = node.func.attr if isinstance(node.func, ast.Attribute) else "unknown"
        line_number = node.lineno
        raw_call = ast.unparse(node)

        # Parse arguments
        args = []
        for arg in node.args:
            if isinstance(arg, ast.Constant):
                args.append(repr(arg.value))
            else:
                args.append(ast.unparse(arg))

        # Parse keyword arguments
        kwargs = {}
        magic_args = set()
        for keyword in node.keywords:
            if keyword.arg:
                if keyword.arg in self.magic_args:
                    magic_args.add(keyword.arg)
                kwargs[keyword.arg] = ast.unparse(keyword.value)

        # Determine event ID
        event_id = None
        has_event_id = False
        if args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
            event_id = node.args[0].value
            has_event_id = True

        # Check event ID format
        event_id_format = self._check_event_id_format(event_id) if event_id else "none"

        # Detect issues
        issues = self._detect_issues(
            method,
            args,
            kwargs,
            magic_args,
            event_id,
            event_id_format,
            prefer_dash_case,
        )

        return LogStatement(
            line_number=line_number,
            method=method,
            event_id=event_id,
            has_event_id=has_event_id,
            event_id_format=event_id_format,
            arguments=args,
            keyword_args=kwargs,
            magic_args=magic_args,
            raw_call=raw_call,
            issues=issues,
        )

    def _check_event_id_format(self, event_id: str) -> str:
        """Check the format of an event ID."""
        if not event_id:
            return "none"

        # dash-case: all lowercase with hyphens (allow numbers)
        if re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", event_id):
            return "dash-case"

        # snake_case: all lowercase with underscores
        if re.match(r"^[a-z]+(_[a-z]+)*$", event_id):
            return "snake_case"

        # camelCase: starts lowercase, then camelCase
        if re.match(r"^[a-z]+([A-Z][a-z]*)*$", event_id):
            return "camelCase"

        # PascalCase: starts uppercase
        if re.match(r"^[A-Z][a-z]*([A-Z][a-z]*)*$", event_id):
            return "PascalCase"

        return "invalid"

    def _detect_issues(
        self,
        method: str,
        args: list[str],
        kwargs: dict[str, str],
        magic_args: set[str],
        event_id: str | None,
        event_id_format: str,
        prefer_dash_case: bool = True,
    ) -> list[str]:
        """Detect common issues in log statements.

        This includes validation for overly long event IDs with too many elements.
        Event IDs with 5+ elements trigger a warning, 7+ elements trigger an error.
        """
        issues = []

        # Check for missing event ID
        if not event_id:
            issues.append("missing_event_id")

        # Check event ID format (configurable preference for dash-case)
        if event_id and event_id_format not in ["dash-case"]:
            # Only report if not allowing snake_case or if it's not snake_case
            if not (event_id_format == "snake_case" and not prefer_dash_case):
                suggested_event_id = self._convert_to_dash_case(event_id)
                issues.append(
                    f"event_id_not_dash_case (found: {event_id_format}, suggested: {suggested_event_id})",
                )

        # Check for too many elements in event ID (readability)
        if event_id:
            element_count = self._count_event_id_elements(event_id)
            if element_count >= 7:
                issues.append(f"event_id_too_many_elements ({element_count}>=7, wtf!)")
            elif element_count >= 5:
                issues.append(f"event_id_many_elements ({element_count}>=5, warning)")

        # Check for single string argument (anti-pattern)
        if len(args) == 1 and not kwargs and not magic_args:
            issues.append("single_string_argument")

        # Check for f-string in event ID (anti-pattern)
        if event_id and ("{" in event_id or "}" in event_id):
            issues.append("fstring_in_event_id")

        # Check for debug with _replace_msg (usually not needed)
        if method == "debug" and "_replace_msg" in magic_args:
            issues.append("debug_with_replace_msg")

        # Check for too many keyword arguments (complexity warning)
        non_magic_kwargs = {k: v for k, v in kwargs.items() if k not in self.magic_args}
        if len(non_magic_kwargs) > 7:
            issues.append(f"too_many_kwargs ({len(non_magic_kwargs)}>7)")

        # Check for proper structured data
        if event_id and not kwargs and "_replace_msg" not in magic_args:
            issues.append("no_structured_data")

        # Check for inconsistent log levels with event severity
        if (
            method == "debug"
            and event_id
            and any(word in event_id.lower() for word in ["error", "fail", "critical", "fatal"])
        ):
            issues.append("debug_for_error_event")

        if (
            method in ["error", "critical"]
            and event_id
            and any(word in event_id.lower() for word in ["debug", "trace", "info"])
        ):
            issues.append("error_level_for_info_event")

        # Check for password/secret leakage in kwargs
        sensitive_patterns = {
            "password",
            "passwd",
            "secret",
            "token",
            "auth_key",
            "auth_token",
            "api_key",
            "api_token",
            "credential",
            "private_key",
            "session_key",
        }
        for kwarg_key in kwargs:
            if kwarg_key.lower() in sensitive_patterns:
                issues.append(f"potential_secret_leak ({kwarg_key})")

        # Check for very long event IDs (readability)
        if event_id and len(event_id) > 50:
            issues.append(f"event_id_too_long ({len(event_id)}>50)")

        return issues

    def _count_event_id_elements(self, event_id: str) -> int:
        """Count the number of elements in an event ID.

        Elements are separated by dashes, underscores, or camelCase boundaries.

        Examples:
        - 'user-login' -> 2 elements
        - 'debug-logging-is-enabled-check-logs-above-for-http-details' -> 8 elements
        - 'userLoginSuccess' -> 3 elements
        - 'simple' -> 1 element

        """
        if not event_id:
            return 0

        # First, handle camelCase by inserting dashes before uppercase letters
        # but be careful with consecutive uppercase letters (like HTTP)
        import re

        # Insert dash before uppercase letters that follow lowercase/digits
        # This handles: userLogin -> user-Login, but keeps HTTP as one unit
        normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", event_id)

        # Handle consecutive uppercase letters followed by lowercase
        # This converts HTTPResponse -> HTTP-Response
        normalized = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1-\2", normalized)

        # Replace underscores with dashes for consistent splitting
        normalized = normalized.replace("_", "-")

        # Convert to lowercase and split by dashes
        normalized = normalized.lower()
        elements = [elem for elem in normalized.split("-") if elem.strip()]

        return len(elements)

    def _convert_to_dash_case(self, event_id: str) -> str:
        """Convert an event ID to dash-case format."""
        if not event_id:
            return event_id

        # Convert snake_case to dash-case
        if "_" in event_id:
            return event_id.replace("_", "-")

        # Convert camelCase/PascalCase to dash-case
        # Insert hyphens before uppercase letters and convert to lowercase
        import re

        result = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", event_id)
        return result.lower()


def analyze_file(file_path: Path, prefer_dash_case: bool = True) -> LogAnalysisResult:
    """Analyze log statements in a Python file."""
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content)

        analyzer = LogStatementAnalyzer(prefer_dash_case)
        analyzer.visit(tree)

        statements = analyzer.statements
        total = len(statements)
        with_event_id = sum(1 for s in statements if s.has_event_id)
        without_event_id = total - with_event_id
        dash_case_violations = sum(1 for s in statements if s.event_id and s.event_id_format != "dash-case")
        single_string_args = sum(1 for s in statements if "single_string_argument" in s.issues)

        # Count magic args usage
        magic_usage: dict[str, int] = {}
        for statement in statements:
            for magic_arg in statement.magic_args:
                magic_usage[magic_arg] = magic_usage.get(magic_arg, 0) + 1

        return LogAnalysisResult(
            file_path=file_path,
            statements=statements,
            total_statements=total,
            statements_with_event_id=with_event_id,
            statements_without_event_id=without_event_id,
            dash_case_violations=dash_case_violations,
            single_string_args=single_string_args,
            magic_args_usage=magic_usage,
        )

    except Exception:
        # Return empty result on error
        return LogAnalysisResult(
            file_path=file_path,
            statements=[],
            total_statements=0,
            statements_with_event_id=0,
            statements_without_event_id=0,
            dash_case_violations=0,
            single_string_args=0,
            magic_args_usage={},
        )


def print_analysis_summary(result: LogAnalysisResult, verbose: bool = False) -> None:
    """Print analysis summary for a file."""
    import structlog

    log = structlog.get_logger()

    if result.total_statements == 0:
        return

    log.info("analysis-summary-file", file=result.file_path.name, _replace_msg=f"📁 {result.file_path.name}")
    log.info(
        "analysis-summary-total",
        count=result.total_statements,
        _replace_msg=f"Total log statements: {result.total_statements}",
    )
    log.info(
        "analysis-summary-with-event",
        count=result.statements_with_event_id,
        _replace_msg=f"With event ID: {result.statements_with_event_id}",
    )
    log.info(
        "analysis-summary-without-event",
        count=result.statements_without_event_id,
        _replace_msg=f"Without event ID: {result.statements_without_event_id}",
    )

    if result.dash_case_violations > 0:
        log.info(
            "analysis-summary-dash-violations",
            count=result.dash_case_violations,
            _replace_msg=f"Dash-case violations: {result.dash_case_violations}",
        )

    if result.single_string_args > 0:
        log.info(
            "analysis-summary-single-string",
            count=result.single_string_args,
            _replace_msg=f"❌ Single string arguments: {result.single_string_args}",
        )

    if result.magic_args_usage:
        magic_str = ", ".join(f"{arg}:{count}" for arg, count in result.magic_args_usage.items())
        log.info("analysis-summary-magic-args", _replace_msg=f"🪄 Magic args: {magic_str}")

    if verbose:
        log.info("analysis-summary-statements", _replace_msg="Detailed statements:")
        for stmt in result.statements:
            args_str = ", ".join(stmt.arguments)
            status = f" ❌ {', '.join(stmt.issues)}" if stmt.issues else " ✅"
            magic = f" magic:{list(stmt.magic_args)}" if stmt.magic_args else ""
            log.info(
                "analysis-summary-statement",
                line=stmt.line_number,
                event_id=stmt.event_id,
                args=args_str,
                status=status,
                magic=magic,
                _replace_msg=f"L{stmt.line_number}: {stmt.method}({args_str}){status}{magic}",
            )


def main():
    """CLI entry point for log statement analysis."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze log statements in Python files",
    )
    parser.add_argument("path", help="File or directory to analyze")
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed statement breakdown",
    )
    parser.add_argument(
        "--allow-snake-case",
        action="store_true",
        help="Allow snake_case event IDs (default: prefer dash-case)",
    )

    args = parser.parse_args()

    path = Path(args.path)

    if path.is_file():
        if path.suffix == ".py":
            result = analyze_file(path, prefer_dash_case=not args.allow_snake_case)
            print_analysis_summary(result, args.verbose)
    else:
        EXCLUDE_DIRS = {
            ".venv",
            "venv",
            "__pycache__",
            ".git",
            ".tox",
            ".nox",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            ".direnv",
            "node_modules",
            "build",
            "dist",
            ".eggs",
        }
        python_files = [p for p in path.rglob("*.py") if not any(part in EXCLUDE_DIRS for part in p.parts)]
        total_files = 0
        total_statements = 0
        total_issues = 0

        for file_path in python_files:
            if "__pycache__" in str(file_path):
                continue

            result = analyze_file(file_path, prefer_dash_case=not args.allow_snake_case)
            if result.total_statements > 0:
                total_files += 1
                total_statements += result.total_statements
                file_issues = sum(len(s.issues) for s in result.statements)
                total_issues += file_issues

                print_analysis_summary(result, args.verbose)


if __name__ == "__main__":
    main()
