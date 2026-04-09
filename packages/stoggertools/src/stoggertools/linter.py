"""Logging Linter - Ensures proper logging coverage in your codebase.

Like a politeness compiler, but for log statements!
"""

import ast
import fnmatch
import json
import os
import tomllib
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import structlog
from rich.console import Console


@dataclass
class LintOptions:
    """Options for linting operations."""

    min_coverage: float = 5.0
    max_coverage: float = 15.0
    analyze_statements: bool = False
    verbose: bool = False
    allow_snake_case: bool = False
    project_structure: Any = None


from .log_statement_analyzer import (
    analyze_file as analyze_log_statements,
)

# Initialize logger
log = structlog.get_logger(__name__)

# Constants for logging wrapper detection
SINGLE_LOGGING_CALL = 1
MAX_BODY_STATEMENTS_FOR_PASSTHROUGH = 3


@dataclass
class LoggingStats:
    """Statistics about logging in a file."""

    total_lines: int
    code_lines: int  # Non-empty, non-comment lines
    log_statements: int
    functions: int
    functions_with_logging: int
    log_coverage_percent: float
    function_coverage_percent: float


@dataclass
class LoggingLevelIssue:
    """Represents a logging level issue or related logging suggestion."""

    line_no: int
    current_level: str
    suggested_level: str
    event_name: str
    reason: str
    severity: str = "warning"
    category: str = "level"  # "level", "except_logging", or "wrapper"


class LoggingVisitor(ast.NodeVisitor):
    """AST visitor to analyze logging patterns."""

    def __init__(self, source_lines: list[str] | None = None) -> None:
        self.log_statements = 0
        self.functions = 0
        self.functions_with_logging = 0
        self.current_function_has_logs = False
        self.source_lines = source_lines or []
        self.level_issues: list[LoggingLevelIssue] = []

        # Detect calls to common logging methods (suffix-based)
        self.log_patterns = {
            ".info(",
            ".debug(",
            ".warning(",
            ".error(",
            ".critical(",
            ".trace(",
            ".exception(",
            ".warn(",
        }

        # Track whether we're currently inside an except block and if that except has a name
        self._except_stack: list[str | None] = []

        # Track function definitions to detect log wrappers
        self._function_definitions: dict[str, ast.FunctionDef] = {}
        self._current_function: str | None = None

    def visit_FunctionDef(self, node) -> None:
        """Visit function definitions."""
        self.functions += 1
        old_has_logs = self.current_function_has_logs
        old_function = self._current_function
        self.current_function_has_logs = False
        self._current_function = node.name

        # Store function definition for wrapper analysis
        self._function_definitions[node.name] = node

        # Visit function body
        self.generic_visit(node)

        # Check if this function is a log wrapper
        self._analyze_log_wrapper(node)

        if self.current_function_has_logs:
            self.functions_with_logging += 1

        self.current_function_has_logs = old_has_logs
        self._current_function = old_function

    # Track try/except context to suggest log.exception usage
    def visit_Try(self, node: ast.Try) -> None:
        # Handle try/except blocks and push except names on stack
        for handler in node.handlers:
            name = handler.name if isinstance(handler.name, str) else None
            self._except_stack.append(name)
            # Visit the handler body to analyze logging calls inside
            for stmt in handler.body:
                self.visit(stmt)
            self._except_stack.pop()
        # Visit try, orelse, and finally parts normally
        for stmt in node.body:
            self.visit(stmt)
        for stmt in getattr(node, "orelse", []):
            self.visit(stmt)
        for stmt in getattr(node, "finalbody", []):
            self.visit(stmt)

    def visit_Call(self, node) -> None:
        """Visit function calls to detect logging."""
        call_str = ast.unparse(node)

        # Check if this looks like a logging call
        if any(pattern in call_str for pattern in self.log_patterns):
            # Count only per function, not every call inside it
            if not self.current_function_has_logs:
                self.log_statements += 1
            self.current_function_has_logs = True

            # Analyze logging level appropriateness
            self._analyze_logging_level(node)

            # If we're in an except: advise to use log.exception or exc_info
            self._analyze_except_logging(node)

        self.generic_visit(node)

    def _analyze_except_logging(self, node: ast.Call) -> None:
        """Within except blocks, suggest log.exception over log.error without exc_info."""
        # Only trigger if we are inside any except block
        if not self._except_stack:
            return
        # Only consider calls on a "log" object
        if not (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "log"
        ):
            return
        level = node.func.attr
        # If user used log.exception, it's fine — encourage dropping redundant error=str(e)
        if level == "exception":
            # Detect redundant explicit error=str(e)
            for kw in node.keywords:
                if kw.arg in {"error", "error_message"}:
                    issue = LoggingLevelIssue(
                        line_no=node.lineno,
                        current_level="exception",
                        suggested_level="exception",
                        event_name=self._extract_event_name(node) or "",
                        reason=(
                            "Inside except: log.exception() already includes"
                            " the exception and traceback; remove redundant error=str(e)"
                        ),
                        severity="warning",
                        category="except_logging",
                    )
                    self.level_issues.append(issue)
            return
        # For error/critical in except: require exc_info
        if level in {"error", "critical"}:
            has_exc_info = any(kw.arg == "exc_info" for kw in node.keywords)
            if not has_exc_info:
                issue = LoggingLevelIssue(
                    line_no=node.lineno,
                    current_level=level,
                    suggested_level="exception",
                    event_name=self._extract_event_name(node) or "",
                    reason="Inside except: prefer log.exception(...) or pass exc_info=True to include traceback",
                    severity="warning",
                    category="except_logging",
                )
                self.level_issues.append(issue)

    def _extract_event_name(self, node: ast.Call) -> str | None:
        try:
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                return str(node.args[0].value)
        except Exception as e:
            # Log the error and re-raise to avoid silent failures
            log.exception(
                "event-name-extraction-error",
                error=str(e),
                _replace_msg="Failed to extract event name: {error}",
            )
            raise
        return None

    def _analyze_logging_level(self, node: ast.Call) -> None:
        """Analyze if the logging level is appropriate."""
        # Extract logging level and event name
        level_info = self._extract_logging_info(node)
        if not level_info:
            return

        level, event_name = level_info

        # Check if this is a library internal operation that should be DEBUG
        if level == "info" and self._is_internal_operation(event_name):
            reason = self._get_level_change_reason(event_name)
            issue = LoggingLevelIssue(
                line_no=node.lineno,
                current_level="info",
                suggested_level="debug",
                event_name=event_name,
                reason=reason,
                severity="warning",
            )
            self.level_issues.append(issue)

    def _extract_logging_info(self, node: ast.Call) -> tuple[str, str] | None:
        """Extract logging level and event name from AST node."""
        try:
            # Check if this is log.LEVEL(event_name, ...)
            if (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "log"
            ):
                level = node.func.attr

                # Extract event name (first argument)
                if node.args and isinstance(node.args[0], ast.Constant):
                    event_name = str(node.args[0].value)
                    return level, event_name

        except Exception as e:
            # Log the error and re-raise to avoid silent failures
            log.exception(
                "logging-info-extraction-error",
                error=str(e),
                _replace_msg="Failed to extract logging info: {error}",
            )
            raise
        return None

    def _is_internal_operation(self, event_name: str) -> bool:
        """Determine if an event represents an internal library operation."""
        if not isinstance(event_name, str):
            return False

        # Patterns that indicate internal library operations
        internal_patterns = [
            "initializing-",
            "initialization-",
            "-init",
            "configuring-",
            "configured-",
            "configuration-",
            "enabling-",
            "enabled-",
            "building-",
            "built-",
            "creating-",
            "created-",
            "starting-",
            "started-",
            "loading-",
            "loaded-",
            "processing-",
            "processed-",
            "-complete",
            "-finished",
            "-done",
            "setup-",
            "stdlib-logging-",
            "sync-logging-",
            "async-logging-",
            "console-logging-",
            "file-logging-",
            "renderer-created",
        ]

        # Specific internal events
        internal_events = {
            "logging-initialization-complete",
            "stdlib-logging-configuration-complete",
            "sync-logging-configured",
            "async-logging-configured",
            "console-logging-enabled",
            "file-logging-enabled",
            "no-pyproject-found",
        }

        event_lower = event_name.lower()

        # Check patterns
        for pattern in internal_patterns:
            if pattern in event_lower:
                return True

        # Check specific events
        return event_name in internal_events

    def _get_level_change_reason(self, event_name: str) -> str:
        """Get human-readable reason for level change suggestion."""
        event_lower = event_name.lower()

        if "initializ" in event_lower:
            return "Library initialization should be debug level to avoid user spam"
        if "configur" in event_lower:
            return "Internal configuration should be debug level"
        if "enabling" in event_lower or "building" in event_lower:
            return "Internal setup operations should be debug level"
        if "complete" in event_lower or "finished" in event_lower:
            return "Completion messages for internal operations should be debug level"
        if "renderer" in event_lower:
            return "Renderer creation is internal library setup"
        return "Internal library operation should be debug level to avoid spamming users"

    def _analyze_log_wrapper(self, node: ast.FunctionDef) -> None:
        """Analyze if a function is a problematic log wrapper."""
        # Skip functions with obvious non-wrapper names
        non_wrapper_names = {
            "__init__",
            "__str__",
            "__repr__",
            "main",
            "run",
            "execute",
            "process",
            "handle",
            "setup",
            "teardown",
            "test_",
        }
        if any(pattern in node.name.lower() for pattern in non_wrapper_names):
            return

        # Look for wrapper patterns in function body
        has_logging_call = False
        has_other_logic = False
        logging_calls = []

        # Only analyze direct statements in the function body, not nested calls
        for stmt in node.body:
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                call = stmt.value
                call_str = ast.unparse(call)

                # Check if this is a logging call
                if any(pattern in call_str for pattern in self.log_patterns):
                    has_logging_call = True
                    logging_calls.append(call)
                elif not self._is_trivial_call(call):
                    has_other_logic = True
            elif isinstance(stmt, ast.If):
                # Check if the if statement contains logging
                for child_stmt in ast.walk(stmt):
                    if isinstance(child_stmt, ast.Call):
                        call_str = ast.unparse(child_stmt)
                        if any(pattern in call_str for pattern in self.log_patterns):
                            has_logging_call = True
                            logging_calls.append(child_stmt)
                        elif not self._is_trivial_call(child_stmt):
                            has_other_logic = True
            elif not isinstance(stmt, ast.Pass | ast.Return):
                # Any other significant statement indicates business logic
                has_other_logic = True

        # Detect wrapper anti-patterns
        if has_logging_call and not has_other_logic and self._is_likely_wrapper(node, logging_calls):
            self._report_wrapper_issue(node, logging_calls)

    def _is_trivial_call(self, call: ast.Call) -> bool:
        """Check if a call is trivial (not significant business logic)."""
        call_str = ast.unparse(call)
        trivial_patterns = [
            "str(",
            "len(",
            "type(",
            "isinstance(",
            "hasattr(",
            "getattr(",
            "setattr(",
            "format(",
            ".strip(",
            ".lower(",
            ".upper(",
            ".split(",
            ".join(",
            ".replace(",
        ]
        return any(pattern in call_str for pattern in trivial_patterns)

    def _is_likely_wrapper(
        self,
        func_node: ast.FunctionDef,
        logging_calls: list[ast.Call],
    ) -> bool:
        """Determine if function is likely an unnecessary log wrapper."""
        # Constants for wrapper detection
        NO_ARGS = 0
        SINGLE_BODY_STATEMENT = 1
        SINGLE_LOGGING_CALL = 1
        MAX_BODY_STATEMENTS_FOR_PASSTHROUGH = 2

        # First check: Don't flag very simple functions with no parameters (like log_startup())
        # These are often legitimate convenience functions
        func_args = {arg.arg for arg in func_node.args.args}
        if (
            len(func_args) == NO_ARGS
            and len(func_node.body) == SINGLE_BODY_STATEMENT
            and len(logging_calls) == SINGLE_LOGGING_CALL
        ):
            return False

        # Pattern 1: Function name suggests it's a wrapper
        wrapper_name_patterns = [
            "log_",
            "_log",
            "write_log",
            "do_log",
            "make_log",
            "send_log",
            "emit_log",
            "output_log",
            "print_log",
        ]
        if any(pattern in func_node.name.lower() for pattern in wrapper_name_patterns):
            return True

        # Pattern 2: Function that conditionally logs (common anti-pattern)
        has_conditional_logging = False
        for stmt in func_node.body:
            if isinstance(stmt, ast.If):
                # Check if the if statement contains logging
                for child in ast.walk(stmt):
                    if isinstance(child, ast.Call):
                        call_str = ast.unparse(child)
                        if any(pattern in call_str for pattern in self.log_patterns):
                            has_conditional_logging = True
                            break

        if has_conditional_logging:
            return True

        # Pattern 3: Simple passthrough function (just calls log with parameters)
        if len(logging_calls) == SINGLE_LOGGING_CALL and len(func_node.body) <= MAX_BODY_STATEMENTS_FOR_PASSTHROUGH:
            # Check if function parameters are just passed through to logging
            log_call = logging_calls[0]

            # Simple heuristic: if function has args and they appear in the log call
            if func_args and len(func_args) > 0:
                log_call_str = ast.unparse(log_call)
                if any(arg in log_call_str for arg in func_args):
                    return True

        return False

    def _report_wrapper_issue(
        self,
        func_node: ast.FunctionDef,
        logging_calls: list[ast.Call],
    ) -> None:
        """Report a log wrapper anti-pattern issue."""
        # Determine the specific wrapper pattern
        reason = "Function appears to be an unnecessary wrapper around logging calls"

        if "log_" in func_node.name.lower() or "_log" in func_node.name.lower():
            reason = (
                f"Function '{func_node.name}' appears to be a wrapper around logging - consider using log.* directly"
            )
        elif len(logging_calls) == SINGLE_LOGGING_CALL and len(func_node.body) <= MAX_BODY_STATEMENTS_FOR_PASSTHROUGH:
            reason = f"Function '{func_node.name}' only passes parameters to logging - use log.* directly instead"
        elif any(isinstance(stmt, ast.If) for stmt in ast.walk(func_node)):
            reason = (
                f"Function '{func_node.name}' conditionally logs"
                " - consider using log levels or structured logging instead"
            )

        issue = LoggingLevelIssue(
            line_no=func_node.lineno,
            current_level="wrapper",
            suggested_level="direct",
            event_name=func_node.name,
            reason=reason,
            severity="warning",
            category="wrapper",
        )
        self.level_issues.append(issue)


def analyze_file(file_path: Path) -> tuple[LoggingStats, list[LoggingLevelIssue]]:
    """Analyze a Python file for logging coverage."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        # Log the error and re-raise to avoid silent failures
        log.exception(
            "file-read-error",
            file_path=str(file_path),
            error=str(e),
            _replace_msg="Failed to read file {file_path}: {error}",
        )
        raise

    lines = content.splitlines()
    total_lines = len(lines)

    # Count non-empty, non-comment lines
    code_lines = 0
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            code_lines += 1

    # Parse AST and analyze
    try:
        tree = ast.parse(content)
        visitor = LoggingVisitor(lines)
        visitor.visit(tree)

        log_coverage = (visitor.log_statements / code_lines * 100) if code_lines > 0 else 0
        func_coverage = (visitor.functions_with_logging / visitor.functions * 100) if visitor.functions > 0 else 0

        stats = LoggingStats(
            total_lines=total_lines,
            code_lines=code_lines,
            log_statements=visitor.log_statements,
            functions=visitor.functions,
            functions_with_logging=visitor.functions_with_logging,
            log_coverage_percent=log_coverage,
            function_coverage_percent=func_coverage,
        )

    except SyntaxError:
        return LoggingStats(0, 0, 0, 0, 0, 0.0, 0.0), []
    else:
        return stats, visitor.level_issues


def check_logging_quality(
    stats: LoggingStats,
    min_coverage: float = 5.0,
    max_coverage: float = 15.0,
) -> list[str]:
    """Check if logging coverage is appropriate."""
    issues: list[str] = []

    if stats.code_lines == 0:
        return issues

    # Check overall logging coverage
    if stats.log_coverage_percent < min_coverage:
        issues.extend(
            (
                f"❌ Too little logging! {stats.log_coverage_percent:.1f}% coverage (minimum: {min_coverage}%)",
                "   Add more log.info(), log.debug(), or log.error() statements",
            )
        )
    elif stats.log_coverage_percent > max_coverage:
        issues.extend(
            (
                f"⚠️  Possibly too much logging! {stats.log_coverage_percent:.1f}% coverage (maximum: {max_coverage}%)",
                "   Consider reducing log verbosity or using higher log levels",
            )
        )
    else:
        issues.append(f"✅ Good logging coverage: {stats.log_coverage_percent:.1f}%")

    # Constants for coverage thresholds
    MIN_FUNCTION_LOGGING_PERCENT = 30
    MAX_FUNCTION_LOGGING_PERCENT = 90

    # Check function coverage
    if stats.functions > 0:
        if stats.function_coverage_percent < MIN_FUNCTION_LOGGING_PERCENT:
            issues.extend(
                (
                    f"❌ Too few functions have logging: {stats.function_coverage_percent:.1f}%",
                    f"   Consider adding logging to more functions (aim for {MIN_FUNCTION_LOGGING_PERCENT}-70%)",
                )
            )
        elif stats.function_coverage_percent > MAX_FUNCTION_LOGGING_PERCENT:
            issues.append(
                f"⚠️  Almost every function logs - might be excessive: {stats.function_coverage_percent:.1f}%",
            )
        else:
            issues.append(
                f"✅ Good function logging coverage: {stats.function_coverage_percent:.1f}%",
            )

    return issues


def lint_directory(directory: Path, options_or_min_coverage=None, **kwargs) -> bool:
    """Lint all Python files in a directory and its subdirectories.

    Uses smart project structure detection to exclude tests from logging analysis.
    """
    console = Console()

    # Handle backward compatibility
    if isinstance(options_or_min_coverage, LintOptions):
        options = options_or_min_coverage
    else:
        # Old signature: lint_directory(directory, min_coverage=5.0, max_coverage=15.0, ...)
        min_coverage = options_or_min_coverage or 5.0
        max_coverage = kwargs.get("max_coverage", 15.0)
        options = LintOptions(
            min_coverage=min_coverage,
            max_coverage=max_coverage,
            project_structure=kwargs.get("project_structure"),
        )

    # Use project structure detection if provided, otherwise fall back to legacy method
    if options.project_structure:
        # Smart filtering: only analyze source files for logging coverage
        python_files = []
        for source_dir in options.project_structure.source_dirs:
            source_path = directory / source_dir
            if source_path.exists():
                python_files.extend(
                    py_file
                    for py_file in source_path.rglob("*.py")
                    if not options.project_structure.should_exclude_from_logging_analysis(py_file)
                )

        if options.verbose:
            [
                py_file
                for py_file in directory.rglob("*.py")
                if options.project_structure.should_exclude_from_logging_analysis(py_file)
            ]
    else:
        # Load exclusion globs from pyproject.toml [tool.stogger]
        exclude_globs: list[str] = []
        pyproject = directory / "pyproject.toml"
        if pyproject.exists():
            exclude_globs = []
            with suppress(Exception):
                with pyproject.open("rb") as f:
                    cfg = tomllib.load(f)
                nl_cfg = cfg.get("tool", {}).get("stogger", {})
                exclude_globs = list(nl_cfg.get("exclude", []))

        def is_excluded(path: Path) -> bool:
            rel = path.relative_to(directory)
            s = str(rel)
            # Match any configured glob
            for pattern in exclude_globs:
                if fnmatch.fnmatch(s, pattern):
                    return True
                # Also allow directory-style pattern without **/*.py
                if rel.parts and pattern.rstrip("/") in rel.parts:
                    return True
            return False

        python_files = [p for p in directory.rglob("*.py") if not is_excluded(p)]

    if not python_files:
        if os.getenv("NICESTLOG_LINTER_FORMAT", "table").lower() in {"json", "toml"}:
            # Emit empty machine-readable report
            fmt = os.getenv("NICESTLOG_LINTER_FORMAT", "table").lower()
            if fmt == "json":
                pass
        return True

    total_issues = 0
    total_stats = LoggingStats(0, 0, 0, 0, 0, 0.0, 0.0)

    # Allow machine-readable output via environment variable
    output_format = os.getenv("NICESTLOG_LINTER_FORMAT", "table").lower()

    if output_format not in {"json", "toml"}:
        pass

    # Collect per-file data first so we can render a clean table
    rows: list[dict[str, Any]] = []
    all_level_issues = []  # Store all level issues for detailed display

    for file_path in python_files:
        # Skip hidden files (dirs already excluded above)
        if file_path.name.startswith("."):
            continue

        stats, level_issues = analyze_file(file_path)
        issues = check_logging_quality(stats, options.min_coverage, options.max_coverage)

        # Accumulate totals
        total_stats.total_lines += stats.total_lines
        total_stats.code_lines += stats.code_lines
        total_stats.log_statements += stats.log_statements
        total_stats.functions += stats.functions
        total_stats.functions_with_logging += stats.functions_with_logging

        # Analyze log statements if requested
        log_analysis = None
        if options.analyze_statements:
            log_analysis = analyze_log_statements(
                file_path,
                prefer_dash_case=not options.allow_snake_case,
            )

        # Determine primary issue label (text only, no emojis)
        primary_issue_text = ""
        if issues:
            for i in issues:
                if "Too little logging" in i:
                    primary_issue_text = "Too little logging"
                    break
                if "Possibly too much logging" in i:
                    primary_issue_text = "Possibly too much logging"
                    break
                if "Good logging coverage" in i:
                    primary_issue_text = "Good logging coverage"
                    break

        # Count issues
        error_count = sum(1 for issue in issues if "❌" in issue)
        warning_count = sum(1 for issue in issues if "⚠️" in issue)

        # Add level issues to warning count
        warning_count += len(level_issues)

        # Store level issues for detailed display
        all_level_issues.extend((file_path.relative_to(directory), issue) for issue in level_issues)

        # Add log statement issues
        statement_issues = 0
        total_statements = 0
        if log_analysis and log_analysis.total_statements > 0:
            total_statements = log_analysis.total_statements
            statement_issues = sum(len(s.issues) for s in log_analysis.statements)
            if statement_issues > 0:
                error_count += 1  # reflect statement problems as errors

        if error_count > 0 or warning_count > 0:
            total_issues += 1

        rows.append(
            {
                "module": str(file_path.relative_to(directory)),
                "lines": stats.code_lines,
                "logs": stats.log_statements,
                "coverage": stats.log_coverage_percent,
                "errors": error_count,
                "warnings": warning_count,
                "primary": primary_issue_text,
                "statements": total_statements,
                "statement_issues": statement_issues,
            },
        )

    # Overall summary (compute percentages)
    if total_stats.code_lines > 0:
        total_stats.log_coverage_percent = total_stats.log_statements / total_stats.code_lines * 100
        total_stats.function_coverage_percent = (
            (total_stats.functions_with_logging / total_stats.functions * 100) if total_stats.functions > 0 else 0
        )

    if output_format == "json":
        # Machine-readable JSON output
        {
            "files": rows,
            "summary": {
                "total_files": len(python_files),
                "files_with_issues": total_issues,
                "total_code_lines": total_stats.code_lines,
                "total_log_statements": total_stats.log_statements,
                "overall_logging_coverage": round(total_stats.log_coverage_percent, 1),
                "functions": total_stats.functions,
                "functions_with_logging": total_stats.functions_with_logging,
                "function_logging_coverage": round(
                    total_stats.function_coverage_percent,
                    1,
                ),
            },
        }
    elif output_format == "toml":
        # Machine-readable TOML output

        {
            "files": rows,
            "summary": {
                "total_files": len(python_files),
                "files_with_issues": total_issues,
                "total_code_lines": total_stats.code_lines,
                "total_log_statements": total_stats.log_statements,
                "overall_logging_coverage": round(total_stats.log_coverage_percent, 1),
                "functions": total_stats.functions,
                "functions_with_logging": total_stats.functions_with_logging,
                "function_logging_coverage": round(
                    total_stats.function_coverage_percent,
                    1,
                ),
            },
        }
    else:
        # Check if AST metrics are available for unified display
        ast_metrics = {}
        try:
            ast_data = os.getenv("NICESTLOG_AST_METRICS")
            if ast_data:
                ast_metrics = json.loads(ast_data)
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            # Log the error and continue with empty metrics
            log.warning(
                "ast-metrics-parse-error",
                error=str(e),
                _replace_msg="Failed to parse AST metrics: {error}, continuing without AST metrics",
            )

        # Human-friendly table output with subtle colors

        # Add AST metrics to rows if available
        for r in rows:
            if r["module"] in ast_metrics:
                r["functions"] = ast_metrics[r["module"]]["functions"]
                r["classes"] = ast_metrics[r["module"]]["classes"]
            else:
                r["functions"] = 0
                r["classes"] = 0

        # Determine dynamic column widths
        module_width = max([len("MODULE")] + [len(r["module"]) for r in rows])
        lines_width = max(len("LINES"), *(len(str(r["lines"])) for r in rows))
        funcs_width = max(
            len("FUNCS"),
            *(len(str(r.get("functions", 0))) for r in rows),
        )
        classes_width = max(
            len("CLASSES"),
            *(len(str(r.get("classes", 0))) for r in rows),
        )
        logs_width = max(len("LOGS"), *(len(str(r["logs"])) for r in rows))
        cov_width = max(len("COVERAGE"), *(len(f"{r['coverage']:.1f}%") for r in rows))
        # Compute width for ISSUES based on visible content (E#/W#), ignoring ANSI codes
        issues_plain_list = []
        for r in rows:
            parts = []
            if r["errors"]:
                parts.append(f"E{r['errors']}")
            if r["warnings"]:
                parts.append(f"W{r['warnings']}")
            issues_plain_list.append(" ".join(parts))
        issues_width = max(len("ISSUES"), *(len(s) for s in issues_plain_list))
        primary_width = max(len("SUMMARY"), *(len(r["primary"]) for r in rows))

        h_module = "MODULE"
        h_lines = "LINES"
        h_funcs = "FUNCS"
        h_classes = "CLASSES"
        h_logs = "LOGS"
        h_cov = "COVERAGE"
        h_issues = "ISSUES"
        h_summary = "SUMMARY"

        # Build header with or without AST columns
        if ast_metrics:
            header = (
                f"{h_module.ljust(module_width)}  "
                f"{h_lines.rjust(lines_width)}  "
                f"{h_funcs.rjust(funcs_width)}  "
                f"{h_classes.rjust(classes_width)}  "
                f"{h_logs.rjust(logs_width)}  "
                f"{h_cov.rjust(cov_width)}  "
                f"{h_issues.rjust(issues_width)}  "
                f"{h_summary.ljust(primary_width)}"
            )
        else:
            header = (
                f"{h_module.ljust(module_width + (len(h_module) - len('MODULE')))}  "
                f"{h_lines.rjust(lines_width + (len(h_lines) - len('LINES')))}  "
                f"{h_logs.rjust(logs_width + (len(h_logs) - len('LOGS')))}  "
                f"{h_cov.rjust(cov_width + (len(h_cov) - len('COVERAGE')))}  "
                f"{h_issues.rjust(issues_width + (len(h_issues) - len('ISSUES')))}  "
                f"{h_summary.ljust(primary_width + (len(h_summary) - len('SUMMARY')))}"
            )
        console.print(header)
        # Calculate separator width based on whether AST metrics are included
        if ast_metrics:
            sep_width = (
                module_width
                + lines_width
                + funcs_width
                + classes_width
                + logs_width
                + cov_width
                + issues_width
                + primary_width
                + 14
            )
        else:
            sep_width = module_width + lines_width + logs_width + cov_width + issues_width + primary_width + 10
        console.print("-" * sep_width)

        for r in rows:
            issues_txt = []
            if r["errors"]:
                issues_txt.append(f"E{r['errors']}")
            if r["warnings"]:
                issues_txt.append(f"W{r['warnings']}")
            issues_cell = " ".join(issues_txt)
            coverage_txt = f"{r['coverage']:.1f}%"

            issues_cell_padded = issues_cell.ljust(issues_width)

            # Build and print row with or without AST columns
            coverage_padded = coverage_txt.rjust(cov_width)

            issues_padded = issues_cell_padded

            if ast_metrics:
                row = (
                    f"{r['module'].ljust(module_width)}  "
                    f"{str(r['lines']).rjust(lines_width)}  "
                    f"{str(r.get('functions', 0)).rjust(funcs_width)}  "
                    f"{str(r.get('classes', 0)).rjust(classes_width)}  "
                    f"{str(r['logs']).rjust(logs_width)}  "
                    f"{coverage_padded}  "
                    f"{issues_padded}  "
                    f"{r['primary'].ljust(primary_width)}"
                )
            else:
                row = (
                    f"{r['module'].ljust(module_width)}  "
                    f"{str(r['lines']).rjust(lines_width)}  "
                    f"{str(r['logs']).rjust(logs_width)}  "
                    f"{coverage_padded}  "
                    f"{issues_padded}  "
                    f"{r['primary'].ljust(primary_width)}"
                )
            console.print(row)

        # Global issue legend: what E#/W# counts refer to and categories
        console.print("\nISSUE LEGEND")
        console.print("E# = Errors (critical issues requiring attention)")
        console.print("W# = Warnings (suggestions for improvement)")

        # Display detailed level issues if any found
        level_issues = [issue for file_path, issue in all_level_issues if issue.category != "wrapper"]
        wrapper_issues = [issue for file_path, issue in all_level_issues if issue.category == "wrapper"]

        if level_issues:
            console.print("🔧 LOGGING LEVEL ISSUES DETECTED")

            for file_path, issue in all_level_issues:
                if issue.category != "wrapper":
                    console.print(f"  {file_path}:{issue.line_no} - {issue.reason}")

        # Display wrapper issues if any found
        if wrapper_issues:
            console.print("🚫 LOG WRAPPER ANTI-PATTERNS DETECTED")

            for file_path, issue in all_level_issues:
                if issue.category == "wrapper":
                    console.print(
                        reason=issue.reason,
                        _replace_msg=f"  {file_path}:{issue.line_no} - {issue.reason}",
                    )

    if output_format not in {"json", "toml"}:
        pass

    if total_issues == 0:
        if output_format not in {"json", "toml"}:
            log.info(
                "linter-no-issues",
                files=len(python_files),
                _replace_msg=f"✅ {len(python_files)} files checked - no issues found!",
            )
        return True
    if output_format not in {"json", "toml"}:
        log.info(
            "linter-issues-found",
            total_issues=total_issues,
            _replace_msg=f"❌ {total_issues} files have logging issues",
        )
    return False
