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
log.info("user-login", user_id=123, username="alice", ip="192.168.1.1")
log.warning("rate-limit-exceeded", user_id=123, attempts=5, limit=3)
log.error("database-connection-failed", host="db.example.com", timeout=30)
```

## Key Concepts

### Event-Style Logging

nicestlog promotes event-style logging where each log entry represents a specific event:

```python
# ✅ Good: Event-style with structured data
log.info("order-created", order_id=12345, customer_id=67890, amount=99.99)

# ❌ Avoid: String formatting without structure
log.info(f"Order {order_id} created for customer {customer_id}")
```

### Structured Data

Always include relevant context as keyword arguments:

```python
log.info("payment-processed", 
         payment_id="pay_123",
         amount=49.99,
         currency="USD",
         gateway="stripe",
         processing_time_ms=245)
```

## Configuration

nicestlog can be configured through various methods:

```python
import nicestlog

# Configure with custom settings
nicestlog.configure(
    level="INFO",
    format="json",
    include_timestamp=True
)
```

## Next Steps

- Learn about [Best Practices](best_practices.md) for effective logging
- Explore [Advanced Features](../features/advanced_assistant.md) for code transformation
- Check out the [API Reference](../development/api_reference.md) for detailed documentation