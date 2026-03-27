# Linter Module

:::{admonition} Test Coverage: 73.7%
:class: warning

This module has moderate test coverage. Some features may not work as expected.
:::

The `nicestlog.linter` module provides linting capabilities for log statements.

## Basic Usage

```python
from pathlib import Path
from nicestlog.linter import LintOptions, lint_directory

# Lint all Python files in a project directory
options = LintOptions(min_coverage=5.0, max_coverage=15.0, verbose=True)
passed = lint_directory(Path("src"), options)
```

## Lint Checks

The linter checks for:

- Missing event names
- Inconsistent key naming
- Missing context data
- Hardcoded values in messages
- Improper log level usage

## API Reference

```{autoapi} nicestlog.linter
:members:
```
