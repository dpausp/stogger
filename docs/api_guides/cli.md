# CLI Module

:::{admonition} Test Coverage: 52.0%
:class: warning

This module has moderate test coverage. Some features may not work as expected.
:::

The `nicestlog.cli` module provides the command-line interface for nicestlog.

## Usage

```bash
# Analyze a file
nicestlog analyze src/my_module.py

# Transform a directory
nicestlog transform src/ --dry-run

# Serve documentation
nicestlog docs serve

# Review log quality
nicestlog review src/
```

## Main Commands

### analyze

Analyze Python files for logging patterns and issues.

```bash
nicestlog analyze [PATH] [--verbose]
```

### transform

Transform print statements to structured logging.

```bash
nicestlog transform [PATH] [--dry-run] [--verbose]
```

### review

Review log quality in Python files.

```bash
nicestlog review [PATH] [--format json]
```

### docs

Documentation commands.

```bash
nicestlog docs serve [--port 8000]
nicestlog docs build
```

## API Reference

```{autoapi} nicestlog.cli
:members:
```
