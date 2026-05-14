# Reference

Quick lookup for log levels, output keys, decorators, and field name conventions.

## Log Levels

| Level | When to use | `_replace_msg` |
|-------|-------------|----------------|
| `DEBUG` | Diagnostic info, internal operations | **Never** |
| `INFO` | Business events, user-facing output | **Should** for user-oriented output |
| `WARNING` | Unusual but non-failing conditions | Yes |
| `ERROR` | Failures needing attention | Yes |
| `CRITICAL` | System unusable, operator action required | Yes |

```python
log.debug("cache-lookup", key="user:123", hit=True, ttl=300)
log.info("user-login", _replace_msg="User {user_id} logged in", user_id=123)
log.warning("rate-limit-approaching", _replace_msg="Rate limit approaching for user {user_id}", user_id=123)
log.error("payment-gateway-timeout", _replace_msg="Payment gateway timeout for {gateway}", gateway="stripe")
log.critical("database-unavailable", _replace_msg="Database unavailable after {attempts} attempts", attempts=3)
```

## Decorators

Import from the top-level package:

```python
from stogger import log_call, log_result, log_operation, log_scope
```

All decorators support sync and async functions.

### @log_call — Entry Logging

Logs function invocation with resolved arguments. Replaces manual `log.info("called", func=..., args={...})`.

```python
@log_call
def process_package(package_name: str):
    ...
    # Logs: {"event": "called", "func": "mymodule.process_package",
    #        "args": {"package_name": "hello"}}
```

### @log_result — Exit Logging with Timing

Logs return value and duration on success, exception info on failure.

```python
@log_result
def timed_operation():
    return perform_operation()
    # Logs: {"event": "returned", "func": "mymodule.timed_operation",
    #        "result": ..., "duration_ms": 12.3}
```

On exception, logs `{"event": "failed", "exc_type": "ValueError", "exc_msg": "...", "duration_ms": ...}` and re-raises.

### @log_operation — Full Audit Logging

Combines entry and exit logging: arguments, return value, and duration in one event.

```python
@log_operation(include_args=["query"], exclude_args=["password"])
def authenticate(query: str, password: str) -> bool:
    ...
    # Logs: {"event": "operation", "func": "mymodule.authenticate",
    #        "args": {"query": "admin"}, "result": true, "duration_ms": 15.3}
```

Use `include_args` to whitelist or `exclude_args` to blacklist argument names. Both strip `self` and `cls` automatically.

### log_scope() — Scoped Context Logging

Context manager for logging a named scope with structured fields. Use for transactions, migrations, or any logical unit of work.

```python
with log_scope("db_transaction", table="users") as scope:
    insert(user)
    scope.add_fields(rows_inserted=1)
    # Exit: {"event": "scope-end", "scope": "db_transaction",
    #   "table": "users", "rows_inserted": 1, "duration_ms": 45.2}
```

`add_fields()` accumulates fields during the scope. On exception, logs `{"event": "scope-failed", ...}` and re-raises. Works with `async with`.

## Output Keys

Use these keys to render tool output, command results, and tracebacks:

| Key | Prefix | DIM | ANSI behavior |
|-----|--------|-----|---------------|
| `cmd_output_line` | `> ` | Yes | Stripped via DIM wrapping |
| `_output` | empty | No | Stripped via `write()` closure |
| `_raw_output` | configurable via `_raw_output_prefix` | No | **Preserved** in console, stripped in file |
| `_raw_output_prefix` | used as prefix label | — | Sets prefix for `_raw_output` |
| `stdout` | `out` | Yes | Stripped via DIM wrapping |
| `stderr` | `err` | Yes | Stripped via DIM wrapping |
| `stack` | `stack` | No | Stripped via `write()` closure |
| `exception_traceback` | `exception` | No | Stripped via `write()` closure |

### Raw Output with ANSI Passthrough

Use `_raw_output` for tool output containing ANSI color codes. Console preserves colors; log file gets stripped output:

```python
log.warning(
    "component-type-errors",
    _replace_msg="{component}: {count} type error(s)",
    component=component_name,
    count=result.output.count("error:"),
    _raw_output_prefix="ty",
    _raw_output=result.output.strip(),
)
```

## Field Name Conventions

Prefer these names for consistency across logs:

- IDs: `user_id`, `request_id`, `correlation_id`
- Timing: `duration_ms`
- HTTP: `method`, `path`, `status_code`
- Generic: `operation`, `component`

Keep cardinality low — avoid unbounded label values.
