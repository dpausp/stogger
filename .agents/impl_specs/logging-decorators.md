---
lifecycle:
  requirements:
    completed_at: "2026-05-03T12:00:00Z"
    git_rev: "c4f0f2b"
  design:
    completed_at: "2026-05-03T12:30:00Z"
    git_rev: "c4f0f2b"
---

# logging-decorators

## Context

Stogger has no decorators or context managers for structured logging. Users must manually write `log.info("called", func=..., args={...})`. Three named decorators and one context manager will provide structured call/result logging that integrates with the existing structlog pipeline.

## Decisions

### module-placement

#### Context

New code must fit the existing layered architecture enforced by pytest-archon. core.py is already 951 lines and should not grow further.

#### Decision

New private module `src/stogger/_decorators.py` at Layer 2. Imports `_types` and `structlog`. Re-exported through `core.py` → `__init__.py`. Registered in `test_architecture.py` with Layer 2 rules (may import `_types`, `config`; may not import `factory` or `__init__`).

#### Alternatives

a. Add to core.py — would push it past 1100 lines, no separation of concerns
b. Public `decorators.py` at Layer 1 — cannot import `_types`, would need duplicate EventDict

#### Consequences

Clean module boundary. Architecture enforcement covers the new code from day one.

### decorator-variants

#### Context

Users need different granularity levels for function-call logging. Three named decorators are more discoverable than one configurable decorator.

#### Decision

Three decorators with distinct semantics:

1. `@log_call` — logs at entry. Event: `event="called"`, `func="module.qualname"`, `args={...}`. No result, no duration.
2. `@log_result` — logs at exit. Event: `event="returned"`, `func="module.qualname"`, `result=...`, `duration_ms=...`. No args.
3. `@log_operation` — logs at exit. Event: `event="operation"`, `func="module.qualname"`, `args={...}`, `result=...`, `duration_ms=...`. Everything in one event.

All three share: sync+async support, `include_args`/`exclude_args` filtering, auto-logger via `structlog.get_logger()`, exception logging with re-raise, automatic `self`/`cls` filtering.

#### Alternatives

a. Single decorator with mode parameter — less discoverable, obscures intent
b. Eliot-style start/end event pairs — doubles output, adds complexity

#### Consequences

Three explicit import paths. Users choose by intent: invocation tracking (`log_call`), result tracking (`log_result`), full audit (`log_operation`).

### scope-object-design

#### Context

The `log_scope()` context manager needs state (start time, bound fields, accumulated fields) and explicit enter/exit behavior including exception handling.

#### Decision

`LogScope` class with `__enter__`/`__exit__`. On enter: binds fields via structlog context. On exit: logs `scope_end` event with duration and accumulated fields. On exception: logs `scope_failed` event with `exc_type`/`exc_msg`, then re-raises. `add_fields(**kwargs)` method for mid-scope enrichment. Factory function `log_scope(name, **fields)` returns a `LogScope` instance.

Async support via `__aenter__`/`__aexit__` on the same class.

#### Alternatives

a. Generator-based `@contextmanager` — requires separate `@asynccontextmanager` for async
b. Two separate classes for sync/async — doubles code

#### Consequences

Single class handles both sync and async. Stateful object enables `add_fields()` accumulation.

### async-support

#### Context

Python ≥3.14. All decorators and context manager must work with both sync and async functions.

#### Decision

Each decorator uses `inspect.iscoroutinefunction(wrapped_function)` at decoration time. Returns either a sync wrapper or an async wrapper accordingly. No runtime check overhead — the check happens once at import/decoration time.

For `LogScope`: implements both `__enter__`/`__exit__` and `__aenter__`/`__aexit__`. Python automatically calls the correct protocol based on `with` vs `async with`.

#### Alternatives

a. Single sync wrapper — breaks async functions
b. Runtime isinstance(result, Coroutine) check — overhead on every call

#### Consequences

Zero runtime overhead for the sync/async dispatch. Two code paths per decorator, but they share arg-extraction and logging logic.

### arg-extraction

#### Context

Need `args={'x': 1, 'y': 2}` in events. `inspect.getcallargs` is removed in Python 3.14.

#### Decision

`inspect.signature(wrapped_function)` + `sig.bind(*args, **kwargs)` + `bound.apply_defaults()`. This resolves positional args, keyword args, and defaults into a plain dict. Then apply `include_args`/`exclude_args` filtering and strip `self`/`cls`.

#### Alternatives

a. Manual dict construction — loses parameter names and defaults
b. `locals()` capture — unreliable with decorators

#### Consequences

Correct arg resolution including defaults. Standard pattern that works with Python 3.14+.

### duration-measurement

#### Context

`@log_result`, `@log_operation`, and `log_scope()` all need `duration_ms`.

#### Decision

`time.perf_counter()` — capture `t0` at entry, compute `(perf_counter() - t0) * 1000` at exit. Highest resolution, monotonic, no NTP drift.

#### Alternatives

a. `time.monotonic` — practically equivalent on Linux, lower resolution on some platforms
b. Event timestamp subtraction — impossible for single-event decorators like `@log_call`

#### Consequences

Consistent duration measurement across all features. Sub-millisecond precision.

### exception-handling

#### Context

Exceptions in decorated functions must be logged without changing program behavior.

#### Decision

Own `exc_type` and `exc_msg` fields in the event dict. `exc_type` = exception class name (e.g., `"ValueError"`). `exc_msg` = `str(exception)`. Exception is then re-raised unchanged. Does NOT use `exc_info=True` — the existing `process_exc_info`/`format_exc_info` pipeline is not invoked for decorator exceptions.

Event semantics per decorator on exception:
- `@log_call` — no exception handling (logs at entry, before execution)
- `@log_result` — `event="failed"`, `exc_type`, `exc_msg`, `duration_ms`
- `@log_operation` — `event="failed"`, `exc_type`, `exc_msg`, `duration_ms`, `args`
- `log_scope()` — `event="scope_failed"`, `exc_type`, `exc_msg`, `duration_ms`

#### Alternatives

a. `exc_info=True` via existing pipeline — produces full tracebacks, too verbose for every decorated call
b. Both own fields AND exc_info — redundant output

#### Consequences

Compact exception logging. Users get exception type and message without traceback noise. Full tracebacks available via explicit `log.exception()` outside decorators.

### func-name

#### Context

Every event needs a `func` field identifying the decorated function.

#### Decision

`f"{wrapped_function.__module__}.{wrapped_function.__qualname__}"` at decoration time. Stored once, no runtime inspection needed. Works with `@functools.wraps` which preserves `__module__` and `__qualname__`.

#### Alternatives

a. `f.__name__` only — not unique across modules
b. Frame inspection — expensive, unreliable with decorators

#### Consequences

Unique, searchable function identifiers. Zero runtime cost (computed once at decoration).

### test-strategy

#### Context

No shared test fixtures exist. Each test file has its own `_reset_structlog` autouse fixture.

#### Decision

1. New `tests/conftest.py` with shared `_reset_structlog` autouse fixture (call `structlog.reset_defaults()`).
2. New `tests/test_decorators.py` with tests for all three decorators and `log_scope()`.
3. Update `tests/test_architecture.py` to register `_decorators` as Layer 2 module.
4. TDD approach: write tests first, then implementation.

Test locations:
- Permanent decision tests: `tests/test_decorators.py`
- Architecture enforcement: `tests/test_architecture.py`

#### Alternatives

a. No shared conftest, each file has its own reset — inconsistent with the improvement opportunity
b. No new tests — unacceptable for new public API

#### Consequences

Solid test foundation. Architecture rules cover the new module from the start.

## Requirements

### Interface Contracts

**Decorator usage:**
```python
from stogger import log_call, log_result, log_operation

@log_call
def fetch_user(user_id: int): ...

@log_result
def compute_hash(data: bytes) -> str: ...

@log_operation(include_args=["query"], exclude_args=["password"])
def authenticate(query: str, password: str) -> bool: ...
```

**Context manager usage:**
```python
from stogger import log_scope

with log_scope("db_transaction", table="users") as scope:
    insert(user)
    scope.add_fields(rows_inserted=1)
```

**Event examples:**
```
# @log_call
{"event": "called", "func": "mymodule.fetch_user", "args": {"user_id": 42}}

# @log_result
{"event": "returned", "func": "mymodule.compute_hash", "result": "abc123", "duration_ms": 2.4}

# @log_operation
{"event": "operation", "func": "mymodule.authenticate", "args": {"query": "admin"}, "result": true, "duration_ms": 15.3}

# log_scope success
{"event": "scope_end", "scope": "db_transaction", "table": "users", "rows_inserted": 1, "duration_ms": 45.2}

# @log_result exception
{"event": "failed", "func": "mymodule.compute_hash", "exc_type": "ValueError", "exc_msg": "empty input", "duration_ms": 0.1}

# log_scope exception
{"event": "scope_failed", "scope": "db_transaction", "exc_type": "ConnectionError", "exc_msg": "timeout", "duration_ms": 30001.0}
```

### Scope Boundary

Not part of this work: task_uuid, task_level, parent-child tracking, preserve_context, distributed tracing, serialization.

### Files to Create/Modify

- **Create**: `src/stogger/_decorators.py`
- **Modify**: `src/stogger/core.py` — add re-exports for decorators and log_scope
- **Modify**: `src/stogger/__init__.py` — add to `__all__` and import from core
- **Create**: `tests/conftest.py` — shared _reset_structlog fixture
- **Create**: `tests/test_decorators.py`
- **Modify**: `tests/test_architecture.py` — register _decorators as Layer 2
