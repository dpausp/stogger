# Nicestlog Best Practices

## Overview

Nicestlog uses a sophisticated structured logging system built on top of `structlog` that provides multi-target logging with different renderers for console output, systemd journal, and file logging. This document outlines best practices for using this logging system effectively.

## Table of Contents

1. [Basic Setup and Initialization](#basic-setup-and-initialization)
2. [Logger Creation and Usage](#logger-creation-and-usage)
3. [Log Levels and When to Use Them](#log-levels-and-when-to-use-them)
4. [Structured Logging Patterns](#structured-logging-patterns)
5. [Message Formatting](#message-formatting)
6. [Error Handling and Exception Logging](#error-handling-and-exception-logging)
7. [Testing Logging](#testing-logging)

## Basic Setup and Initialization

### Initialize Logging Early

Always initialize logging at the start of your application's execution.

```python
import nicestlog
import structlog
from pathlib import Path

# Initialize logging with appropriate settings
nicestlog.init_logging(
    verbose=True,  # Set to False in production for less noise
    logdir=Path("/var/log/myapp"),
    log_cmd_output=True,
    log_to_console=True,
    syslog_identifier="your-component",
    show_caller_info=False  # Enable for debugging
)

# Get a logger instance after initialization
log = structlog.get_logger()
```

### Configuration Parameters

- **verbose**: Controls console log level (`trace` if True, `info` if False).
- **logdir**: Directory for file logging. Enables file logging if provided.
- **log_cmd_output**: Enables a separate `commands.log` file (requires `logdir`).
- **log_to_console**: Force console logging on/off. If `None` (default), it's disabled when a systemd journal is detected.
- **syslog_identifier**: Identifier for journal and log file entries.
- **show_caller_info**: Adds file, function, and line number to logs. Useful for debugging, but has a performance cost.

## Logger Creation and Usage

### Get Logger Instances

Once `init_logging` has been called, you can get a logger anywhere in your application.

```python
import structlog

# Get the root logger
log = structlog.get_logger()

# Get a component-specific logger (recommended)
db_log = structlog.get_logger("database")
api_log = structlog.get_logger("api.v1")

# Bind context to create a specialized logger for a request or task
def handle_request(request):
    request_log = structlog.get_logger().bind(
        request_id=request.id,
        user_id=request.user.id
    )
    request_log.info("request-started")
    # ...
```

### Basic Logging

```python
# Simple message
log.info("user-logged-in")

# With structured data
log.info("user-logged-in", user_id=123, ip="192.168.1.1")

# With a human-readable template message
log.info(
    "user-login-event",
    _replace_msg="User {username} logged in from {ip}",
    username="alice",
    ip="192.168.1.1"
)
```

## Log Levels and When to Use Them

### TRACE / DEBUG
For detailed information, typically only of interest when diagnosing problems. `verbose=True` enables this level.

```python
log.debug("Processing item", item_id=item.id, status=item.status)
```

### INFO
For general information about program execution. This is the default level for production.

```python
log.info("application-started", version="1.2.3", port=8080)
```

### WARNING
For potentially harmful situations that don't prevent the program from continuing.

```python
log.warning("deprecated-api-used", endpoint="/old/api", user_id=123)
```

### ERROR
For error events that might still allow the application to continue running.

```python
log.error("failed-to-process-item", item_id=123, error=str(e))
```

### CRITICAL
For very serious error events that might cause the program to abort.

```python
log.critical("database-unavailable", error=str(e), exc_info=True)
```

## Structured Logging Patterns

### Use Event-Style Messages

Use kebab-case event names as the primary message for easy filtering and analysis.

```python
# Good - clear event names
log.info("database-connection-established", host="db.example.com")
log.info("cache-miss", key="user:123")
log.info("email-sent", recipient="user@example.com")

# Avoid - unclear or inconsistent naming
log.info("DB connected")
log.info("cache miss for user:123")
```

### Use Consistent Field Names

Establish conventions for field names (e.g., `user_id`, `request_id`, `duration_ms`).

## Message Formatting

### Checking i18n coverage

Use the built-in CLI to ensure your translations match your code usage.

- .info events without `_replace_msg` are treated as requiring a translation
- .debug events are ignored for coverage; if they use `_replace_msg`, a warning is shown in the report

Examples:

```bash
# Full, human-friendly report
nicestlog i18n check . --translation-dir translations -l en

# Machine-friendly list of missing keys
nicestlog i18n check src --translation-dir translations -l en --list-missing

# Strictly fail on missing keys
nicestlog i18n check . --translation-dir translations -l en --strict

# Also fail if extra (unused) keys exist
nicestlog i18n check . --translation-dir translations -l en --fail-on-extra
```


Use `_replace_msg` for human-readable messages while maintaining structured data. The formatter is partial, so it won't break if a key is missing.

```python
log.info(
    "user-login-success",
    _replace_msg="User {username} successfully logged in from {ip_address}",
    username=user.username,
    user_id=user.id,
    ip_address=request.remote_addr,
)
```

## Error Handling and Exception Logging

Always include `exc_info=True` when logging exceptions to get a full traceback.

```python
try:
    risky_operation()
except Exception as e:
    log.error(
        "operation-failed",
        operation="risky_operation",
        error=str(e),
        error_type=type(e).__name__,
        exc_info=True  # Includes full traceback
    )
    raise  # Re-raise if appropriate
```

## Testing Logging

Use `structlog.testing.LogCapture` to capture and assert log entries in your tests.

```python
import pytest
import structlog
from structlog.testing import LogCapture

def my_function():
    log = structlog.get_logger()
    log.info("testing-event", key="value")

def test_my_function_logging():
    # The LogCapture processor replaces other processors
    nicestlog.init_logging(verbose=True) # init is still needed
    log_capture = LogCapture()
    structlog.configure(processors=[log_capture])

    my_function()

    assert len(log_capture.entries) == 1
    assert log_capture.entries[0]["event"] == "testing-event"
    assert log_capture.entries[0]["key"] == "value"
```
