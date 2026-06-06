# Resolve Stogger Tech Debt — Suppressed Violations

## Context

`STOGGER_TECH_DEBT.md` reports 33 suppressed logging-convention violations.
ADR `docs/dev/adr/stogger-self-logging.md` describes the strategy. Many
planned log statements are already implemented. This spec covers only
the remaining changes.

## Already Done (DO NOT TOUCH)

- `format-field-missing` — core.py PartialFormatter.get_field
- `format-field-bad-format` — core.py PartialFormatter.format_field
- `no-stogger-section` — config.py _probe_stogger_section
- `no-hatch-section` — config.py _probe_hatch_section
- `no-pytest-section` — config.py _probe_pytest_section
- `stogger-postgres-not-installed` — core.py _build_postgres_factory
- `file-open-permission-denied` — core.py build_logger_factories
- `infrastructure_files` — does not exist in pyproject.toml

## Changes Required

### 1. decorators.py → per-file-ignores

In `pyproject.toml`, add to `[tool.pytest-stogger.per-file-ignores]`:

```toml
"decorators.py" = ["except-must-log", "complexity-needs-log"]
```

In `src/stogger/decorators.py` line 31, remove the inline ignore comment
`# stogger: ignore complexity-needs-log` from the function signature.

### 2. config.py — _check_test_dependencies

File: `src/stogger/config.py`, function `_check_test_dependencies` (line 109).

Remove `# stogger: ignore complexity-needs-log` from the function signature.

Add at function entry (after the docstring, before `global _TEST_DEPS_WARNED`):

```python
log = structlog.get_logger(__name__)
log.debug("checking-test-dependencies")
```

### 3. core.py — _build_console_renderer_kwargs

File: `src/stogger/core.py`, function `_build_console_renderer_kwargs`.

Remove `# stogger: ignore complexity-needs-log` from the function signature.

Add at function entry:

```python
log.debug("building-console-renderer-kwargs", verbose=verbose, show_caller_info=show_caller_info)
```

Module-level `log = structlog.get_logger(__name__)` exists at line 22.

### 4. core.py — _ensure_stderr_logging

File: `src/stogger/core.py`, function `_ensure_stderr_logging`.

Remove `# stogger: ignore complexity-needs-log` from the function signature.

Add at function entry:

```python
log.debug("ensuring-stderr-logging", already_configured=structlog.is_configured())
```

Module-level `log` available (line 22).

### 5. core.py — init_logging

File: `src/stogger/core.py`, function `init_logging`.

Remove `# stogger: ignore complexity-needs-log` from the function signature
(keep the `# noqa: PLR0913` comment).

**Python scoping issue:** `init_logging` reassigns `log = structlog.get_logger()`
near the end (line ~701). Python treats `log` as local for the entire function.
Using `log.debug(...)` before line 701 raises UnboundLocalError.

**Fix:** Rename the local assignment at line ~701 from `log` to `logger`.
Update all references after that line:
- `log.warning(...)` → `logger.warning(...)`
- `log.info(...)` → `logger.info(...)`
- `init_command_logging(log, logdir)` → `init_command_logging(logger, logdir)`

After renaming, add at function entry (after `_already_configured = ...`):

```python
log.debug("init-logging-started")
```

## Conventions (from ADR)

- All new log statements at `log.debug()` level
- No `_replace_msg` needed for debug-level logs (CR-5)
- Event IDs in kebab-case, max 4 words
- Module-level `log = structlog.get_logger(__name__)` at core.py:22 is the
  standard logger for non-rendering code
- config.py functions create local `log = structlog.get_logger(__name__)`
  inside each function (existing pattern in that file)

## What NOT to Change

- Rendering pipeline inline ignores (ConsoleFileRenderer, JournalRenderer,
  PostgresRenderer, etc.) — these are circular and legitimate
- Per-file ignores for `_colors.py`, `__init__.py`, `systemd.py` — legitimate
- The `# stogger: ignore` (all rules) comments on rendering methods

## Tests

Add tests in natural test locations (`tests/test_core.py`, `tests/test_config.py`):

1. `_check_test_dependencies` emits `checking-test-dependencies` debug event
2. `init_logging` emits `init-logging-started` debug event
3. `_build_console_renderer_kwargs` emits `building-console-renderer-kwargs` debug event
4. `_ensure_stderr_logging` emits `ensuring-stderr-logging` debug event

Test pattern: call the function with `log` capture fixture, assert `log.has("event-id")`.
