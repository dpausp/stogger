# stogger Documentation

```{image} assets/stogger_logo_ascii.txt
:alt: stogger logo
```

**Multi-target structured logging built on structlog**

Console, file, systemd journal, and PostgreSQL targets — plus AST-based convention checking via pytest-stogger.

## Quick Start

Install stogger and start logging:

```bash
uv add stogger
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

- **Multi-Target Output** — Simultaneous console (colorized), file, systemd journal, and PostgreSQL targets via `MultiRenderer`
- **Logging Decorators** — `@log_call`, `@log_result`, `@log_operation` decorators and `log_scope()` context manager with sync/async support
- **Message Translation** — TOML-based i18n with `_replace_msg` pattern for human-readable formatted log messages
- **Flexible Timestamps** — Configurable precision: `iso`, `iso_seconds`, `iso_no_z`, or `relative` (process-elapsed)
- **AST Convention Checking** — pytest-stogger enforces 13 logging rules (except-must-log, no-info-in-except, etc.) at test time
- **JSON Output** — Switch to structured JSON with `log_format="json"` in `[tool.stogger]`

## User Guide

```{toctree}
:maxdepth: 2
:caption: User Guide

user/index
```


## Development

```{toctree}
:maxdepth: 2
:caption: Development

dev/index
```
