# Log Reviewer Module

:::{admonition} Test Coverage: 98.0%
:class: tip

This module has high test coverage and is well-documented.
:::

The `nicestlog.log_reviewer` module provides tools for analyzing and reviewing log quality in Python codebases.

## Overview

Log reviewer helps you:
- Analyze log statement quality
- Detect common logging anti-patterns
- Review log message structure
- Generate quality reports

## Quick Start

```python
from pathlib import Path
from nicestlog.log_reviewer import review_file

# Review a single file
report = review_file(Path("my_module.py"))
print(f"Score: {report.score}")
print(f"Issues: {report.issues}")
```

## Main Functions

### review_file

Analyze a Python file for log quality issues.

```python
from nicestlog.log_reviewer import review_file
from pathlib import Path

report = review_file(Path("module.py"))
```

### review_directory

Analyze all Python files in a directory.

```python
from nicestlog.log_reviewer import review_directory
from pathlib import Path

reports = review_directory(Path("src/"))
for report in reports:
    print(f"{report.file_path}: {report.score}")
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
from nicestlog.log_reviewer import review_directory

reports = review_directory(Path("src/"))

for report in reports:
    print(f"\n{report.file_path}:")
    print(f"  Score: {report.score}/100")
    print(f"  Log statements: {report.log_statement_count}")
    
    for issue in report.issues:
        print(f"  Issue: {issue.message}")
        print(f"    Line: {issue.line_number}")
        print(f"    Severity: {issue.severity}")
```

## API Reference

```{autoapi} nicestlog.log_reviewer
:members:
```
