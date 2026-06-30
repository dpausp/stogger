# Stogger Structured Logging Skill

## Project Setup

**Dependencies:**
```bash
uv add stogger
uv add --dev pytest-stogger pytest-structlog
```

**pyproject.toml:**
```toml
[tool.stogger]
log_format = "simple"
syslog_identifier = "myapp"

[tool.pytest-stogger]
source = "src/mypackage"
test_dir = "tests"
```

**Initialization at entry point:**
```python
import stogger
import structlog

stogger.init_logging(logdir="/var/log/myapp", syslog_identifier="myapp")
log = structlog.get_logger()
```

**Imports — always these two:**
```python
import structlog

log = structlog.get_logger()
```

Never `import logging`. Never `logging.getLogger()`. Always `structlog.get_logger()`.

## Artifacts

### Log Call Schema

Every log call follows this structure:

```python
log.LEVEL("event-id", _replace_msg="Human text with {key}", key=value, ...)
```

**LEVEL**: one of `debug`, `info`, `warning`, `error`, `exception`
**event-id**: machine-readable label in `kebab-case`, max 4 words
**_replace_msg**: human-readable template with `{key}` placeholders (see level rules below)
**key=value**: structured context data

### Level Rules

| Level | `_replace_msg` | Audience | When to use |
|-------|---------------|----------|-------------|
| `debug` | **NEVER** | Developer | Internal operations, cache hits, branch decisions |
| `info` | **ALWAYS** | User | Business events, state changes, milestones |
| `warning` | **ALWAYS** | User | Degraded but functional, unusual conditions |
| `error` | Optional | Ops | Failures that need attention |
| `exception` | No | Ops | In except blocks — auto-captures traceback |

```python
# debug — developer context, no _replace_msg
log.debug("cache-hit", operation="scan", name=name, cache_type="redis")

# info — user-facing event, always has _replace_msg
log.info("user-login", _replace_msg="User {user_id} logged in", user_id=123)

# warning — degraded state, always has _replace_msg
log.warn("rate-limit-approaching", _replace_msg="Rate limit approaching for {user_id}", user_id=123)

# exception — in except blocks, no _replace_msg needed
log.exception("database-connection-failed", host="db.example.com")
```

### The _replace_msg Pattern

`_replace_msg` is a template string with `{key}` placeholders. The same keys appear as keyword arguments. Placeholders render for humans; key=value keeps data structured and filterable.

```python
log.info("order-created",
         _replace_msg="Order {order_id} created for user {user_id}",
         order_id=12345,
         user_id=67890,
         total_cents=9999)
```

**FORBIDDEN:**
```python
# f-strings in _replace_msg — breaks structured data extraction
log.info("fetch", _replace_msg=f"Fetching {sid[:10]}")

# Naked event without context
log.info("processing-started")

# Prose event IDs
log.info("user logged in successfully")
```

**REQUIRED:**
```python
# Placeholder + structured data
log.info("fetch", _replace_msg="Fetching {sid}", sid=sid)

# Context via keyword arguments
log.info("processing-started", _replace_msg="Processing started", items=len(items))

# kebab-case event IDs
log.info("user-login", ...)
```

### Exception Handling

```python
try:
    risky_operation()
except ValueError:
    # log.exception() auto-captures traceback — no error=str(e) needed
    log.exception("validation-failed", field="email")
    raise
except Exception:
    log.exception("operation-failed")
    raise
```

**Rules:**
- Use `log.exception()` in except blocks, never `log.info()`
- Never pass `error=str(e)` — the exception is captured automatically
- Never pass `exc=e` — redundant with `log.exception()`
- Every except block must contain at least one log call
- Re-raise with `raise` unless SPEC explicitly requires suppression

### bind() for Repeating Keys

When 3+ log calls repeat the same keyword arguments, use `log.bind()`:

```python
# BEFORE — repeating keys
def process(items):
    for item in items:
        log.info("item-started", batch_id=batch_id, item_id=item.id)
        log.info("item-finished", batch_id=batch_id, item_id=item.id, result=len(item.data))

# AFTER — bind once
def process(items):
    batch_log = log.bind(batch_id=batch_id)
    for item in items:
        item_log = batch_log.bind(item_id=item.id)
        item_log.info("item-started", _replace_msg="Processing item {item_id}", item_id=item.id)
        item_log.info("item-finished", _replace_msg="Item {item_id} done", item_id=item.id, result=len(item.data))
```

### Decorators

Import from stogger top-level:

```python
from stogger import log_call, log_result, log_operation, log_scope
```

- `@log_call` — logs function invocation with resolved arguments
- `@log_result` — logs return value and duration on success, exception on failure
- `@log_operation` — full audit: arguments + return value + duration in one event
- `log_scope("name", **fields)` — context manager for scoped logging with `add_fields()`

```python
@log_call
def process_order(order_id: int):
    ...  # Logs: {"event": "called", "func": "module.process_order", "args": {"order_id": 42}}

@log_result
def timed_operation():
    return perform_work()
    # Logs: {"event": "returned", "duration_ms": 12.3, "result": ...}

with log_scope("db_transaction", table="users") as scope:
    insert(user)
    scope.add_fields(rows_inserted=1)
    # Exit: {"event": "scope-end", "scope": "db_transaction", "table": "users", "rows_inserted": 1, "duration_ms": 45.2}
```

### Testing

Use `pytest-structlog` for test assertions. The `log` fixture captures all structlog events:

```python
from pytest_structlog import StructuredLogCapture

def test_order_processing(log: StructuredLogCapture):
    process_order(42)

    # Assert specific event with context
    assert log.has("order-processed", order_id=42, level="info")

    # Count occurrences
    assert log.count("order-processed") == 1

    # Ordered subset match
    assert log.events >= [
        {"event": "order-processed", "level": "info"},
        {"event": "order-shipped", "level": "info"},
    ]
```

**pytest-stogger** runs 13 convention rules automatically via AST analysis — no test files needed. It checks event ID format, `_replace_msg` presence, exception handling, complexity coverage, and more.

### Output Rendering Keys

| Key | Use case |
|-----|----------|
| `_replace_msg` | Human-readable text with `{key}` placeholders |
| `_raw_output` | Tool output with ANSI colors (preserved in console, stripped in file) |
| `_raw_output_prefix` | Label prefix for `_raw_output` |
| `cmd_output_line` | Command output lines (dimmed) |
| `stdout` / `stderr` | Subprocess output (dimmed) |

## Skills

### Event ID Naming Pattern

**Rule:** Event IDs are labels for filtering, not sentences. `kebab-case`, max 4 words.

```
GOOD:  "user-login", "cache-miss", "config-loaded", "session-timeout"
BAD:   "userLogin", "user_login", "User Login", "user-logged-in-successfully"
```

**When to apply:** Every single log call. No exceptions.

### Level Selection Pattern

**Decision tree:**
1. Is this inside an `except` block? → `log.exception()` (or `log.error()` with `exc_info=True`)
2. Is this a developer-internal detail? → `log.debug()` (no `_replace_msg`)
3. Is this a user-facing state change or milestone? → `log.info()` (with `_replace_msg`)
4. Is something unusual but still working? → `log.warn()` (with `_replace_msg`)
5. Did something fail outside an except block? → `log.error()`

**Boundaries:**
- `log.info()` in except blocks is FORBIDDEN — use `log.exception()` or `log.error()`
- `_` prefixed (private) functions must NOT use `log.info()` — use `log.debug()`
- `log.debug()` must NOT have `_replace_msg`

### Context Data Pattern

**Rule:** Every log call needs at least one keyword argument beyond `_replace_msg`. Naked `log.info("event-id")` is forbidden.

```python
# BAD — no context
log.info("processing-started")

# GOOD — structured context
log.info("processing-started", _replace_msg="Processing started", items=len(items))
```

**When to apply:** Every log call.

### Timing Pattern

```python
import time

start = time.time()
log.info("operation-started", _replace_msg="Starting {operation}", operation="data_sync")

result = perform_operation()

log.info("operation-completed",
         _replace_msg="{operation} completed",
         operation="data_sync",
         duration_ms=round((time.time() - start) * 1000))
```

Or use `@log_result` decorator for automatic timing.

### Progress Reporting Pattern

```python
def process_files(file_list: list[str]):
    total = len(file_list)
    log.info("batch-started", _replace_msg="Processing {total} files", total=total)

    for i, file_path in enumerate(file_list, 1):
        log.debug("file-processing", file_path=file_path, index=i)
        process_file(file_path)

        if i % 10 == 0 or i == total:
            log.info("batch-progress",
                     _replace_msg="Processed {current}/{total} files",
                     current=i, total=total)

    log.info("batch-completed", _replace_msg="All {total} files processed", total=total)
```

## Heuristics

### If adding a log call → follow the checklist

1. Event ID: `kebab-case`, max 4 words, descriptive label
2. Level: debug (no msg), info (with msg), warn (with msg), error, exception
3. Context: at least one keyword argument
4. `_replace_msg`: present for info/warn, absent for debug, not needed for exception
5. No f-strings in `_replace_msg` — use `{key}` placeholders
6. No `error=str(e)` with `log.exception()`

### If inside an except block → use log.exception()

Always. Never `log.info()`. Never `log.error()` with `error=str(e)`. The traceback is captured automatically.

### If logging user-visible output → use log.info() with _replace_msg

Not `print()`, not `typer.echo()`. stogger fuses user output with logging — single source of truth for both humans and machines.

### If 3+ calls repeat the same keys → use log.bind()

Reduces noise, ensures consistency, prevents accidental key name drift.

### If function is private (_prefix) → use log.debug()

Private functions are internal. User-facing messages (`log.info()`) belong in public functions only.

### If testing log output → use log.has()

Not `caplog`, not `log_to_stdlib`, not custom processors. `pytest-structlog` captures events directly from the structlog pipeline.

## Experience

### Typical Integration

1. `uv add stogger && uv add --dev pytest-stogger pytest-structlog`
2. Add `[tool.stogger]` and `[tool.pytest-stogger]` to pyproject.toml
3. Call `stogger.init_logging()` in `__main__.py` or CLI entry point
4. `import structlog; log = structlog.get_logger()` in each module
5. Run `uv run pytest` — stogger convention rules check automatically

### Migration from stdlib logging

```python
# BEFORE
import logging
logger = logging.getLogger(__name__)
logger.info(f"User {uid} logged in")

# AFTER
import structlog
log = structlog.get_logger()
log.info("user-login", _replace_msg="User {user_id} logged in", user_id=uid)
```

Key changes: `import structlog` not `logging`, event IDs not prose, `_replace_msg` not f-strings, keyword args not formatted strings.

### Common Agent Mistakes

1. **Using `import logging`** — must be `import structlog`
2. **Missing `_replace_msg` on info/warn** — info and warn are user-facing, always need it
3. **Adding `_replace_msg` on debug** — debug is developer-only, structured keys suffice
4. **f-strings in `_replace_msg`** — use `{key}` placeholders + separate key=value
5. **`log.info()` in except blocks** — use `log.exception()`
6. **`error=str(e)` with `log.exception()`** — redundant, exception auto-captured
7. **camelCase or prose event IDs** — must be `kebab-case`
8. **Naked events without context** — always add keyword arguments
9. **Using `caplog` in tests** — use `pytest-structlog` `log` fixture instead

### CLI Command Pattern

```python
def deploy_command(package_name: str, environment: str):
    log.info("deployment-started",
             _replace_msg="Deploying {package} to {env}...",
             package=package_name, env=environment)

    try:
        result = deploy_package(package_name, environment)
        log.info("deployment-completed",
                 _replace_msg="Deployed {package} to {env}",
                 package=package_name, env=environment,
                 deployment_id=result.id)
    except DeploymentError:
        log.exception("deployment-failed",
                      package=package_name, env=environment)
        raise
```

### Configuration File Pattern

```python
def validate_config(config_path: Path):
    log.debug("config-validation-started", config_path=str(config_path))

    if not config_path.exists():
        log.error("config-file-missing",
                  _replace_msg="Configuration file not found: {path}",
                  path=str(config_path))
        raise FileNotFoundError(f"Config file missing: {config_path}")

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError:
        log.exception("config-parse-failed", config_path=str(config_path))
        raise

    log.info("config-validation-completed",
             _replace_msg="Configuration validated",
             config_path=str(config_path),
             config_keys=list(config.keys()))
    return config
```

## Natural Talent

### Distinguishing Event ID from Message

Event IDs are labels for log aggregation and filtering. `_replace_msg` is the human sentence. They serve different audiences and must both be present for user-facing logs.

- Event ID: `"user-login"` — for `grep`, `jq`, monitoring dashboards
- `_replace_msg`: `"User {user_id} logged in"` — for humans reading console or log files

### Distinguishing debug from info

Ask: "Would a user of this application need to see this?" If yes → `info` with `_replace_msg`. If no, it's developer context → `debug` without `_replace_msg`.

- User sees: "Order 123 created" → `log.info("order-created", ...)`
- Developer needs: "Cache hit for key user:123" → `log.debug("cache-hit", ...)`
- User sees: "Processing started" → `log.info("processing-started", ...)`
- Developer needs: "Branch took path B" → `log.debug("branch-decision", ...)`

### Knowing when to bind vs inline

If a function logs about the same entity 3+ times → `log.bind()`. If it logs once or about different entities → inline keyword arguments. The threshold is repetition, not complexity.

### Judging exception context

`log.exception()` needs operational context (what was being attempted), not the error message. The error itself is captured in the traceback. Good: `log.exception("payment-failed", order_id=123, gateway="stripe")`. Bad: `log.exception("payment-failed", error=str(e))`.
