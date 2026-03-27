# Factory Module

:::{admonition} Test Coverage: 82.7%
:class: tip

This module has high test coverage and is well-documented.
:::

The `nicestlog.factory` module provides factory functions for building nicestlog components, including processors, renderers, and stdlib integration.

## Overview

Factory functions simplify the configuration of nicestlog by providing pre-built processor chains and renderer setups.

## Main Functions

### build_shared_processors

Builds processors that are shared between sync and async logging modes.

```python
from nicestlog.factory import build_shared_processors
from nicestlog.config import NicestLogConfig

config = NicestLogConfig(verbose=True)
processors = build_shared_processors(config)
```

This creates a processor chain including:
- Log level addition
- Timestamp generation
- PID addition
- Caller info addition
- Exception processing
- PII scrubbing (if enabled)
- Translation (if enabled)
- Final renderer

### build_renderer

Builds the final renderer based on configuration.

```python
from nicestlog.factory import build_renderer
from nicestlog.config import NicestLogConfig

config = NicestLogConfig(log_format="json")
renderer = build_renderer(config)
```

### configure_stdlib_logging

Configures Python's standard logging library to work with structlog.

```python
from nicestlog.factory import configure_stdlib_logging
from nicestlog.config import NicestLogConfig

config = NicestLogConfig(
    logdir=Path("/var/log/myapp"),
    log_to_console=True,
    async_logging=True
)
processors = build_shared_processors(config)
configure_stdlib_logging(config, processors)
```

## Example: Full Setup

```python
from pathlib import Path
from nicestlog.config import NicestLogConfig
from nicestlog.factory import build_shared_processors, configure_stdlib_logging

# Create configuration
config = NicestLogConfig(
    verbose=True,
    logdir=Path("./logs"),
    log_format="simple",
    log_to_console=True,
    enable_pii_scrubbing=True
)

# Build processors
processors = build_shared_processors(config)

# Configure stdlib logging
configure_stdlib_logging(config, processors)

# Now use structlog
import structlog
log = structlog.get_logger()
log.info("application-started")
```

## Async Logging

Enable async logging for better performance in high-throughput applications:

```python
config = NicestLogConfig(
    async_logging=True,
    logdir=Path("./logs")
)
```

This uses a QueueHandler and QueueListener to handle log messages asynchronously.

## API Reference

```{autoapi} nicestlog.factory
:members:
```
