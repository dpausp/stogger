# Log Statement Analyzer Module

:::{warning} Limited Test Coverage (18.1%)

This module has limited test coverage. Use at your own risk. Contributions to improve test coverage are welcome.
:::

The `stogger.log_statement_analyzer` module provides AST-based analysis of log statements to detect common issues and patterns.

## Basic Usage

```python
from pathlib import Path
from stogger.log_statement_analyzer import LogStatementAnalyzer

analyzer = LogStatementAnalyzer(prefer_dash_case=True)
analyzer.analyze_file(Path("src/module.py"))

for statement in analyzer.statements:
    print(f"Line {statement.line_number}: {statement.method} - {statement.issues}")
```

## LogStatementAnalyzer

AST visitor that analyzes log statements in Python files.

```python
from stogger.log_statement_analyzer import LogStatementAnalyzer

analyzer = LogStatementAnalyzer(
    prefer_dash_case=True,  # Enforce dash-case event IDs
)

# Analyze a file
result = analyzer.analyze_file(Path("module.py"))
```

### Analysis

The analyzer detects:
- Missing event IDs
- Dash-case violations in event names
- Single string arguments (should use structured data)
- Magic argument usage (`_replace_msg`, `exc_info`, etc.)
- Logger variable tracking (follows `log = get_logger()` patterns)

## Data Classes

### LogStatement

Represents a parsed log statement.

```python
@dataclass
class LogStatement:
    line_number: int
    method: str                    # info, debug, warning, error, etc.
    event_id: str | None
    has_event_id: bool
    event_id_format: str           # "dash-case", "snake_case", "camelCase", "invalid"
    arguments: list[str]
    keyword_args: dict[str, str]
    magic_args: set[str]
    raw_call: str
    issues: list[str]
```

### LogAnalysisResult

Results of analyzing log statements in a file.

```python
@dataclass
class LogAnalysisResult:
    file_path: Path
    statements: list[LogStatement]
    total_statements: int
    statements_with_event_id: int
    statements_without_event_id: int
    dash_case_violations: int
    single_string_args: int
    magic_args_usage: dict[str, int]
```

## API Reference

```{autoapi} stogger.log_statement_analyzer
:members:
```
