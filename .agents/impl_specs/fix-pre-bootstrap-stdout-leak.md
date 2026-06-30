# Fix Pre-Bootstrap Stdout Leak

## Problem

Two debug events fire BEFORE the bootstrap pipeline is configured,
going through structlog's default PrintLogger which writes to stdout:

1. `log.debug("init-logging-started")` at the top of `init_logging()`
2. `log.debug("ensuring-stderr-logging")` at the top of `_ensure_stderr_logging()`

When structlog is unconfigured (fresh test, first `init_logging()` call),
`log.debug()` uses the default `PrintLogger` → stdout. This breaks all
E2E tests that assert `captured.out == ""`.

## Root Cause

Execution order in current code:

```
init_logging():
    _already_configured = structlog.is_configured()
    log.debug("init-logging-started")     ← structlog UNCONFIGURED → stdout
    _ensure_stderr_logging():
        log.debug("ensuring-stderr-logging") ← structlog UNCONFIGURED → stdout
        structlog.configure(stderr pipeline)  ← NOW configured
    ...
```

The `_drop_below_info` filter only works in the bootstrap pipeline,
but these events fire before that pipeline exists.

## Fix

### In `_ensure_stderr_logging()`

Move `log.debug("ensuring-stderr-logging")` to AFTER the
`structlog.configure()` call, not before. This way it goes through
the bootstrap pipeline which filters it via `_drop_below_info`.

### In `init_logging()`

Move the `_ensure_stderr_logging()` call to the very first line of
the function, BEFORE `_already_configured` and BEFORE any
`log.debug()`. This ensures the bootstrap pipeline (with stderr +
debug filter) is active when `log.debug("init-logging-started")`
fires.

Resulting order:

```
init_logging():
    _ensure_stderr_logging()              ← bootstrap pipeline up
        log.debug("ensuring-stderr-logging")  ← filtered by _drop_below_info
    _already_configured = structlog.is_configured()
    log.debug("init-logging-started")     ← filtered by _drop_below_info
    ...
```

## Files to Change

- `src/stogger/core.py` — reorder in `_ensure_stderr_logging()` and `init_logging()`

## What NOT to Change

- The 4 log.debug() calls themselves — they are correct and satisfy
  complexity-needs-log
- The `_drop_below_info` processor — it works correctly once the
  pipeline is configured
- Test files — the `assert captured.out == ""` assertions are correct
