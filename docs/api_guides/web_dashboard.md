# Web Dashboard Module

:::{warning} Limited Test Coverage (21.8%)

This module has limited test coverage. Use at your own risk. Contributions to improve test coverage are welcome.
:::

The `nicestlog.web_dashboard` module provides a simple Flask + HTMX web dashboard for live log viewing.

## Basic Usage

```python
import nicestlog

# Setup web logging
nicestlog.setup_web_logging(host="0.0.0.0", port=8080)

# The dashboard captures all structlog events
import structlog
log = structlog.get_logger()
log.info("user-login", user_id=123)  # Visible in dashboard
```

## Functions

### setup_web_logging

Setup the web dashboard with optional Flask server.

```python
import nicestlog

nicestlog.setup_web_logging(
    host="0.0.0.0",     # Bind address
    port=8080,           # Port
    debug=False,         # Flask debug mode
    start_server=True,   # Auto-start the server
)
```

### run_dashboard

Run the web dashboard server.

```python
import nicestlog
nicestlog.run_dashboard(host="0.0.0.0", port=8080)
```

### get_log_stats

Get statistics about captured logs.

```python
import nicestlog
stats = nicestlog.get_log_stats()
```

## WebLogHandler

A structlog processor that captures log events for web display.

```python
from nicestlog.web_dashboard import WebLogHandler

handler = WebLogHandler()
# Add to structlog processors
```

## Architecture

The dashboard uses:
- Flask for the HTTP server
- HTMX for live updates (no WebSocket needed)
- In-memory buffer for recent logs (max 500 entries)
- Thread-safe log capture

## Installation

Requires Flask:

```bash
pip install nicestlog[web]
```

## API Reference

```{autoapi} nicestlog.web_dashboard
:members:
```
