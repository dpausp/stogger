# Getting Started with nicestlog

Welcome to nicestlog! This guide will help you get up and running quickly with our sophisticated structured logging system.

## Installation

Install nicestlog using pip:

```bash
pip install nicestlog
```

## Basic Usage

Here's how to start logging with nicestlog:

```python
import nicestlog
import structlog

# Initialize logging (console by default)
nicestlog.init_logging(verbose=True)

# Get a logger instance
log = structlog.get_logger()

# Log with structured data
log.info("user-login", _replace_msg="User {username} logged in", user_id=123, username="alice", ip="192.168.1.1")
log.warning("rate-limit-exceeded", _replace_msg="Rate limit exceeded for user {user_id}", user_id=123, attempts=5, limit=3)
log.error("database-connection-failed", _replace_msg="Database connection failed to {host}", host="db.example.com", timeout=30)
```

## Key Concepts

### Event-Style Logging

nicestlog promotes event-style logging where each log entry represents a specific event:

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

nicestlog can be configured through various methods:

```python
import nicestlog

# Configure with custom settings
# Prefer init_logging; configure is subject to change.
nicestlog.init_logging(
    level="INFO",
    format="json",
    include_timestamp=True
)
```

## Next Steps

- Learn about [Best Practices](best_practices.md) for effective logging
- Explore [Advanced Features](../features/advanced_assistant.md) for code transformation
- Check out the [API Reference](../development/api_reference) for detailed documentation