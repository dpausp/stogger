# stogger Documentation

```{image} assets/stogger_logo_ascii.txt
:alt: stogger logo
```

**A sophisticated multi-target structured logging system built on structlog**

Welcome to the comprehensive documentation for stogger - your go-to solution for elegant, structured, and powerful logging in Python applications.

## Quick Start

Install stogger and start logging:

```bash
pip install stogger
```

```python
import stogger
import structlog

# Initialize console logging and get a structlog logger
stogger.init_logging(verbose=True)
log = structlog.get_logger()
log.info("hello-world", user_id=123, action="login")
```

## Key Features

- **Advanced AST Assistant** - Revolutionary code transformation
- **Log Statement Analysis** - Intelligent issue detection
- **Best Practices** - Proven logging patterns
- **Beautiful Output** - Colorful and structured logs
- **Multiple Integrations** - Eliot, systemd, and more

## User Guide

```{toctree}
:maxdepth: 2
:caption: User Guide

user_guide/getting_started
user_guide/logging_patterns
user_guide/testing

user_guide/cheatsheet
user_guide/nix_integration
user_guide/cli_reference
user_guide/migration_examples
```

## Features

```{toctree}
:maxdepth: 2
:caption: Features

features/advanced_assistant
features/log_analysis
features/integrations
features/i18n
```

## API Reference

```{toctree}
:maxdepth: 2
:caption: API Reference

api/index
```

## Development

```{toctree}
:maxdepth: 2
:caption: Development

development/type_checking_guide
development/test_improvements_summary
```

## Migration Guides

```{toctree}
:maxdepth: 2
:caption: Migration Guides

agents/migration_guide
agents/migration_templates
```

## Indices

- {ref}`genindex`
- {ref}`modindex`
- {ref}`search`
