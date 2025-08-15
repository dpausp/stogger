"""
AST-based log statement analyzer for nicestlog.

Analyzes log statements to detect common issues and patterns.
"""

import ast
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Set
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
            'info', 'debug', 'warning', 'warn', 'error', 'critical', 'exception', 'trace'
        }
        self.magic_args = {
            '_replace_msg', 'exc_info', '_structured', '_level', '_name'
        }
    
    def visit_Call(self, node: ast.Call) -> None:
        """Visit function calls to detect log statements."""
        if self._is_log_call(node):
            statement = self._parse_log_statement(node, self.prefer_dash_case)
            self.statements.append(statement)
        
        self.generic_visit(node)
    
    def _is_log_call(self, node: ast.Call) -> bool:
        """Check if this is a logging method call."""
        try:
            if isinstance(node.func, ast.Attribute):
                return node.func.attr in self.log_methods
            return False
        except AttributeError:
            return False
    
    def _parse_log_statement(self, node: ast.Call, prefer_dash_case: bool = True) -> LogStatement:
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
        issues = self._detect_issues(method, args, kwargs, magic_args, event_id, event_id_format, prefer_dash_case)
        
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
            issues=issues
        )
    
    def _check_event_id_format(self, event_id: str) -> str:
        """Check the format of an event ID."""
        if not event_id:
            return "none"
        
        # dash-case: all lowercase with hyphens (allow numbers)
        if re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', event_id):
            return "dash-case"
        
        # snake_case: all lowercase with underscores
        if re.match(r'^[a-z]+(_[a-z]+)*$', event_id):
            return "snake_case"
        
        # camelCase: starts lowercase, then camelCase
        if re.match(r'^[a-z]+([A-Z][a-z]*)*$', event_id):
            return "camelCase"
        
        # PascalCase: starts uppercase
        if re.match(r'^[A-Z][a-z]*([A-Z][a-z]*)*$', event_id):
            return "PascalCase"
        
        return "invalid"
    
    def _detect_issues(self, method: str, args: List[str], kwargs: Dict[str, str], 
                      magic_args: Set[str], event_id: Optional[str], 
                      event_id_format: str, prefer_dash_case: bool = True) -> List[str]:
        """Detect common issues in log statements."""
        issues = []
        
        # Check for missing event ID
        if not event_id:
            issues.append("missing_event_id")
        
        # Check event ID format (configurable preference for dash-case)
        if event_id and event_id_format not in ["dash-case"]:
            # Only report if not allowing snake_case or if it's not snake_case
            if not (event_id_format == "snake_case" and not prefer_dash_case):
                issues.append(f"event_id_not_dash_case (found: {event_id_format})")
        
        # Check for single string argument (anti-pattern)
        if len(args) == 1 and not kwargs and not magic_args:
            issues.append("single_string_argument")
        
        # Check for f-string in event ID (anti-pattern)
        if event_id and ('{' in event_id or '}' in event_id):
            issues.append("fstring_in_event_id")
        
        # Check for debug with _replace_msg (usually not needed)
        if method == "debug" and "_replace_msg" in magic_args:
            issues.append("debug_with_replace_msg")
        
        # Check for proper structured data
        if event_id and not kwargs and "_replace_msg" not in magic_args:
            issues.append("no_structured_data")
        
        return issues


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
        dash_case_violations = sum(1 for s in statements 
                                 if s.event_id and s.event_id_format != "dash-case")
        single_string_args = sum(1 for s in statements 
                               if "single_string_argument" in s.issues)
        
        # Count magic args usage
        magic_usage = {}
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
            magic_args_usage=magic_usage
        )
        
    except Exception as e:
        # Return empty result on error
        return LogAnalysisResult(
            file_path=file_path,
            statements=[],
            total_statements=0,
            statements_with_event_id=0,
            statements_without_event_id=0,
            dash_case_violations=0,
            single_string_args=0,
            magic_args_usage={}
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
        magic_summary = ", ".join(f"{k}:{v}" for k, v in result.magic_args_usage.items())
        print(f"   🪄 Magic args: {magic_summary}")
    
    if verbose:
        print("   Detailed statements:")
        for stmt in result.statements:
            issues_str = f" ❌ {', '.join(stmt.issues)}" if stmt.issues else " ✅"
            event_str = f"'{stmt.event_id}'" if stmt.event_id else "NO_EVENT"
            magic_str = f" magic:{list(stmt.magic_args)}" if stmt.magic_args else ""
            print(f"     L{stmt.line_number}: {stmt.method}({event_str}){magic_str}{issues_str}")
    
    print()


def main():
    """CLI entry point for log statement analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze log statements in Python files")
    parser.add_argument("path", help="File or directory to analyze")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Show detailed statement breakdown")
    parser.add_argument("--allow-snake-case", action="store_true",
                       help="Allow snake_case event IDs (default: prefer dash-case)")
    
    args = parser.parse_args()
    
    path = Path(args.path)
    
    if path.is_file():
        if path.suffix == ".py":
            result = analyze_file(path, prefer_dash_case=not args.allow_snake_case)
            print_analysis_summary(result, args.verbose)
    else:
        python_files = list(path.rglob("*.py"))
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
        
        print(f"📊 Summary: {total_files} files, {total_statements} log statements, {total_issues} issues")


if __name__ == "__main__":
    main()