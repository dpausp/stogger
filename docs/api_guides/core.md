# Core Module

:::{admonition} Test Coverage: 82.7%
:class: tip

This module has high test coverage and is well-documented.
:::

The `nicestlog.core` module provides the core logging functionality for nicestlog, including renderers, processors, and logger factories.

## Quick Start

```python
import nicestlog
import structlog

# Initialize console logging
nicestlog.init_logging(verbose=True)

# Get a logger
log = structlog.get_logger()
log.info("hello-world", user_id=123, action="login")
```

## Main Functions

### init_logging

Initialize the logging system with multiple output targets.

```python
nicestlog.init_logging(
    verbose=True,           # Enable debug-level logging
    logdir=None,            # Directory for log files
    log_cmd_output=False,   # Enable command output logging
    log_to_console=True,    # Output to console
    syslog_identifier="nicestlog",  # Systemd journal identifier
    show_caller_info=False  # Include caller info in logs
)
```

### init_early_logging

Initialize minimal logging early in application startup to reduce uninitialized structlog messages.

```python
nicestlog.init_early_logging()
```

### logging_initialized

Check if logging has been configured.

```python
if nicestlog.logging_initialized():
    print("Logging is configured")
```

## Renderers

### ConsoleFileRenderer

Renders log events with colors and alignment for console output.

```python
from nicestlog.core import ConsoleFileRenderer

renderer = ConsoleFileRenderer(
    min_level="info",
    show_caller_info=True
)
```

### JSONRenderer

Renders log events as JSON for structured logging.

```python
from nicestlog.core import JSONRenderer

renderer = JSONRenderer(min_level="debug")
```

### SystemdJournalRenderer

Renders log events for systemd journal integration.

```python
from nicestlog.core import SystemdJournalRenderer

renderer = SystemdJournalRenderer(
    syslog_identifier="my-app",
    syslog_facility=syslog.LOG_LOCAL0
)
```

## Processors

### add_pid

Adds the process ID to each log event.

### add_caller_info

Adds caller information (file, function, line number) to log events.

### process_exc_info

Processes exception information in log events.

### format_exc_info

Formats exception information for structured output.

## Logger Classes

### MultiOptimisticLogger

A logger that distributes messages to multiple loggers (console, file, journal).

### MultiOptimisticLoggerFactory

Factory for creating MultiOptimisticLogger instances.

### JournalLogger / JournalLoggerFactory

Logger for systemd journal integration.

## Example Usage

```python
import nicestlog
import structlog
from pathlib import Path

# Initialize with file logging
nicestlog.init_logging(
    verbose=True,
    logdir=Path("/var/log/myapp"),
    log_to_console=True
)

log = structlog.get_logger()

# Log with structured data
log.info(
    "user-login",
    user_id=123,
    ip_address="192.168.1.1",
    session_id="abc123"
)

# Log with exception info
try:
    risky_operation()
except Exception as e:
    log.exception("operation-failed", error=str(e))
```

## API Reference

```{autoapi} nicestlog.core
:members:
```
