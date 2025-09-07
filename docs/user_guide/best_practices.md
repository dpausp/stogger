# Nicestlog Best Practices

> 📖 **See also**: [Logging Conventions](logging_conventions.md) for detailed structlog/nicestlog coding standards and patterns.

This guide covers proven patterns and best practices for effective logging with nicestlog.

## Core Principles

### 1. Use Event-Style Messages

Structure your log messages as events rather than prose:

```python
# ✅ Good: Event-style
log.info("user-registration-completed", _replace_msg="User registration completed for user {user_id}", user_id=123, email="user@example.com")

# ❌ Avoid: Prose-style
log.info("User with ID 123 has completed registration")
```

### 2. Include Structured Data

Always provide context through keyword arguments:

```python
# ✅ Good: Rich context
log.error("api-request-failed",
          endpoint="/api/users",
          method="POST", 
          status_code=500,
          response_time_ms=1250,
          user_id=123)

# ❌ Avoid: Missing context
log.error("API request failed")
```

### 3. Use Consistent Event IDs

Adopt a consistent naming convention for event IDs:

```python
# ✅ Good: dash-case convention
log.info("order-payment-processed", _replace_msg="Order payment processed")
log.warning("inventory-low-stock")
log.error("database-connection-timeout")

# ❌ Avoid: Inconsistent naming
log.info("orderPaymentProcessed")  # camelCase
log.warning("inventory_low_stock")  # snake_case
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
# ✅ Good: Lazy evaluation
log.debug("query-executed", sql=query, params=params, duration_ms=duration)

# ❌ Avoid: Eager string formatting
log.debug(f"Executed query: {query} with params {params} in {duration}ms")
```

### Conditional Logging

For expensive operations, use conditional logging:

```python
if log.isEnabledFor(logging.DEBUG):
    expensive_data = compute_expensive_debug_info()
    log.debug("expensive-operation-completed", data=expensive_data)
```

## Security Best Practices

### Avoid Logging Sensitive Data

```python
# ✅ Good: Mask sensitive data
log.info("user-authenticated", user_id=123, email_domain="example.com")

# ❌ Avoid: Logging sensitive information
log.info("user-authenticated", password="secret123", api_key="sk_live_...")
```

### Use PII Scrubbing

nicestlog provides built-in PII scrubbing capabilities:

```python
from nicestlog import PIIScrubber

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
import nicestlog, structlog

nicestlog.init_logging(verbose=True)
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
import nicestlog

log = nicestlog.get_logger()

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

## Common Anti-Patterns to Avoid

### 1. String Concatenation in Logs

```python
# ❌ Avoid
log.info("User " + str(user_id) + " logged in")

# ✅ Better
log.info("user-login", user_id=user_id)
```

### 2. Logging in Loops Without Throttling

```python
# ❌ Avoid: Can flood logs
for item in large_list:
    log.debug("processing-item", item_id=item.id)

# ✅ Better: Batch logging
log.info("batch-processing-started", item_count=len(large_list))
# ... process items ...
log.info("batch-processing-completed", processed_count=processed)
```

### 3. Inconsistent Log Levels

```python
# ❌ Avoid: Wrong level for content
log.error("User logged in successfully")  # Should be INFO

# ✅ Better: Appropriate level
log.info("user-login-successful", user_id=123)
```

### 4. Log Wrapper Functions

```python
# ❌ Avoid: Wrapper functions hide source location
def log_debug(message):
    print(f"DEBUG: {message}")

def write_info(msg):
    logging.info(msg)

def emit_warning(text):
    logger.warning(text)

def log_user_action(user_id, action):
    log.info(f"User {user_id} performed {action}")

# Usage creates problems
log_debug("Starting application")  # Where did this actually happen?
write_info("Processing data")      # Hard to trace back to source
emit_warning("Low disk space")     # Lost structured data opportunity
log_user_action(123, "login")      # No flexibility for additional context

# ✅ Better: Direct logging with structure
import structlog
log = structlog.get_logger()

# Direct calls with proper structure
log.debug("application-starting", component="main", version="1.2.3")
log.info("data-processing", status="started", batch_id="batch_001")
log.warning("disk-space-low", available_gb=2.1, threshold_gb=5.0)
log.info("user-action", user_id=123, action="login", ip="192.168.1.100")
```

**Why wrapper functions are problematic:**
- **Hidden source location**: Stack traces show the wrapper, not the actual call site
- **Reduced flexibility**: Wrappers limit structured data you can include
- **Maintenance overhead**: Extra functions to test and maintain
- **Inconsistent patterns**: Different developers create different wrapper styles
- **Lost debugging context**: The actual call site information is obscured

**Detection**: Use `nicestlog check .` to automatically detect wrapper anti-patterns in structlog-based codebases. For legacy projects without structlog, use `nicestlog migrate .` to analyze and migrate to structured logging.

## Summary

Following these best practices will help you:

- Create more maintainable and searchable logs
- Improve application observability
- Reduce debugging time
- Enhance security posture
- Build better monitoring and alerting

Remember: Good logging is an investment in your application's maintainability and operational excellence!