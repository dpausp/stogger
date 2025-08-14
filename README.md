# nicestlog

A sophisticated logging system built on top of [structlog](https://www.structlog.org/) that provides multi-target logging with different renderers for console output, systemd journal, and file logging.

## Features

- **Multi-target logging**: Console, file, and systemd journal simultaneously
- **Optimistic error handling**: Logging failures don't crash your application
- **Rich console formatting**: Colored output with structured data display
- **Structured logging**: Machine-parseable logs for monitoring and analysis
- **Command output logging**: Separate logging for external command output
- **Template-based messages**: Human-readable messages with graceful fallbacks
- **Systemd integration**: Automatic detection and proper journal integration
- **Development-friendly**: Rich debugging information when needed

## Installation

```bash
pip install nicestlog
```

## Quick Start

### Basic Console Logging

```python
import nicestlog
import structlog

# Initialize logging for console output
nicestlog.init_logging(verbose=True, syslog_identifier="myapp")

# Get a logger instance
log = structlog.get_logger()

log.info(
    "application-started",
    _replace_msg="Application {name} started successfully",
    name="myapp",
    version="1.0.0"
)
```

### File + Console Logging

```python
import nicestlog
import structlog
from pathlib import Path

# Setup with file and console logging
nicestlog.init_logging(
    logdir=Path("/var/log/myapp"),
    verbose=True,
    syslog_identifier="myapp"
)

log = structlog.get_logger()
log.info("Starting application", component="main")
```

For more examples and best practices, see the [documentation](docs/best_practices.md).

## License

MIT License
