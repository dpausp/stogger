# Nicestlog Best Practices

> 📖 **See also**: [Logging Conventions](logging_conventions.md) for detailed structlog/stogger coding standards and patterns.

This guide covers proven patterns and best practices for effective logging with stogger.

## Core Principles

### 1. Use Event-Style Messages

Structure your log messages as events rather than prose:

```python
log.info("user-registration-completed", _replace_msg="User registration completed for user {user_id}", user_id=123, email="user@example.com")
```

### 2. Include Structured Data

Always provide context through keyword arguments:

```python
log.error("api-request-failed",
          endpoint="/api/users",
          method="POST",
          status_code=500,
          response_time_ms=1250,
          user_id=123)
```

### 3. Use Consistent Event IDs

Adopt a consistent naming convention for event IDs:

```python
log.info("order-payment-processed", _replace_msg="Order payment processed")
log.warning("inventory-low-stock")
log.error("database-connection-timeout")
```

## Logging Levels

### When to Use Each Level

```python
# DEBUG: Detailed diagnostic information
log.debug("cache-lookup", key="user:123", hit=True, ttl=300)

# INFO: General operational events
log.info("user-login", _replace_msg="User {user_id} logged in", user_id=123, session_id="sess_abc")

# WARNING: Something unexpected but not critical
log.warning("rate-limit-approaching", _replace_msg="Rate limit approaching for user {user_id}", user_id=123, requests=95, limit=100)

# ERROR: Error conditions that need attention
log.error("payment-gateway-timeout", _replace_msg="Payment gateway timeout for {gateway}", gateway="stripe", timeout_ms=5000)

# CRITICAL: Serious errors requiring immediate action
log.critical("database-unavailable", _replace_msg="Database unavailable after {attempts} attempts", attempts=3, last_error="connection refused")
```

## Performance Considerations

### Lazy Evaluation

Use structured data instead of string formatting for better performance:

```python
log.debug("query-executed", sql=query, params=params, duration_ms=duration)
```

## Security Best Practices

### Avoid Logging Sensitive Data

```python
log.info("user-authenticated", user_id=123, email_domain="example.com")
```

### Use PII Scrubbing

stogger provides built-in PII scrubbing capabilities:

```python
from stogger import PIIScrubber

scrubber = PIIScrubber()
log.info("user-data-processed", **scrubber.scrub(user_data))
```

## Error Handling

### Include Exception Context

```python
try:
    process_payment(order_id)
except PaymentError:
    log.exception(
        "payment-processing-failed",
        order_id=order_id,
    )
```

### Correlation IDs

Use correlation IDs to track requests across services:

```python
import uuid

correlation_id = str(uuid.uuid4())

log.info("request-started", 
         correlation_id=correlation_id,
         endpoint="/api/orders",
         method="POST")

# ... processing ...

log.info("request-completed",
         correlation_id=correlation_id,
         status_code=201,
         processing_time_ms=150)
```

## Testing and Monitoring

### Structured Logs for Monitoring

Design your logs to be easily parsed by monitoring systems:

```python
# Metrics-friendly logging
log.info("api-response",
         endpoint="/api/users",
         method="GET",
         status_code=200,
         response_time_ms=45,
         cache_hit=True)
```

### Log Sampling

For high-volume applications, consider log sampling:

```python
import random

if random.random() < 0.1:  # 10% sampling
    log.debug("high-frequency-event", event_data=data)
```

## Integration Patterns

### With Web Frameworks

```python
# Flask example
from flask import request, g
import stogger, structlog

stogger.init_logging(verbose=True)
log = structlog.get_logger()

@app.before_request
def before_request():
    g.request_id = str(uuid.uuid4())
    log.info("request-started",
             request_id=g.request_id,
             method=request.method,
             path=request.path)

@app.after_request
def after_request(response):
    log.info("request-completed",
             request_id=g.request_id,
             status_code=response.status_code)
    return response
```

### With Background Tasks

```python
# Celery example
from celery import Celery
import stogger

log = stogger.get_logger()

@app.task
def process_order(order_id):
    log.info("task-started", task="process_order", order_id=order_id)
    
    try:
        # Process order
        result = do_processing(order_id)
        log.info("task-completed", task="process_order", order_id=order_id, result=result)
        return result
    except Exception as e:
        log.error("task-failed", task="process_order", order_id=order_id, error=str(e))
        raise
```

## Best Practices

### 1. Use Structured Data Instead of String Concatenation

```python
log.info("user-login", user_id=user_id)
```

### 2. Batch Logging in Loops

```python
log.info("batch-processing-started", item_count=len(large_list))
# ... process items ...
log.info("batch-processing-completed", processed_count=processed)
```

### 3. Use Appropriate Log Levels

```python
log.info("user-login-successful", user_id=123)
```

### 4. Use Direct Structured Logging

```python
log.info("user-action", user_id=123, action="login", ip="192.168.1.100")
```

Avoid wrapper functions that obscure stack traces and limit structured data.

## Summary

Good logging practices improve observability, debugging, and maintenance. Follow these patterns for better structured logs.