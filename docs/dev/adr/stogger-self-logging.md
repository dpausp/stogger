# stogger-self-logging

## Context

Stogger's own codebase violates its own logging conventions: `complexity-needs-log` fires on `_filter_args()` in `_decorators.py`, and `log-suppression-budget` reports 28 suppressed statements (budget: 7). Several code paths in `core.py` and `config.py` silently swallow errors or skip diagnostic opportunities. Stogger should practice what it preaches by adding proper logging to non-circular code paths and configuring per-file-ignores where logging would be circular.

## Decisions

### overall-strategy

#### Context

Two active violations in `_decorators.py`. Real logging at code paths that benefit from it, config fallback for infrastructure code where logging would be circular or bureaucratic.

#### Decision

Hybrid: add `log.debug()` / `log.warning()` at non-circular code paths in `core.py` and `config.py`. Extend `per-file-ignores` for `_decorators.py` (pure logging infrastructure — logging it would be circular).

#### Alternatives

a. Config-only — fast but stogger never practices its own conventions
b. Real logging everywhere — risks recursion in rendering code

#### Consequences

~8 new log statements across two files plus one config change. Both violations resolved.

### logging-level

#### Context

New log statements need a level respecting stogger conventions CR-4/CR-5.

#### Decision

All new statements at `log.debug()` (no `_replace_msg` needed per CR-5). One exception: `OSError` in `build_logger_factories()` at `log.warning()` with `_replace_msg` because a missing log file is a real operational problem. The catch is broad (`OSError`, not `PermissionError`) so that every file-setup failure variant — permission denied, missing directory, not-a-directory, etc. — surfaces as a warning rather than crashing `init_logging`. The directory is created via `mkdir(parents=True, exist_ok=True)` before opening, so a missing logdir is a non-event for the caller.

#### Alternatives

a. Mix of debug + info — noise for no audience benefit
b. All info — violates stogger convention that infra logging should be debug

#### Consequences

Debug statements invisible unless `verbose=True`. Warning event `file-logging-setup-failed` needs `_replace_msg` and addition to `exempt_event_ids`.

### recursion-safety

#### Context

Adding `log.debug()` inside `PartialFormatter.get_field()` and `format_field()` (core.py:36-51) raises a recursion concern — the log call goes through the structlog pipeline which includes renderers that use `PartialFormatter`.

#### Decision

Safe to proceed. Proof: (1) `log.debug()` has no `_replace_msg` per CR-5, (2) `ConsoleFileRenderer` only constructs `PartialFormatter` when `_replace_msg` is present, (3) `TranslationProcessor` is not in the default `init_logging` processor chain, (4) the kv-rendering path (line 297-302) does string interpolation only, no `PartialFormatter` involved.

#### Alternatives

a. Skip PartialFormatter logging — loses diagnostic value for template debugging
b. Use stdlib logging instead — breaks convention, different output format

#### Consequences

Two new `log.debug()` statements in `PartialFormatter` are safe. No code comments about recursion needed — the proof is structural.

### config-single-source

#### Context

`conftest.py` auto-derives `infrastructure_files` from `per-file-ignores` entries that contain both `except-must-log` and `complexity-needs-log`. The explicit `infrastructure_files` key in `pyproject.toml` is currently the only place `_decorators.py` gets its infrastructure status. After adding `_decorators.py` to `per-file-ignores`, the explicit list becomes redundant.

#### Decision

Remove the explicit `infrastructure_files` key from `[tool.pytest-stogger]` in `pyproject.toml`. Let `conftest.py` auto-derive everything from `per-file-ignores`. Single source of truth.

#### Alternatives

a. Keep both — explicit list as documentation, `setdefault` doesn't overwrite
b. Only add per-file-ignores, leave infrastructure_files — minimal change but redundant

#### Consequences

After change: `per-file-ignores` has three entries (`core.py`, `_colors.py`, `_decorators.py`), `infrastructure_files` is auto-derived from those. Config is DRY.

### event-id-naming

#### Context

New event IDs need kebab-case, max 4 words per CR-1.

#### Decision

Negative naming as drafted: `no-stogger-section`, `no-hatch-section`, `no-pytest-section`, `format-field-missing`, `format-field-bad-format`, `early-init-failed`, `stogger-postgres-not-installed`, `file-logging-setup-failed`. All are precise, grepable, under 4 words.

#### Alternatives

a. Action-based (`probing-skipped-stogger`) — longer, describes action not state
b. Parameterized (`no-config-section` with `section=` key) — DRYer but harder to grep

#### Consequences

8 new event IDs, all kebab-case, all under 4 words. `file-logging-setup-failed` added to `exempt_event_ids`.

### test-strategy

#### Context

Existing tests cover `PartialFormatter` (4 tests), probe functions (indirect via `detect_project_structure`), and decorator helpers (indirect via decorator tests). No tests for PermissionError path, early-init suppress path, or ImportError paths.

#### Decision

Tests-after for new logging paths only. New tests in natural test structure (`test_core.py`, `test_config.py`). No spec-validation tests (overkill for log statements). No tests for config-only changes.

#### Alternatives

a. TDD with spec-validation tests — disproportionate overhead for ~8 log statements
b. No new tests — acceptable but new warning event should have coverage

#### Consequences

New test cases for: `file-logging-setup-failed` warning, `early-init-failed` debug, `stogger-postgres-not-installed` debug, probe early-exit debugs. ~4-5 new test functions.

## Verified By

## Addendum: Bug-Fix for Missing-Logdir Crash

The original decision covered only `PermissionError`. A downstream consumer reported
that `init_logging(logdir=path)` crashed with `FileNotFoundError` when `path`
did not exist, because `Path.open("a")` does not create parent directories and the
narrow `PermissionError` catch left every other `OSError` subclass uncaught. Resolution
broadens the catch to `OSError` (subsuming `PermissionError`) and adds the missing
`mkdir(parents=True, exist_ok=True)` before the open. The event-id was renamed from
`file-open-permission-denied` to `file-logging-setup-failed` because the original name
implied a permission problem when the actual cause could be any file-setup failure.
The contract "warn and continue" is unchanged — only its scope is corrected.

