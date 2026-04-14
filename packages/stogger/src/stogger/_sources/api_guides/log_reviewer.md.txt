# Log Reviewer Module

:::{admonition} Test Coverage: 98.0%
:class: tip

This module has high test coverage and is well-documented.
:::

The `stogger.log_reviewer` module provides tools for analyzing and reviewing log quality in Python codebases.

## Overview

Log reviewer helps you:
- Analyze log statement quality
- Detect common logging anti-patterns
- Review log message structure
- Generate quality reports

## Quick Start

```python
from pathlib import Path
from stoggertools.log_reviewer import LogQualityReviewer, print_report

reviewer = LogQualityReviewer()

# Analyze a single log file
report = reviewer.analyze_log_file(Path("logs/app.log"))
print(f"Score: {report.overall_score}/100")
print(f"Verdict: {report.overall_verdict}")
print_report(report)
```

## Main Functions

### LogQualityReviewer

Create a reviewer instance and analyze log files or raw log content.

```python
from pathlib import Path
from stoggertools.log_reviewer import LogQualityReviewer

reviewer = LogQualityReviewer()

# Analyze a log file on disk
report = reviewer.analyze_log_file(Path("logs/app.log"))

# Analyze log content directly (e.g. from a string)
report = reviewer.analyze_log_content("""2025-01-15 10:30:00 INFO user_login user_id=42 session_id=abc
2025-01-15 10:30:01 ERROR db_query_failed query="SELECT *" duration_ms=500""")
```

### LogQualityReport

The dataclass returned by every analysis method.

```python
from stoggertools.log_reviewer import LogQualityReport

report: LogQualityReport = reviewer.analyze_log_file(Path("logs/app.log"))
report.overall_score      # 0-100 float
report.overall_verdict    # "arsch" | "mäßig" | "schlecht" | "verziehbar" | "leiwand"
report.issues             # list of issue descriptions
report.good_practices     # list of good-practice descriptions
report.suggestions        # list of improvement suggestions
report.stats              # dict with structured/unstructured line counts, levels, etc.
```

### print_report

Pretty-print a `LogQualityReport` to stdout.

```python
from stoggertools.log_reviewer import print_report

print_report(report)       # text format (default)
print_report(report, format_type="json")
```

## Quality Checks

The reviewer checks for:

1. **Message Quality**
   - Descriptive event names
   - Proper use of structured data
   - Avoiding string interpolation in messages

2. **Log Levels**
   - Appropriate level usage
   - Consistent level patterns

3. **Context**
   - Sufficient contextual data
   - Proper key naming

4. **Anti-Patterns**
   - Overly verbose logging
   - Missing error context
   - Hardcoded values

## Example Report

```python
from pathlib import Path
from stoggertools.log_reviewer import LogQualityReviewer

reviewer = LogQualityReviewer()
report = reviewer.analyze_log_file(Path("logs/app.log"))

print(f"\nVerdict: {report.overall_verdict}")
print(f"  Score: {report.overall_score}/100")

print("\nIssues:")
for issue in report.issues:
    print(f"  - {issue}")

print("\nGood practices:")
for practice in report.good_practices:
    print(f"  - {practice}")

print("\nSuggestions:")
for suggestion in report.suggestions:
    print(f"  - {suggestion}")

print(f"\nStats: {report.stats}")
```

## API Reference

```{autoapi} stogger.log_reviewer
:members:
```
