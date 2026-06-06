# Fix Bootstrap Pipeline Debug Leak

## Problem

`_ensure_stderr_logging()` in `src/stogger/core.py` configures a minimal
stderr pipeline with no level filter. Debug log statements that fire
during `init_logging()` — before `configure_structlog()` sets up the
full pipeline — leak to stderr.

Four tests fail because of this:
1. `test_exception_renders_traceback_on_stderr_patterns` (unexpected debug lines)
2. `test_console_output_pattern` (unexpected debug lines)
3. `test_console_and_file_parity` (unexpected debug lines)
4. `test_default_init_no_internals_on_stderr` (stderr not empty)

## Root Cause

The bootstrap pipeline in `_ensure_stderr_logging()` uses
`structlog.dev.ConsoleRenderer()` which renders ALL levels. There is
no processor that drops debug/trace events.

## Fix

Add a level filter processor to the bootstrap pipeline in
`_ensure_stderr_logging()` that drops events below info level.

Insert a lambda processor BEFORE `ConsoleRenderer` in the processor
list that raises `structlog.DropEvent` when
`event_dict.get("level")` is `"debug"` or `"trace"`.

The existing `log.debug("ensuring-stderr-logging")` call at the top
of `_ensure_stderr_logging` itself must NOT be dropped — it fires
BEFORE the bootstrap pipeline is configured, so it goes through
whatever pipeline existed before (test capture, previous
init_logging, or structlog default).

## Files to Change

- `src/stogger/core.py` — modify `_ensure_stderr_logging()` only

## What NOT to Change

- The 4 new `log.debug()` calls in config.py and core.py — they are
  correct and useful. The bootstrap pipeline needs to filter them.
- Any test files — the existing tests that check for clean stderr
  are correct expectations.
