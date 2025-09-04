"""
AST-based log statement analyzer for nicestlog.

Analyzes log statements to detect common issues and patterns.
"""

import ast
import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Set
from pathlib import Path


@dataclass
class LogStatement:
    """Represents a parsed log statement."""

    line_number: int
    method: str  # info, debug, warning, error, etc.
    event_id: Optional[str]
    has_event_id: bool
    event_id_format: str  # "dash-case", "snake_case", "camelCase", "invalid"
    arguments: List[str]
    keyword_args: Dict[str, str]
    magic_args: Set[str]  # _replace_msg, exc_info, etc.
    raw_call: str
    issues: List[str]


@dataclass
class LogAnalysisResult:
    """Results of analyzing log statements in a file."""

    file_path: Path
    statements: List[LogStatement]
    total_statements: int
    statements_with_event_id: int
    statements_without_event_id: int
    dash_case_violations: int
    single_string_args: int
    magic_args_usage: Dict[str, int]


class LogStatementAnalyzer(ast.NodeVisitor):
    """AST visitor that analyzes log statements."""

    def __init__(self, prefer_dash_case: bool = True):
        self.statements: List[LogStatement] = []
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
        self.logging_imports: Set[str] = (
            set()
        )  # e.g., {'logging', 'structlog', 'loguru'}
        self.logger_variables: Set[str] = set()  # e.g., {'log', 'logger', 'my_logger'}
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
            node.value
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
                    if (
                        isinstance(node.func.value.attr, str)
                        and "logger" in node.func.value.attr.lower()
                    ):
                        return True

                # Check for chained calls like structlog.get_logger().info()
                if isinstance(node.func.value, ast.Call):
                    if self._is_logger_factory_call(node.func.value):
                        return True

            return False
        except AttributeError:
            return False

    def _parse_log_statement(
        self, node: ast.Call, prefer_dash_case: bool = True
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
        if (
            args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
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
        args: List[str],
        kwargs: Dict[str, str],
        magic_args: Set[str],
        event_id: Optional[str],
        event_id_format: str,
        prefer_dash_case: bool = True,
    ) -> List[str]:
        """Detect common issues in log statements."""
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
                    f"event_id_not_dash_case (found: {event_id_format}, suggested: {suggested_event_id})"
                )

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
            and any(
                word in event_id.lower()
                for word in ["error", "fail", "critical", "fatal"]
            )
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
        for kwarg_key in kwargs.keys():
            if kwarg_key.lower() in sensitive_patterns:
                issues.append(f"potential_secret_leak ({kwarg_key})")

        # Check for very long event IDs (readability)
        if event_id and len(event_id) > 50:
            issues.append(f"event_id_too_long ({len(event_id)}>50)")

        return issues

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
        dash_case_violations = sum(
            1 for s in statements if s.event_id and s.event_id_format != "dash-case"
        )
        single_string_args = sum(
            1 for s in statements if "single_string_argument" in s.issues
        )

        # Count magic args usage
        magic_usage: Dict[str, int] = {}
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
    if result.total_statements == 0:
        return

    print(f"📁 {result.file_path.name}")
    print(f"   Total log statements: {result.total_statements}")
    print(f"   With event ID: {result.statements_with_event_id}")
    print(f"   Without event ID: {result.statements_without_event_id}")

    if result.dash_case_violations > 0:
        print(f"   ❌ Dash-case violations: {result.dash_case_violations}")

    if result.single_string_args > 0:
        print(f"   ❌ Single string arguments: {result.single_string_args}")

    if result.magic_args_usage:
        magic_summary = ", ".join(
            f"{k}:{v}" for k, v in result.magic_args_usage.items()
        )
        print(f"   🪄 Magic args: {magic_summary}")

    if verbose:
        print("   Detailed statements:")
        for stmt in result.statements:
            issues_str = f" ❌ {', '.join(stmt.issues)}" if stmt.issues else " ✅"
            event_str = f"'{stmt.event_id}'" if stmt.event_id else "NO_EVENT"
            magic_str = f" magic:{list(stmt.magic_args)}" if stmt.magic_args else ""
            print(
                f"     L{stmt.line_number}: {stmt.method}({event_str}){magic_str}{issues_str}"
            )

    print()


def main():
    """CLI entry point for log statement analysis."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze log statements in Python files"
    )
    parser.add_argument("path", help="File or directory to analyze")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed statement breakdown"
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
        python_files = [
            p
            for p in path.rglob("*.py")
            if not any(part in EXCLUDE_DIRS for part in p.parts)
        ]
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

        print(
            f"📊 Summary: {total_files} files, {total_statements} log statements, {total_issues} issues"
        )


if __name__ == "__main__":
    main()
