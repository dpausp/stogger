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

Note: The high-level configure API is not finalized; prefer init_logging with kwargs.

stogger can be configured through various methods:

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
- Set up [Systemd Journal Integration](systemd.md) for services running under systemd
- Set up [PostgreSQL Integration](postgres.md) for queryable persistent logs
- Read [Testing with stogger](testing.md) to test your log output
- Explore [Advanced Features](../features/advanced_assistant.md) for code transformation
- Check out the [API Reference](../api/index) for detailed documentation