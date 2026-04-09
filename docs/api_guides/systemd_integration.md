# Systemd Integration Module

:::{admonition} Test Coverage: 42.4%
:class: warning

This module has moderate test coverage. Some features may not work as expected.
:::

The `stogger_systemd.systemd_integration` module provides advanced systemd journal integration, including structured field mapping, environment detection, and service file generation.

## Basic Usage

```python
import stogger

# Setup systemd logging
success = stogger.setup_systemd_logging(identifier="myapp")
```

## Functions

### setup_systemd_logging

Configure systemd journal logging integration.

```python
import stogger

success = stogger.setup_systemd_logging(
    identifier="myapp",      # SYSLOG_IDENTIFIER
    facility=None,            # SYSLOG_FACILITY
)
```

Returns `True` if systemd logging was configured, `False` otherwise.

### detect_systemd_environment

Detect if running under systemd and gather environment info.

```python
import stogger
from stogger_systemd.systemd_integration import detect_systemd_environment

info = detect_systemd_environment()
print(info["running_under_systemd"])
print(info["journal_available"])
print(info["service_name"])
print(info["invocation_id"])
```

### create_systemd_service_file

Generate a systemd service unit file with proper logging configuration.

```python
from stogger_systemd.systemd_integration import ServiceConfig, create_systemd_service_file

config = ServiceConfig(
    service_name="my-python-app",
    exec_command="/usr/bin/python3 /opt/myapp/main.py",
    user="myapp",
    working_directory="/opt/myapp",
    environment={"PYTHONPATH": "/opt/myapp", "LOG_LEVEL": "info"},
)

service_content = create_systemd_service_file(config)
```

### query_journal_logs

Query systemd journal for logs.

```python
from stogger_systemd.systemd_integration import query_journal_logs

entries = query_journal_logs(
    service_name="myapp",
    since="1 hour ago",
    level="error",
    lines=100,
)
```

## SystemdJournalHandler

A structlog processor that sends log events to the systemd journal with proper field mapping.

```python
from stogger_systemd.systemd_integration import SystemdJournalHandler

handler = SystemdJournalHandler(
    identifier="myapp",
    facility="daemon",
)

# Add to structlog processors
import structlog
structlog.configure(processors=[handler, ...])
```

Custom event fields are automatically prefixed with `STOGGER_` for journal compatibility.

## ServiceConfig

Configuration dataclass for systemd service generation.

```python
@dataclass
class ServiceConfig:
    service_name: str
    exec_command: str
    user: str | None = None
    working_directory: str | None = None
    environment: dict[str, str] | None = None
    restart_policy: str = "always"
```

## Installation

Requires the `systemd-python` package:

```bash
pip install systemd-python
```

## API Reference

```{autoapi} stogger_systemd.systemd_integration
:members:
```
