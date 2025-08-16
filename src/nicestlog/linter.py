"""
Logging Linter - Ensures proper logging coverage in your codebase.

Like a politeness compiler, but for log statements!
"""

import ast
import argparse
import sys
import os
import json
import toml
from pathlib import Path
from typing import List
from dataclasses import dataclass
from colorama import init as colorama_init, Fore, Style

from .log_statement_analyzer import analyze_file as analyze_log_statements, LogAnalysisResult


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


class LoggingVisitor(ast.NodeVisitor):
    """AST visitor to analyze logging patterns."""

    def __init__(self):
        self.log_statements = 0
        self.functions = 0
        self.functions_with_logging = 0
        self.current_function_has_logs = False

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

    def visit_FunctionDef(self, node):
        """Visit function definitions."""
        self.functions += 1
        old_has_logs = self.current_function_has_logs
        self.current_function_has_logs = False

        # Visit function body
        self.generic_visit(node)

        if self.current_function_has_logs:
            self.functions_with_logging += 1

        self.current_function_has_logs = old_has_logs

    def visit_Call(self, node):
        """Visit function calls to detect logging."""
        call_str = ast.unparse(node)

        # Check if this looks like a logging call
        if any(pattern in call_str for pattern in self.log_patterns):
            # Count only per function, not every call inside it
            if not self.current_function_has_logs:
                self.log_statements += 1
            self.current_function_has_logs = True

        self.generic_visit(node)


def analyze_file(file_path: Path) -> LoggingStats:
    """Analyze a Python file for logging coverage."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return LoggingStats(0, 0, 0, 0, 0, 0.0, 0.0)

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
        visitor = LoggingVisitor()
        visitor.visit(tree)

        log_coverage = (
            (visitor.log_statements / code_lines * 100) if code_lines > 0 else 0
        )
        func_coverage = (
            (visitor.functions_with_logging / visitor.functions * 100)
            if visitor.functions > 0
            else 0
        )

        return LoggingStats(
            total_lines=total_lines,
            code_lines=code_lines,
            log_statements=visitor.log_statements,
            functions=visitor.functions,
            functions_with_logging=visitor.functions_with_logging,
            log_coverage_percent=log_coverage,
            function_coverage_percent=func_coverage,
        )
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}", file=sys.stderr)
        return LoggingStats(0, 0, 0, 0, 0, 0.0, 0.0)


def check_logging_quality(
    stats: LoggingStats, min_coverage: float = 5.0, max_coverage: float = 15.0
) -> List[str]:
    """Check if logging coverage is appropriate."""
    issues = []

    if stats.code_lines == 0:
        return issues

    # Check overall logging coverage
    if stats.log_coverage_percent < min_coverage:
        issues.append(
            f"❌ Too little logging! {stats.log_coverage_percent:.1f}% coverage (minimum: {min_coverage}%)"
        )
        issues.append("   Add more log.info(), log.debug(), or log.error() statements")
    elif stats.log_coverage_percent > max_coverage:
        issues.append(
            f"⚠️  Possibly too much logging! {stats.log_coverage_percent:.1f}% coverage (maximum: {max_coverage}%)"
        )
        issues.append("   Consider reducing log verbosity or using higher log levels")
    else:
        issues.append(f"✅ Good logging coverage: {stats.log_coverage_percent:.1f}%")

    # Check function coverage
    if stats.functions > 0:
        if stats.function_coverage_percent < 30:
            issues.append(
                f"❌ Too few functions have logging: {stats.function_coverage_percent:.1f}%"
            )
            issues.append(
                "   Consider adding logging to more functions (aim for 30-70%)"
            )
        elif stats.function_coverage_percent > 90:
            issues.append(
                f"⚠️  Almost every function logs - might be excessive: {stats.function_coverage_percent:.1f}%"
            )
        else:
            issues.append(
                f"✅ Good function logging coverage: {stats.function_coverage_percent:.1f}%"
            )

    return issues


def lint_directory(
    directory: Path, min_coverage: float = 5.0, max_coverage: float = 15.0,
    analyze_statements: bool = False, verbose: bool = False, allow_snake_case: bool = False
) -> bool:
    """Lint all Python files in a directory and its subdirectories.

    Excludes common virtual env, cache and VCS directories (e.g., .venv, venv, __pycache__, .git).
    """
    # Recursively find all Python files in the directory, excluding unwanted dirs
    EXCLUDE_DIRS = {
        ".venv", "venv", "__pycache__", ".git", ".tox", ".nox",
        ".mypy_cache", ".pytest_cache", ".ruff_cache", ".direnv",
        "node_modules", "build", "dist", ".eggs"
    }
    python_files = [
        p for p in directory.rglob("*.py")
        if not any(part in EXCLUDE_DIRS for part in p.parts)
    ]

    if not python_files:
        if os.getenv("NICESTLOG_LINTER_FORMAT", "table").lower() in {"json", "toml"}:
            # Emit empty machine-readable report
            report = {
                "files": [],
                "summary": {
                    "total_files": 0,
                    "files_with_issues": 0,
                    "total_code_lines": 0,
                    "total_log_statements": 0,
                    "overall_logging_coverage": 0.0,
                    "functions": 0,
                    "functions_with_logging": 0,
                    "function_logging_coverage": 0.0,
                },
            }
            fmt = os.getenv("NICESTLOG_LINTER_FORMAT", "table").lower()
            if fmt == "json":
                print(json.dumps(report, ensure_ascii=False))
            else:
                print(toml.dumps(report))
        else:
            print("No Python files found in the specified directory!")
        return True

    total_issues = 0
    total_stats = LoggingStats(0, 0, 0, 0, 0, 0.0, 0.0)

    # Allow machine-readable output via environment variable
    output_format = os.getenv("NICESTLOG_LINTER_FORMAT", "table").lower()

    if output_format not in {"json", "toml"}:
        print(f"🔍 Analyzing {len(python_files)} Python files in {directory} for logging quality...\n")

    # Collect per-file data first so we can render a clean table
    rows: List[dict] = []

    for file_path in python_files:
        # Skip hidden files (dirs already excluded above)
        if file_path.name.startswith("."):
            continue

        stats = analyze_file(file_path)
        issues = check_logging_quality(stats, min_coverage, max_coverage)

        # Accumulate totals
        total_stats.total_lines += stats.total_lines
        total_stats.code_lines += stats.code_lines
        total_stats.log_statements += stats.log_statements
        total_stats.functions += stats.functions
        total_stats.functions_with_logging += stats.functions_with_logging

        # Analyze log statements if requested
        log_analysis = None
        if analyze_statements:
            log_analysis = analyze_log_statements(file_path, prefer_dash_case=not allow_snake_case)

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
            }
        )

    # Overall summary (compute percentages)
    if total_stats.code_lines > 0:
        total_stats.log_coverage_percent = (
            total_stats.log_statements / total_stats.code_lines * 100
        )
        total_stats.function_coverage_percent = (
            (total_stats.functions_with_logging / total_stats.functions * 100)
            if total_stats.functions > 0
            else 0
        )

    if output_format == "json":
        # Machine-readable JSON output
        report = {
            "files": rows,
            "summary": {
                "total_files": len(python_files),
                "files_with_issues": total_issues,
                "total_code_lines": total_stats.code_lines,
                "total_log_statements": total_stats.log_statements,
                "overall_logging_coverage": round(total_stats.log_coverage_percent, 1),
                "functions": total_stats.functions,
                "functions_with_logging": total_stats.functions_with_logging,
                "function_logging_coverage": round(total_stats.function_coverage_percent, 1),
            },
        }
        print(json.dumps(report, ensure_ascii=False))
    elif output_format == "toml":
        # Machine-readable TOML output
        report = {
            "files": rows,
            "summary": {
                "total_files": len(python_files),
                "files_with_issues": total_issues,
                "total_code_lines": total_stats.code_lines,
                "total_log_statements": total_stats.log_statements,
                "overall_logging_coverage": round(total_stats.log_coverage_percent, 1),
                "functions": total_stats.functions,
                "functions_with_logging": total_stats.functions_with_logging,
                "function_logging_coverage": round(total_stats.function_coverage_percent, 1),
            },
        }
        print(toml.dumps(report))
    else:
        # Human-friendly table output with subtle colors
        colorama_init(autoreset=True)
        # Determine dynamic column widths
        module_width = max([len("MODULE")] + [len(r["module"]) for r in rows])
        lines_width = max(len("LINES"), *(len(str(r["lines"])) for r in rows))
        logs_width = max(len("LOGS"), *(len(str(r["logs"])) for r in rows))
        cov_width = max(len("COVERAGE"), *(len(f"{r['coverage']:.1f}%") for r in rows))
        issues_width = len("ISSUES")
        primary_width = max(len("SUMMARY"), *(len(r["primary"]) for r in rows))

        h_module = Fore.CYAN + Style.BRIGHT + "MODULE" + Style.RESET_ALL
        h_lines = Fore.CYAN + Style.BRIGHT + "LINES" + Style.RESET_ALL
        h_logs = Fore.CYAN + Style.BRIGHT + "LOGS" + Style.RESET_ALL
        h_cov = Fore.CYAN + Style.BRIGHT + "COVERAGE" + Style.RESET_ALL
        h_issues = Fore.CYAN + Style.BRIGHT + "ISSUES" + Style.RESET_ALL
        h_summary = Fore.CYAN + Style.BRIGHT + "SUMMARY" + Style.RESET_ALL

        header = (
            f"{h_module.ljust(module_width + (len(h_module)-len('MODULE')))}  "
            f"{h_lines.rjust(lines_width + (len(h_lines)-len('LINES')))}  "
            f"{h_logs.rjust(logs_width + (len(h_logs)-len('LOGS')))}  "
            f"{h_cov.rjust(cov_width + (len(h_cov)-len('COVERAGE')))}  "
            f"{h_issues.rjust(issues_width + (len(h_issues)-len('ISSUES')))}  "
            f"{h_summary.ljust(primary_width + (len(h_summary)-len('SUMMARY')))}"
        )
        sep = "-" * (module_width + lines_width + logs_width + cov_width + issues_width + primary_width + 10)
        print(header)
        print(sep)
        for r in rows:
            issues_txt = []
            if r["errors"]:
                issues_txt.append(Fore.RED + f"E{r['errors']}" + Style.RESET_ALL)
            if r["warnings"]:
                issues_txt.append(Fore.YELLOW + f"W{r['warnings']}" + Style.RESET_ALL)
            issues_cell = " ".join(issues_txt)
            coverage_txt = f"{r['coverage']:.1f}%"
            cov_colored = (
                Fore.GREEN + coverage_txt + Style.RESET_ALL if r["coverage"] >= 5.0 and r["coverage"] <= 15.0
                else (Fore.RED + coverage_txt + Style.RESET_ALL if r["coverage"] < 5.0 else Fore.YELLOW + coverage_txt + Style.RESET_ALL)
            )
            print(
                f"{r['module'].ljust(module_width)}  "
                f"{str(r['lines']).rjust(lines_width)}  "
                f"{str(r['logs']).rjust(logs_width)}  "
                f"{cov_colored.rjust(cov_width + (len(cov_colored)-len(coverage_txt)))}  "
                f"{issues_cell.rjust(issues_width + (len(issues_cell)-len(' '.join(issues_txt))))}  "
                f"{r['primary'].ljust(primary_width)}"
            )

        # Global issue legend: what E#/W# counts refer to and categories
        print()
        legend_title = Fore.CYAN + Style.BRIGHT + "ISSUE LEGEND" + Style.RESET_ALL
        print(legend_title)
        print("  " + Fore.RED + "E#" + Style.RESET_ALL + " = number of error-level findings; categories:")
        print("    " + Fore.RED + "E1" + Style.RESET_ALL + ": Too little logging")
        print("    " + Fore.RED + "E2" + Style.RESET_ALL + ": Too few functions have logging")
        print("    " + Fore.RED + "E3" + Style.RESET_ALL + ": Log statement issues")
        print("  " + Fore.YELLOW + "W#" + Style.RESET_ALL + " = number of warning-level findings; categories:")
        print("    " + Fore.YELLOW + "W1" + Style.RESET_ALL + ": Possibly too much logging")
        print("    " + Fore.YELLOW + "W2" + Style.RESET_ALL + ": Almost every function logs")

    if output_format not in {"json", "toml"}:
        print("=" * 60)
        print("📊 OVERALL LOGGING QUALITY REPORT")
        print("=" * 60)
        print(f"Total files analyzed: {len(python_files)}")
        print(f"Total code lines: {total_stats.code_lines}")
        print(f"Total log statements: {total_stats.log_statements}")
        print(f"Overall logging coverage: {total_stats.log_coverage_percent:.1f}%")
        print(
            f"Functions with logging: {total_stats.functions_with_logging}/{total_stats.functions} ({total_stats.function_coverage_percent:.1f}%)"
        )

    if total_issues == 0:
        if output_format not in {"json", "toml"}:
            print("\n🎉 All files have appropriate logging coverage! Well done!")
        return True
    else:
        if output_format not in {"json", "toml"}:
            print(f"\n💥 {total_issues} files need logging attention!")
        return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Logging Linter - Ensures your code has appropriate logging coverage",
        epilog="Like a politeness compiler, but for log statements! 🚽📝",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to analyze (default: current directory)",
    )
    parser.add_argument(
        "--min-coverage",
        type=float,
        default=5.0,
        help="Minimum logging coverage percentage (default: 5.0)",
    )
    parser.add_argument(
        "--max-coverage",
        type=float,
        default=15.0,
        help="Maximum logging coverage percentage (default: 15.0)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Use stricter coverage requirements (3-10%)",
    )
    parser.add_argument(
        "--analyze-statements",
        action="store_true",
        help="Analyze individual log statements for common issues",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed statement breakdown when analyzing statements",
    )
    parser.add_argument(
        "--allow-snake-case",
        action="store_true",
        help="Allow snake_case event IDs (default: prefer dash-case)",
    )

    args = parser.parse_args()

    if args.strict:
        args.min_coverage = 3.0
        args.max_coverage = 10.0

    path = Path(args.path)
    if not path.exists():
        print(f"Error: Path {path} does not exist!", file=sys.stderr)
        sys.exit(1)

    if path.is_file():
        stats = analyze_file(path)
        issues = check_logging_quality(stats, args.min_coverage, args.max_coverage)
        print(f"📁 {path}")
        for issue in issues:
            print(f"   {issue}")
        
        # Analyze statements for single file if requested
        if args.analyze_statements:
            log_analysis = analyze_log_statements(path, prefer_dash_case=not args.allow_snake_case)
            if log_analysis.total_statements > 0:
                statement_issues = sum(len(s.issues) for s in log_analysis.statements)
                print(f"   Log statements: {log_analysis.total_statements} ({statement_issues} issues)")
                if args.verbose:
                    for stmt in log_analysis.statements:
                        if stmt.issues:
                            issues_str = ', '.join(stmt.issues)
                            event_str = f"'{stmt.event_id}'" if stmt.event_id else "NO_EVENT"
                            print(f"     L{stmt.line_number}: {stmt.method}({event_str}) ❌ {issues_str}")
        
        success = not any("❌" in issue for issue in issues)
    else:
        success = lint_directory(path, args.min_coverage, args.max_coverage, 
                                args.analyze_statements, args.verbose, args.allow_snake_case)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
