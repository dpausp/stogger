"""
Logging Linter - Ensures proper logging coverage in your codebase.

Like a politeness compiler, but for log statements!
"""

import ast
import argparse
import sys
from pathlib import Path
from typing import List
from dataclasses import dataclass


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
    directory: Path, min_coverage: float = 5.0, max_coverage: float = 15.0
) -> bool:
    """Lint all Python files in a directory and its subdirectories."""
    # Recursively find all Python files in the directory
    python_files = list(directory.rglob("*.py"))

    if not python_files:
        print("No Python files found in the specified directory!")
        return True

    total_issues = 0
    total_stats = LoggingStats(0, 0, 0, 0, 0, 0.0, 0.0)

    print(f"🔍 Analyzing {len(python_files)} Python files in {directory} for logging quality...\n")
    
    if any(python_files):
        print("📁 MODULE │ LINES:LOGS (COVERAGE%) │ ISSUES")
        print("─" * 50)

    for file_path in python_files:
        # Skip __pycache__ and other irrelevant files
        if "__pycache__" in str(file_path) or file_path.name.startswith("."):
            continue

        stats = analyze_file(file_path)
        issues = check_logging_quality(stats, min_coverage, max_coverage)

        # Accumulate totals
        total_stats.total_lines += stats.total_lines
        total_stats.code_lines += stats.code_lines
        total_stats.log_statements += stats.log_statements
        total_stats.functions += stats.functions
        total_stats.functions_with_logging += stats.functions_with_logging

        # Count issues and prepare compact summary
        error_count = sum(1 for issue in issues if "❌" in issue)
        warning_count = sum(1 for issue in issues if "⚠️" in issue)
        
        if error_count > 0 or warning_count > 0:
            total_issues += 1
            # One-line summary per module
            status_icons = []
            if error_count > 0:
                status_icons.append(f"❌{error_count}")
            if warning_count > 0:
                status_icons.append(f"⚠️{warning_count}")
            
            print(f"📁 {file_path.relative_to(directory)} │ "
                  f"Lines:{stats.code_lines} Logs:{stats.log_statements} "
                  f"({stats.log_coverage_percent:.1f}%) │ {' '.join(status_icons)}")

    # Overall summary
    if total_stats.code_lines > 0:
        total_stats.log_coverage_percent = (
            total_stats.log_statements / total_stats.code_lines * 100
        )
        total_stats.function_coverage_percent = (
            (total_stats.functions_with_logging / total_stats.functions * 100)
            if total_stats.functions > 0
            else 0
        )

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
        print("\n🎉 All files have appropriate logging coverage! Well done!")
        return True
    else:
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
        success = not any("❌" in issue for issue in issues)
    else:
        success = lint_directory(path, args.min_coverage, args.max_coverage)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
