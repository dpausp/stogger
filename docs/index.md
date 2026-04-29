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

user_guide/index
```

## Features

```{toctree}
:maxdepth: 2
:caption: Features

features/index
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

development/index
```


## Indices

- {ref}`genindex`
- {ref}`modindex`
- {ref}`search`
