# Logging Patterns

Proven patterns and conventions for structured logging with stogger and structlog.

## Core Principles

1. Use dash-case event names as the primary message
2. Add structured keyword arguments for all context
3. Choose appropriate log levels
4. Use `log.exception()` in except blocks (not `log.error()` with `exc_info`)
5. Use `log.info()` for line-oriented user output instead of `print()` or `typer.echo()`

## Event-Style Logging

Structure log messages as events with dash-case names, not prose:

```python
log.debug("user-login-attempt", user_id=123, ip="192.168.1.1")
log.info("welcome-new-user", _replace_msg="Welcome {username}!", username=user.name)
log.error("package-validation-failed", package_name="hello", reason="invalid_version")
```

## Structured Data

Always provide context through keyword arguments — never via f-strings in the message:

```python
log.debug("package-processing-completed",
         package_name="hello",
         version="2.10.0",
         processing_time_ms=150,
         files_processed=42)
```

## Log Levels

| Level | When to Use | User Output |
|-------|-------------|-------------|
| `DEBUG` | Diagnostic info for developers, internal operations | **NEVER** use `_replace_msg` |
| `INFO` | Important business events, user-facing output | **SHOULD** use `_replace_msg` for user-oriented output |
| `WARNING` | Expected problems, unusual but non-failing conditions | Use `_replace_msg` for user warnings |
| `ERROR` | Error conditions that need attention | Use `_replace_msg` for user errors |
| `CRITICAL` | Severe errors requiring immediate action | Use `_replace_msg` for critical user messages |

```python
# DEBUG: internal details
log.debug("cache-lookup", key="user:123", hit=True, ttl=300)

# INFO: business events and user output
log.info("user-login", _replace_msg="User {user_id} logged in", user_id=123, session_id="sess_abc")

# WARNING: unexpected but non-critical
log.warning("rate-limit-approaching", _replace_msg="Rate limit approaching for user {user_id}", user_id=123, requests=95, limit=100)

# ERROR: failures
log.error("payment-gateway-timeout", _replace_msg="Payment gateway timeout for {gateway}", gateway="stripe", timeout_ms=5000)

# CRITICAL: system unusable
log.critical("database-unavailable", _replace_msg="Database unavailable after {attempts} attempts", attempts=3, last_error="connection refused")
```

## User Output with `_replace_msg`

stogger fuses user output with logging. Use `log.info()` instead of `print()` or `typer.echo()` for line-oriented user output. The event name provides structure; `_replace_msg` provides the human-readable sentence:

```python
log.info("package-installed",
         _replace_msg="Successfully installed {package_name} v{version} ({size_mb:.1f} MB)",
         package_name="hello",
         version="2.10.0",
         size_mb=15.7)
```

Benefits: single source of truth for user communication and diagnostics, structured data for analysis, consistent formatting, audit trail of user interactions.

## Exception Handling

Use `log.exception()` in except blocks. It is equivalent to `log.error()` with `exc_info=True` and automatically includes the full traceback. Do not pass `error=str(e)` — the exception context is already captured.

```python
try:
    process_package(package_data)
except ValidationError as e:
    log.exception("package-validation-failed",
                  package_name=package_data.get("name"))
    raise
```

### Alternative: `log.error` with `exc_info`

Use this only when you have a specific reason not to use `log.exception()`:

```python
try:
    do_work()
except Exception as e:
    log.error(
        "work-failed",
        operation="do_work",
        exc_info=True,
    )
```

Never use `exc_info` on `info`/`debug` levels.

## Correlation IDs

Track requests across services with correlation IDs:

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

## Common Patterns

### Function Tracing

```python
def process_package(package_name: str):
    log.info("package-processing-started", package_name=package_name)

    try:
        result = perform_processing(package_name)
        log.info("package-processing-completed",
                package_name=package_name,
                result_size=len(result))
        return result
    except Exception as e:
        log.exception("package-processing-failed", package_name=package_name)
        raise
```

### Timing Operations

```python
import time

def timed_operation():
    start = time.time()
    log.info("operation-started", operation="data_sync")

    result = perform_operation()

    duration = time.time() - start
    log.info("operation-completed",
            operation="data_sync",
            duration_ms=round(duration * 1000))

    return result
```

### CLI Command Logging

```python
def deploy_command(package_name: str, environment: str):
    log.info("deployment-started",
             _replace_msg="Deploying {package} to {env}...",
             package=package_name,
             env=environment)

    try:
        result = deploy_package(package_name, environment)
        log.info("deployment-completed",
                 _replace_msg="Successfully deployed {package} to {env}",
                 package=package_name,
                 env=environment,
                 deployment_id=result.id)
    except DeploymentError as e:
        log.exception("deployment-failed",
                      _replace_msg="Failed to deploy {package}: {error}",
                      package=package_name,
                      error=str(e))
        raise
```

### Progress Reporting

```python
def process_files(file_list: list[str]):
    total = len(file_list)
    log.info("batch-processing-started",
             _replace_msg="Processing {total} files...",
             total=total)

    for i, file_path in enumerate(file_list, 1):
        log.debug("file-processing-started", file_path=file_path, index=i)
        process_file(file_path)

        if i % 10 == 0 or i == total:
            log.info("batch-progress-update",
                     _replace_msg="Processed {current}/{total} files",
                     current=i,
                     total=total,
                     progress_percent=round(i/total*100))

    log.info("batch-processing-completed",
             _replace_msg="All {total} files processed successfully",
             total=total)
```

### Error Context

```python
def validate_config(config_path: Path):
    log.debug("config-validation-started", config_path=str(config_path))

    if not config_path.exists():
        log.error("config-file-missing",
                  _replace_msg="Configuration file not found: {path}",
                  config_path=str(config_path))
        raise FileNotFoundError(f"Config file missing: {config_path}")

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        log.exception("config-parse-failed",
                      _replace_msg="Invalid YAML in config file: {error}",
                      config_path=str(config_path),
                      error=str(e))
        raise

    log.info("config-validation-completed",
             _replace_msg="Configuration validated successfully",
             config_path=str(config_path),
             config_keys=list(config.keys()))

    return config
```

## Security

### Avoid Logging Sensitive Data

```python
log.info("user-authenticated", user_id=123, email_domain="example.com")
```

Never log passwords, tokens, or raw PII. Enable PII scrubbing via configuration (`enable_pii_scrubbing=True`).

## Performance

### Batch Logging in Loops

```python
log.info("batch-processing-started", item_count=len(large_list))
# ... process items ...
log.info("batch-processing-completed", processed_count=processed)
```

### Log Sampling for High-Volume Applications

```python
import random

if random.random() < 0.1:  # 10% sampling
    log.debug("high-frequency-event", event_data=data)
```

Avoid chatty `info` logs in tight loops. Use `debug`, sample, or aggregate instead.

## Monitoring-Friendly Logging

Design logs to be easily parsed by monitoring systems:

```python
log.info("api-response",
         endpoint="/api/users",
         method="GET",
         status_code=200,
         response_time_ms=45,
         cache_hit=True)
```

## Consistent Field Names

Prefer these field names for consistency:

- IDs: `user_id`, `request_id`, `correlation_id`
- Timing: `duration_ms`
- HTTP: `method`, `path`, `status_code`
- Generic: `operation`, `component`

Keep the cardinality low — avoid unbounded label values.

## Do / Don't

Do:

```python
log.info("order-created", _replace_msg="Order {order_id} created for user {user_id}", order_id=oid, user_id=uid, total_cents=total)
```

Don't:

```python
log.info(f"order {oid} by user {uid} created with total {total}")
```
