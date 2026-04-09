# CLI Module

:::{admonition} Test Coverage: 52.0%
:class: warning

This module has moderate test coverage. Some features may not work as expected.
:::

The `stogger.cli` module provides the command-line interface for stogger.

## Usage

```bash
# Lint a file or directory
stoggertools check src/my_module.py

# Migrate print statements to structured logging
stoggertools migrate src/ --dry-run

# Initialize stogger in a project
stoggertools init

# Review log quality
stoggertools tools review src/

# Serve documentation
stoggertools docs serve

# Check translations
stoggertools tools i18n check
```

## Main Commands

### check

Main linting command for analyzing Python files for logging issues.

```bash
stoggertools check [PATH]
```

### migrate

Migrate print statements to structured logging.

```bash
stoggertools migrate [PATH]
```

### init

Initialize stogger in a project.

```bash
stoggertools init
```

### docs

Documentation commands.

```bash
stoggertools docs serve
```

### tools

Utility commands for advanced features.

```bash
# Review log quality
stoggertools tools review [PATH]

# Advanced AST-based checks
stoggertools tools check-advanced [PATH]

# View systemd journal
stoggertools tools journal

# Launch web dashboard
stoggertools tools dashboard

# Demo features
stoggertools tools demo

# Generate systemd service file
stoggertools tools generate-service
```

### i18n

Internationalization commands.

```bash
# Check translations
stoggertools tools i18n check
```

## API Reference

```{autoapi} stogger.cli
:members:
```
