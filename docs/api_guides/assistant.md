# Assistant Module

:::{admonition} Test Coverage: 67.1%
:class: warning

This module has moderate test coverage. Some features may not work as expected.
:::

The `stogger.assistant` module provides tools for migrating print statements to structured logging.

## Basic Usage

```python
from pathlib import Path
from stogger.assistant import migrate_directory

# Migrate all Python files in a directory
migrate_directory(Path("src/"))
```

## migrate_directory

Migrate all Python files in a directory from print statements to structured logging.

```python
from stogger.assistant import migrate_directory
from pathlib import Path

migrate_directory(
    directory=Path("src/"),
    dry_run=True  # Preview changes
)
```

## API Reference

```{autoapi} stogger.assistant
:members:
```
