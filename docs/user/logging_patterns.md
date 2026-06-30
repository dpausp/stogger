# Logging Patterns

Common patterns for structured logging with stogger.
For log level details, decorator API, and output key reference, see
[Reference](reference.md).

## User Output with `_replace_msg`

Use `log.info()` instead of `print()` or `typer.echo()` for line-oriented user output.
The event name provides structure; `_replace_msg` provides the human-readable sentence:

```python
log.info("package-installed",
         _replace_msg="Successfully installed {package_name} v{version} ({size_mb:.1f} MB)",
         package_name="hello",
         version="2.10.0",
         size_mb=15.7)
```

Single source of truth for user communication and diagnostics — structured data for
analysis, formatted text for humans, audit trail of user interactions.

## Output Rendering

stogger renders output to two targets: **console** (with ANSI colors) and **file**
(stripped).
Use output keys to embed command results, tool output, or tracebacks in a log
event. The `write()` closure handles the split automatically — console gets raw ANSI,
file gets stripped text.

| Key | Prefix label | DIM | ANSI behavior |
| --- | --- | --- | --- |
| `cmd_output_line` | `> ` | Yes | Stripped via DIM wrapping |
| `_output` | *(none)* | No | Stripped via `write()` closure |
| `_raw_output` | configurable via `_raw_output_prefix` | No | **Preserved** in console, stripped in file |
| `_raw_output_prefix` | Sets prefix for `_raw_output` | — | *(metadata only)* |
| `stdout` | `out` | Yes | Stripped via DIM wrapping |
| `stderr` | `err` | No | Stripped via `write()` closure |
| `stack` | `stack` | No | Stripped via `write()` closure |
| `exception_traceback` | `exception` | No | Stripped via `write()` closure |

The `_` prefix marks internal keys consumed by dedicated render stages — they never appear in the fallback `key=value` body and cannot be referenced from `_replace_msg` format strings. Don't use `_` for your own fields; see [Reference: Underscore Prefix Convention](reference.md#underscore-prefix-convention).

### Tool Output with ANSI Colors

Use `_raw_output` for tool output containing ANSI codes (e.g.,
`ty check --color always`, `pytest --color yes`). Set `_raw_output_prefix` to label the
block:

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

Without `_raw_output_prefix`, the output renders without a label.

### Command Invocation

Use `cmd_output_line` for a single command line.
Renders dimmed with a `>` prefix:

```python
log.info("deploy-command", cmd_output_line="rsync -avz ./dist/ server:/var/www/")
```

### Captured Process Output

Use `stdout` and `stderr` for subprocess output.
Both render dimmed with `out:` / `err:` prefix labels:

```python
log.error(
    "build-failed",
    _replace_msg="Build failed for {package}",
    package=package_name,
    stderr=process.stderr,
)
```

### Stack Traces and Exceptions

Use `stack` for a formatted stack trace and `exception_traceback` for the exception
chain. When both are present, they are separated by a divider line:

```python
log.error("unhandled-exception", stack=formatted_stack, exception_traceback=traceback_str)
```

Usually you don’t set these manually — `log.exception()` captures the traceback
automatically.

### Generic Multi-line Output

Use `_output` for arbitrary multi-line content that doesn’t fit the other keys.
No prefix label, no DIM wrapping:

```python
log.info("diff-result", _output=diff_text)
```

## Exception Handling

Use `log.exception()` in except blocks.
It is equivalent to `log.error()` with `exc_info=True` and automatically includes the
full traceback. Do not pass `error=str(e)` — the exception context is already captured.

```python
try:
    process_package(package_data)
except ValidationError as e:
    log.exception("package-validation-failed",
                  package_name=package_data.get("name"))
    raise
```

Use `log.error` with `exc_info=True` only when you have a specific reason not to use
`log.exception()`. Never use `exc_info` on `info`/`debug` levels.

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

Or use the [`@log_call`](reference.md#log_call--entry-logging) decorator instead — see [Decorators](#decorators) for the full pattern guide.

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

Or use the [`@log_result`](reference.md#log_result--exit-logging-with-timing) decorator
instead — see [Decorators](#decorators) for the full pattern guide.

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

## Decorators

Automate common logging patterns with decorators instead of manual
`log.info()` calls.
All decorators support sync and async functions and are imported from
the top-level package:

```python
from stogger import log_call, log_result, log_operation, log_scope
```

### Entry Logging with `@log_call`

Replace manual "function started" logging:

```python
from stogger import log_call

@log_call
def process_package(package_name: str):
    # Automatically logs: {"event": "called", "func": "mymodule.process_package",
    #                      "package_name": "hello"}
    ...
```

Filter sensitive arguments:

```python
@log_call(exclude_args=["password", "token"])
def authenticate(username: str, password: str, token: str):
    # Logs: {"event": "called", "func": "...", "username": "alice"}
    ...
```

### Exit Logging with `@log_result`

Replace manual "operation completed" + timing:

```python
from stogger import log_result

@log_result
def compute_hash(data: bytes) -> str:
    ...
    # On success: {"event": "returned", "func": "mymodule.compute_hash",
    #              "result": "abc123", "duration_ms": 12.5}
    # On failure: {"event": "failed", "func": "mymodule.compute_hash",
    #              "exc_type": "ValueError", "exc_msg": "...", "duration_ms": 5.1}
```

### Full Audit with `@log_operation`

Combine entry and exit logging — arguments, result, and timing in a
single event:

```python
from stogger import log_operation

@log_operation(exclude_args=["api_key"])
def fetch_data(endpoint: str, api_key: str) -> dict:
    ...
    # On success: {"event": "operation", "func": "mymodule.fetch_data",
    #              "endpoint": "/users", "result": {...}, "duration_ms": 45.2}
```

When the function raises, logs `{"event": "failed", ...}` with exception
info and re-raises.

### Scoped Logging with `log_scope()`

Context manager for code blocks that aren't functions — transactions,
migrations, multi-step operations:

```python
from stogger import log_scope

with log_scope("db_transaction", table="users") as scope:
    insert(user)
    scope.add_fields(rows_inserted=1)
    # On exit: {"event": "scope-end", "scope": "db_transaction",
    #           "table": "users", "rows_inserted": 1, "duration_ms": 3.2}
```

Add fields mid-scope with `add_fields()`.
On exception, logs `scope-failed` and re-raises.

Async usage:

```python
async with log_scope("api-request", endpoint="/orders") as scope:
    result = await fetch_orders()
    scope.add_fields(order_count=len(result))
```

## Error Context

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

Never log passwords, tokens, or raw PII. Structure log calls to exclude sensitive fields
from the outset:

```python
log.info("user-authenticated", user_id=123, email_domain="example.com")
```

## Performance

Log batch start/end, not every item:

```python
log.info("batch-processing-started", item_count=len(large_list))
# ... process items ...
log.info("batch-processing-completed", processed_count=processed)
```

For high-volume events, sample instead of logging every occurrence:

```python
import random

if random.random() < 0.1:  # 10% sampling
    log.debug("high-frequency-event", event_data=data)
```

Avoid chatty `info` logs in tight loops.
Use `debug`, sample, or aggregate instead.

## Monitoring-Friendly Logging

Design logs for easy parsing by monitoring systems:

```python
log.info("api-response",
         endpoint="/api/users",
         method="GET",
         status_code=200,
         response_time_ms=45,
         cache_hit=True)
```
