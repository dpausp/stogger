# Linter Module

:::{admonition} Test Coverage: 73.7%
:class: warning

This module has moderate test coverage. Some features may not work as expected.
:::

The `nicestlog.linter` module provides linting capabilities for log statements.

## Basic Usage

```python
from pathlib import Path
from nicestlog.linter import lint_file

# Lint a single file
issues = lint_file(Path("my_module.py"))
for issue in issues:
    print(f"{issue.line}: {issue.message}")
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
