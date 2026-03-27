# CLI Module

:::{admonition} Test Coverage: 52.0%
:class: warning

This module has moderate test coverage. Some features may not work as expected.
:::

The `nicestlog.cli` module provides the command-line interface for nicestlog.

## Usage

```bash
# Lint a file or directory
nicestlog check src/my_module.py

# Migrate print statements to structured logging
nicestlog migrate src/ --dry-run

# Initialize nicestlog in a project
nicestlog init

# Review log quality
nicestlog tools review src/

# Serve documentation
nicestlog docs serve

# Check translations
nicestlog i18n check
```

## Main Commands

### check

Main linting command for analyzing Python files for logging issues.

```bash
nicestlog check [PATH]
```

### migrate

Migrate print statements to structured logging.

```bash
nicestlog migrate [PATH]
```

### init

Initialize nicestlog in a project.

```bash
nicestlog init
```

### docs

Documentation commands.

```bash
nicestlog docs serve
```

### tools

Utility commands for advanced features.

```bash
# Review log quality
nicestlog tools review [PATH]

# Advanced AST-based checks
nicestlog tools check-advanced [PATH]

# View systemd journal
nicestlog tools journal

# Launch web dashboard
nicestlog tools dashboard

# Demo features
nicestlog tools demo

# Generate systemd service file
nicestlog tools generate-service
```

### i18n

Internationalization commands.

```bash
# Check translations
nicestlog i18n check
```

## API Reference

```{autoapi} nicestlog.cli
:members:
```
