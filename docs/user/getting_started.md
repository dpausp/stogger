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
| ``STOGGER_ENABLE_SYSTEMD`` | ``enable_systemd`` | bool |
| ``STOGGER_SYSTEMD_FACILITY`` | ``systemd_facility`` | str |
| ``STOGGER_ENABLE_POSTGRES`` | ``enable_postgres`` | bool |
| ``STOGGER_POSTGRES_DSN`` | ``postgres_dsn`` | str |
| ``STOGGER_POSTGRES_TABLE`` | ``postgres_table`` | str |
| ``STOGGER_SRC_DIR`` | ``src_dir`` | str |

Useful for CI/CD, containers, and shared config files where editing ``pyproject.toml`` is impractical.

### Python API

stogger can also be configured programmatically:

```python
import stogger

# Configure with custom settings
# Prefer init_logging; configure is subject to change.
stogger.init_logging(
    verbose=True,
    logdir="logs/",
    syslog_identifier="my-app"
)
```

## Next Steps

- Learn about [Logging Patterns](logging_patterns.md) for effective logging
- Browse the [Output Gallery](output_gallery.md) to see what stogger output looks like
- Set up [Systemd Journal Integration](systemd.md) for services running under systemd
- Set up [PostgreSQL Integration](postgres.md) for queryable persistent logs
- Read [Testing with stogger](testing.md) to test your log output
- Read the source — agents read code, not generated docs ;)