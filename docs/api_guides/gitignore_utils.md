# Gitignore Utils Module

:::{admonition} Test Coverage: 66.0%
:class: warning

This module has moderate test coverage. Some features may not work as expected.
:::

The `nicestlog.gitignore_utils` module provides utilities for respecting `.gitignore` patterns during file analysis, ensuring that ignored files are not processed by nicestlog's analysis tools.

## Basic Usage

```python
from pathlib import Path
from nicestlog.gitignore_utils import filter_python_files

# Get Python files respecting .gitignore
files = filter_python_files(Path("src/"), respect_gitignore=True)
```

## Functions

### load_gitignore_patterns

Load patterns from a `.gitignore` file, plus common defaults.

```python
from nicestlog.gitignore_utils import load_gitignore_patterns

patterns = load_gitignore_patterns(Path("."))
# Returns: list of gitignore patterns including defaults
```

Default patterns always included:
- `.git/*`, `.venv/*`, `venv/*`, `__pycache__/*`
- `*.pyc`, `*.pyo`, `*.egg-info/*`
- `.tox/*`, `.pytest_cache/*`, `.mypy_cache/*`, `.ruff_cache/*`
- `build/*`, `dist/*`, `node_modules/*`

### should_ignore_path

Check if a file path should be ignored based on gitignore patterns.

```python
from nicestlog.gitignore_utils import should_ignore_path

ignored = should_ignore_path(
    file_path=Path("src/.venv/module.py"),
    base_dir=Path("src/"),
    patterns=[".venv/*"],
)
# Returns: True
```

### filter_python_files

Get Python files in a directory, respecting `.gitignore` if requested.

```python
from nicestlog.gitignore_utils import filter_python_files

# With gitignore respect
files = filter_python_files(Path("src/"), respect_gitignore=True)

# Without gitignore (include all .py files)
files = filter_python_files(Path("src/"), respect_gitignore=False)
```

## API Reference

```{autoapi} nicestlog.gitignore_utils
:members:
```
