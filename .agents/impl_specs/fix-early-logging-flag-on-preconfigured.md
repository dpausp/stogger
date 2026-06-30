# Fix: `_early_logging_active` flag not set on early-return

## Problem

`stogger.init_early_logging()` sets `_early_logging_active = True` only at the END of the function (`src/stogger/core.py:939`). When structlog is already configured at function entry, the function early-returns at `src/stogger/core.py:900-901` WITHOUT setting the flag.

Result: `init_logging()` (`src/stogger/core.py:857`) emits the warning `init-logging-overriding-existing-config` even when the caller follows the documented two-phase init pattern (`init_early_logging()` -> `init_logging()`).

Reproduction: any service where structlog is configured before `init_early_logging()` runs (e.g. gunicorn `--preload`, uv wrapper process, another library configuring structlog during import). Reported from `dompti-web.service`.

## Root Cause

In `src/stogger/core.py`, function `init_early_logging`:

```python
def init_early_logging(*, verbose: bool = False) -> None:
    global _early_logging_active
    # ... verbose/STOGGER_DEBUG debug logging ...
    if structlog.is_configured():
        return  # early return: flag NOT set
    structlog.configure(...)
    # ...
    _early_logging_active = True  # only reached when configure() ran
```

The flag's sole consumer is `init_logging()` at `src/stogger/core.py:857`:

```python
if _already_configured and not _early_logging_active:
    logger.warning("init-logging-overriding-existing-config", ...)
```

Semantically `_early_logging_active` should mean "the two-phase pattern was opted into" — NOT "this specific call performed the configure()". The current placement breaks the documented two-phase pattern whenever structlog is pre-configured by anything other than init_early_logging itself.

## Fix A: Move flag set BEFORE the early-return

In `src/stogger/core.py`, function `init_early_logging`:

- Move the line `_early_logging_active = True` from the END of the function (currently `core.py:939`, after the second `structlog.configure(...)` call and `logging.basicConfig(...)`) to the TOP of the function, immediately after the `global _early_logging_active` declaration (currently `core.py:891`), BEFORE the `if verbose or os.environ.get("STOGGER_DEBUG"):` block.

Resulting structure:

```python
def init_early_logging(*, verbose: bool = False) -> None:
    """..."""
    global _early_logging_active
    _early_logging_active = True  # always set, before any return

    if verbose or os.environ.get("STOGGER_DEBUG"):
        # ... debug caller logging (unchanged)

    if structlog.is_configured():
        return  # Already configured — flag already set above

    structlog.configure(...)
    # ... rest unchanged, but NO `_early_logging_active = True` at end anymore
    logging.basicConfig(...)
```

Rationale: `_early_logging_active` semantically means "the two-phase pattern is being used". That is true regardless of whether `init_early_logging()` actually performed the configure() or just observed that someone else had. The warning at `core.py:857` exists to flag overrides of pipelines the caller did not author — when the caller opted into the two-phase pattern, no warning is wanted.

Risk: low. Only consumer is `init_logging:857`. `shutdown_logging()` resets the flag explicitly.

## Fix B: Remove dead module-level `_already_configured`

`src/stogger/core.py:32` declares a module-level `_already_configured: bool = False`. Grep shows it is:
- Reset to `False` in `shutdown_logging()` (`core.py:57`)
- NEVER READ by production code

In `init_logging()` (`core.py:812`) a LOCAL variable `_already_configured = _ensure_stderr_logging()` SHADOWS the module-level — they are unrelated despite identical names.

The module-level is vestigial state; it is only read by a test asserting that `shutdown_logging()` resets it. Remove:
- `core.py:30-32` (the comment block + declaration of `_already_configured`)
- `core.py:54` — change `global _already_configured, _early_logging_active` to `global _early_logging_active`
- `core.py:57` — remove the line `_already_configured = False`

Preserve the surrounding comment for `_early_logging_active` (it stays valid).

Also update `tests/test_core.py:443-456` (`test_shutdown_resets_configured_flags`): remove the line `assert core_mod._already_configured is False` (it asserts a dead variable that no longer exists). The remaining assertions (`assert core_mod._early_logging_active is False`, `assert not structlog.is_configured()`) stay — they verify real behavior.

## Regression Tests

Add TWO tests to `tests/test_core.py`:

### Test 1 (unit-level): in `TestInitEarlyLogging` class (test_core.py:945)

```python
def test_init_early_logging_sets_flag_when_already_configured(self):
    """Regression: _early_logging_active must be set even when
    init_early_logging() early-returns because structlog was already
    configured (e.g. gunicorn preload, uv wrapper, another library).

    Without this, init_logging() emits a spurious override warning on
    every startup of services that follow the documented two-phase
    pattern but have structlog pre-configured.
    """
    import stogger.core

    # Simulate third-party pre-configuration (gunicorn preload, etc.)
    structlog.configure(
        processors=[structlog.dev.ConsoleRenderer()],
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.BoundLogger,
        cache_logger_on_first_use=False,
    )

    original = stogger.core._early_logging_active
    try:
        init_early_logging()
        assert stogger.core._early_logging_active is True, (
            "init_early_logging() must set _early_logging_active even "
            "when structlog is already configured — otherwise init_logging() "
            "emits a spurious override warning in two-phase pattern users."
        )
    finally:
        stogger.core._early_logging_active = original
```

### Test 2 (subprocess end-to-end): next to `test_early_to_full_upgrade_no_override_warning` (test_core.py:302)

```python
def test_early_to_full_upgrade_with_preconfigured_no_override_warning(self):
    """Two-phase init must not warn even when structlog is pre-configured
    before init_early_logging() runs (e.g. gunicorn --preload, uv wrapper).

    Regression test for: _early_logging_active was not set when
    init_early_logging() early-returned due to structlog already being
    configured.
    """
    test_script = """
import structlog
import stogger

# Simulate gunicorn preload / uv wrapper / another library
# configuring structlog BEFORE the application's __init__.py runs.
structlog.configure(
    processors=[structlog.dev.ConsoleRenderer()],
    logger_factory=structlog.PrintLoggerFactory(),
    wrapper_class=structlog.BoundLogger,
    cache_logger_on_first_use=False,
)

# Phase 1: application __init__.py calls init_early_logging().
# This is a documented no-op when structlog is already configured,
# but must still mark the two-phase pattern as active.
stogger.init_early_logging()

# Phase 2: CLI/service entry point calls init_logging().
stogger.init_logging()

import sys
sys.stderr.flush()
"""
    result = subprocess.run(
        [sys.executable, "-c", test_script],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "init-logging-overriding-existing-config" not in result.stderr, (
        f"Two-phase upgrade with pre-configured structlog should not "
        f"produce override warning, but got:\n{result.stderr}"
    )
```

## Constraints

- DO NOT modify `_ensure_stderr_logging()` (`core.py:714-749`) — out of scope.
- DO NOT modify the warning text or event ID `init-logging-overriding-existing-config`.
- DO NOT change `shutdown_logging()` semantics beyond removing the dead `_already_configured` reset.
- DO NOT add try/except, logging-in-logging, or defensive layers — the fix is purely reordering + dead-code removal.
- DO NOT modify the docstring of `init_early_logging` beyond what is necessary (it currently correctly says "No-op if structlog is already configured" — keep it).

## Existing Tests That Must Stay Green

- `test_early_to_full_upgrade_no_override_warning` (test_core.py:302) — fresh structlog, no warning
- `test_third_party_pipeline_override_still_warns` (test_core.py:336) — no init_early_logging(), warning expected
- `test_early_flag_suppresses_override_warning` (test_core.py:373) — direct flag patch
- `test_no_early_flag_still_warns` (test_core.py:387) — direct flag patch
- `test_init_logging_warns_on_already_configured` (test_core.py:983) — no init_early_logging(), warning expected
- `test_init_early_logging_fresh` (test_core.py:948)
- `test_init_early_logging_already_configured` (test_core.py:953)
- `test_shutdown_resets_configured_flags` (test_core.py:443) — adjusted per Fix B
- `test_shutdown_allows_reinit_without_warning` (test_core.py:458)

## Verification

1. `CI=1 uv run tox` — full suite green (per project AGENTS.md, includes `docs` env)
2. `uv run ruff check src tests` — 0 issues
3. `uv run ty check` — 0 errors
4. The two new regression tests pass.
