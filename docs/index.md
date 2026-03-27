# nicestlog Documentation

```{image} assets/nicestlog_logo_ascii.txt
:alt: nicestlog logo
```

**A sophisticated multi-target structured logging system built on structlog**

Welcome to the comprehensive documentation for nicestlog - your go-to solution for elegant, structured, and powerful logging in Python applications.

## Quick Start

Install nicestlog and start logging:

```bash
pip install nicestlog
```

```python
import nicestlog
import structlog

# Initialize console logging and get a structlog logger
nicestlog.init_logging(verbose=True)
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
user_guide/best_practices
user_guide/advanced_features
user_guide/quick_practices
user_guide/nix_integration
user_guide/cli_reference
```

## Features

```{toctree}
:maxdepth: 2
:caption: Features

features/advanced_assistant
features/log_analysis
features/integrations
```

## API Reference

```{toctree}
:maxdepth: 2
:caption: API Reference

api/index
```

## Coverage-Based API Guides

Documentation prioritized by test coverage:

```{toctree}
:maxdepth: 2
:caption: High Coverage Modules (≥80%)

api_guides/core
api_guides/factory
api_guides/config
api_guides/advanced_assistant
api_guides/log_reviewer
```

```{toctree}
:maxdepth: 1
:caption: Medium Coverage Modules (40-80%)

api_guides/assistant
api_guides/cli
api_guides/linter
api_guides/pii_scrubber
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
