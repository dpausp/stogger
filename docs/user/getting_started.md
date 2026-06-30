# Getting Started with stogger

stogger provides structured logging on top of structlog — console, file, and systemd journal targets in one call.

## Installation

Install stogger using uv:

```bash
uv add stogger
```

## Basic Usage

Here's how to start logging with stogger:

```python
import stogger
import structlog

# Initialize logging (console by default)
stogger.init_logging(verbose=True)

# Get a logger instance
log = structlog.get_logger()

# Log with structured data
log.info("user-login", _replace_msg="User {username} logged in", user_id=123, username="alice", ip="192.168.1.1")
log.warning("rate-limit-exceeded", _replace_msg="Rate limit exceeded for user {user_id}", user_id=123, attempts=5, limit=3)
log.error("database-connection-failed", _replace_msg="Database connection failed to {host}", host="db.example.com", timeout=30)
```

## Two-Phase Initialization (CLI Apps and Services)

The "Basic Usage" example calls `init_logging()` at module level, which works for scripts.
CLI apps and long-running services need a different approach: modules get imported before
CLI flags are parsed, so `init_logging()` can't be called at import time — you don't know
the log level, logdir, or other settings yet.

stogger solves this with two functions:

### Phase 1: Bootstrap at Import

Call `init_early_logging()` in your package's `__init__.py`. It installs a lightweight
pipeline (timestamp, level, console renderer) so that import-time log messages appear
formatted instead of as raw dicts. It's a no-op if structlog is already configured, so it's
safe to call in tests too.

```python
# src/myapp/__init__.py
from stogger import init_early_logging

init_early_logging()
```

### Phase 2: Full Pipeline After Config

Call `init_logging()` **exactly once**, **unconditionally**, at the earliest point where
all parameters are known. That's typically the Typer callback — after flags are parsed,
before any command runs. It replaces the early pipeline with the full one: exception
formatting, PID, caller info, file logging, systemd journal, multiple render targets.

**Wrong** — gating `init_logging` behind a flag means the early pipeline stays active
forever when the flag is off:

```python
# src/myapp/cli.py — BROKEN
from stogger import init_logging
import typer

app = typer.Typer()

@app.callback()
def main(verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False):
    if verbose:                          # ← WRONG
        init_logging(verbose=True)       # ← no init_logging() when verbose=False
```

Without `-v`, `log.exception()` produces no traceback, no PID, no caller info — the
early pipeline was never replaced.

**Right** — always call `init_logging()`, pass the flags as parameters:

```python
# src/myapp/cli.py — CORRECT
from stogger import init_logging
import typer

app = typer.Typer()

@app.callback()
def main(verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False):
    init_logging(verbose=verbose)       # ← ALWAYS, with or without -v
```

`init_logging(verbose=False)` is the default production setup (info level, console +
file + journal). `init_logging(verbose=True)` adds debug level. Both get the full
pipeline. The flag controls *verbosity*, not *whether logging is configured*.

### What the Early Pipeline Does NOT Provide

The early pipeline is intentionally minimal — a bootstrap, not a replacement. Without
calling `init_logging()`, you get:

- **No exception tracebacks** — `log.exception()` behaves like `log.error()`, no stack trace
- **No PID, no caller info** — missing context in every log entry
- **No file logging, no systemd journal** — only console output
- **No `_replace_msg` formatting** — event names appear raw

If you see `log.exception()` without a traceback, the most likely cause is a missing
`init_logging()` call — the early pipeline was never replaced.

## Key Concepts

### Event-Style Logging

stogger promotes event-style logging where each log entry represents a specific event:

```python
log.info("order-created", _replace_msg="Order {order_id} created for customer {customer_id}", order_id=12345, customer_id=67890, amount=99.99)
```

### Structured Data

Always include relevant context as keyword arguments:

```python
log.info("payment-processed", 
         _replace_msg="Payment {payment_id} processed for {amount} {currency}",
         payment_id="pay_123",
         amount=49.99,
         currency="USD",
         gateway="stripe",
         processing_time_ms=245)
```

## Configuration

### TOML Configuration

For persistent settings, add a ``[tool.stogger]`` section to your ``pyproject.toml``:

```toml
[tool.stogger]
verbose = true
log_format = "simple"
```

See the feature-specific guides (systemd, postgres) for detailed configuration options.

### Environment Variable Overrides

Override any ``[tool.stogger]`` setting via ``STOGGER_<KEY>`` environment variables.
Priority: **environment > kwargs > pyproject.toml**.

```bash
STOGGER_LOGDIR=/var/log/myapp
STOGGER_VERBOSE=true
STOGGER_SYSLOG_IDENTIFIER=myapp
STOGGER_LOG_TO_CONSOLE=false
```

Bool values accept ``1``/``true``/``yes`` (True) and ``0``/``false``/``no`` (False).
Invalid values are silently ignored.

Available variables:

| Variable | Config Key | Type |
|----------|-----------|------|
| ``STOGGER_VERBOSE`` | ``verbose`` | bool |
| ``STOGGER_LOGDIR`` | ``logdir`` | path |
| ``STOGGER_LOG_CMD_OUTPUT`` | ``log_cmd_output`` | bool |
| ``STOGGER_LOG_TO_CONSOLE`` | ``log_to_console`` | bool |
| ``STOGGER_SYSLOG_IDENTIFIER`` | ``syslog_identifier`` | str |
| ``STOGGER_SHOW_CALLER_INFO`` | ``show_caller_info`` | bool |
| ``STOGGER_TRANSLATION_DIR`` | ``translation_dir`` | path |
| ``STOGGER_LANGUAGE`` | ``language`` | str |
| ``STOGGER_LOG_FORMAT`` | ``log_format`` | str |
| ``STOGGER_ASYNC_LOGGING`` | ``async_logging`` | bool |
| ``STOGGER_SYSTEMD`` | ``systemd`` | ``"auto"``, ``"required"``, ``"off"`` |
| ``STOGGER_SYSTEMD_FACILITY`` | ``systemd_facility`` | str |
| ``STOGGER_ENABLE_POSTGRES`` | ``enable_postgres`` | bool |
| ``STOGGER_POSTGRES_DSN`` | ``postgres_dsn`` | str |
| ``STOGGER_POSTGRES_TABLE`` | ``postgres_table`` | str |
| ``STOGGER_SRC_DIR`` | ``src_dir`` | str |
| ``STOGGER_LOG_ROTATION`` | ``log_rotation`` | str (``"size"`` or ``"none"``) |
| ``STOGGER_LOG_MAX_BYTES`` | ``log_max_bytes`` | int |
| ``STOGGER_LOG_BACKUP_COUNT`` | ``log_backup_count`` | int |

Useful for CI/CD, containers, and shared config files where editing ``pyproject.toml`` is impractical.

### Python API

stogger can also be configured programmatically:

```python
import stogger
from stogger import SystemdMode

# Configure with custom settings
stogger.init_logging(
    verbose=True,
    logdir="logs/",
    syslog_identifier="my-app",
    systemd=SystemdMode.AUTO,
)
```

For long-running applications (daemons, services), enable file rotation to cap log
file growth — see [File Rotation](file_rotation.md) for details:

```python
stogger.init_logging(
    logdir="logs/",
    syslog_identifier="my-app",
    log_rotation="size",
    log_max_bytes=10_000_000,
    log_backup_count=5,
)
```

## Next Steps

- Learn about [Logging Patterns](logging_patterns.md) for effective logging
- Browse the [Output Gallery](output_gallery.md) to see what stogger output looks like
- Set up [Systemd Journal Integration](systemd.md) for services running under systemd
- Set up [PostgreSQL Integration](postgres.md) for queryable persistent logs
- Configure [File Rotation](file_rotation.md) for long-running daemons and services
- Read [Testing with stogger](testing.md) to test your log output
- Read the source — agents read code, not generated docs ;)