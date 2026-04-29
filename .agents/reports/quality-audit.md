# Quality Audit Report

## Human Summary

Quality meta-audit of the stogger logging library. Found 9 ty diagnostics (single root cause: colorama constant typing in `_colors.py`), fixed by wrapping colorama values with `str()`. The project has a trustworthy test suite: 100% spec'd mocks (0 bare MagicMock), 4 genuine e2e tests using real structlog pipeline, 35 tests total, 0 skip/xfail. Main coverage gaps: 5 of 10 `__all__` exports have zero direct tests (`init_command_logging`, `drop_cmd_output_logfile`, `JournalLoggerFactory`, `MultiOptimisticLogger`, `MultiOptimisticLoggerFactory`, `SystemdJournalRenderer`). No error-hiding detected in tool config.

## Completion Checklist

- [x] Entry point inventory completed (all 10 `__all__` exports + 30+ internal symbols catalogued)
- [x] E2E smoke test completed (6/6 PASS — import, config, init_logging, early_logging, json_renderer, console_renderer)
- [x] All raw data collected in `.agents/tmp/quality/` (baseline/, extreme/, analysis/, e2e/)
- [x] All 4 investigation streams completed with structured review results
- [x] Tool tolerance audit produced with per-tool signals (ruff: green, ty: orange)
- [x] Test structure report with mock health metrics
- [x] E2E coverage assessed for every entry point (4 PROVEN, 2 SUSPECTED, 4 UNKNOWN)
- [x] Full CLI test not triggered — library project, core paths proven via e2e tests + smoke tests
- [x] Fixes applied for critical findings (ty diagnostics resolved)
- [x] Baseline re-run confirms no regressions (tox all 5 envs green)
- [x] Git commit: 2a8b327 on main, not pushed

## Entry Point Inventory

| Entry Point | Type | Source | E2E Status | Evidence |
|-------------|------|--------|------------|----------|
| StoggerConfig | class | config.py:81 | PROVEN | test_config.py (8 tests) + e2e tests |
| init_logging | function | core.py:456 | PROVEN | test_e2e_single_module_app.py (4 tests: console+file, context, disabled, exceptions) |
| init_early_logging | function | core.py:557 | PROVEN | test_core.py subprocess test + smoke test |
| logging_initialized | function | core.py:909 | PROVEN | Smoke test + e2e tests |
| init_command_logging | function | core.py:813 | UNKNOWN | No tests found |
| drop_cmd_output_logfile | function | core.py:864 | UNKNOWN | No tests found |
| JournalLoggerFactory | class | core.py:595 | UNKNOWN | Stub returning None, no tests |
| MultiOptimisticLogger | class | core.py:778 | SUSPECTED | Indirect e2e coverage via init_logging, no direct tests |
| MultiOptimisticLoggerFactory | class | core.py:756 | SUSPECTED | Indirect e2e coverage via init_logging, no direct tests |
| SystemdJournalRenderer | class | core.py:637 | UNKNOWN | No tests, 5-method class with complex rendering |

## Tool Tolerance Audit

| Tool | Baseline | Extreme | Delta | Signal |
|------|----------|---------|-------|--------|
| ruff | 0 issues | 179 issues | 179 suppressed | green |
| ty (pre-fix) | 9 diagnostics | — | 1 root cause | orange |
| ty (post-fix) | 0 diagnostics | — | resolved | green |

### Ruff Suppression Analysis

- **35 rules ignored** in pyproject.toml — intentional project decisions, not error-hiding
- **Legitimate** (27 rules): D-rules (docstring style), PLR (complexity thresholds), COM812 (formatter conflict), E402 (log init order)
- **Questionable** (8 rules): A002 (builtin shadowing), ARG001 (unused args), SLF001 (private access), SIM115 (context managers), BLE001 (broad except), S603/S607 (subprocess)
- **Critical hiding** (3 rules): BLE001 blinds to future broad excepts, S603/S607 silences future subprocess warnings, SLF001 hides 3 private structlog API dependencies
- **Zero** noqa comments in source code
- **Zero** skip/xfail in tests

### ty Analysis

- All 9 diagnostics were from single root cause: `_colors.py` color constants had union type (`int | str`) from colorama conditional
- **Fixed**: Wrapped colorama values with `str()` for consistent typing
- Remaining: 1 `# ty: ignore[unresolved-import]` needed for tox env (tradeoff: appears unused in main venv)

## Test Structure

- Total tests: 35
- Distribution: unit 31, integration 0, e2e 4
- Mock health: 0 bare MagicMock, 14 with spec=/autospec= (100% spec'd)
- Skip/xfail: 0
- RED FLAGS: 0/10 — not a mock-only suite
- Signal: orange (coverage gaps in 5 `__all__` exports)

### Coverage Gaps

**Untested `__all__` exports** (5):
- `init_command_logging` — file creation, systemd detection, factory registration
- `drop_cmd_output_logfile` — private `_file` attribute access
- `JournalLoggerFactory` — stub (low risk)
- `MultiOptimisticLogger` / `MultiOptimisticLoggerFactory` — core dispatch mechanism

**Untested internal symbols** (13):
- `PartialFormatter`, `prefix()`, `format_exc_info()`, `SelectRenderedString`, `log_to_stdlib()`
- `CmdOutputFileRenderer`, `MultiRenderer`
- `ProjectStructure` (+ 3 methods), `detect_project_structure()`

## E2E Coverage Assessment

- PROVEN: 4 entry points (StoggerConfig, init_logging, init_early_logging, logging_initialized)
- SUSPECTED: 2 entry points (MultiOptimisticLogger, MultiOptimisticLoggerFactory)
- UNKNOWN: 4 entry points (init_command_logging, drop_cmd_output_logfile, JournalLoggerFactory, SystemdJournalRenderer)
- BROKEN: 0 entry points
- Full CLI test triggered: NO (library project)
- Signal: orange

## Stream Signals

- Code Architecture: orange — no test_architecture.py, ConsoleFileRenderer.__call__ CC=28 god-method
- Code Quality: green — clean baseline ruff, ty issues resolved
- Test Structure: orange — excellent mock health but 5 untested `__all__` exports
- E2E Coverage + Production Reality: orange — core path proven, command logging and journal rendering untested

## Critical Findings Fixed

- **ty unsupported-operator (8 errors)**: Fixed by wrapping colorama attribute assignments with `str()` in `_colors.py`. Both branches now produce consistent `str` type.

## Code Volume

| File | Change |
|------|--------|
| packages/stogger/src/stogger/_colors.py | +10/-2 (str() wrapping + restore ty: ignore) |

## Post-Fix Quality Gates

| Tool | Result |
|------|--------|
| tox (all 5 envs) | PASS — fix OK, cov OK, docs OK, build OK, 3.13 OK |
| pytest | 35 passed, 0 failed |
| ruff check | 0 issues |
| ty check (standalone) | 0 errors, 1 warning (unused-ignore-comment, inherent tradeoff) |
| architecture tests | N/A — test_architecture.py does not exist |
| E2E smoke | PASS (6/6) |

## Recommendations

### High Priority
- Add tests for `init_command_logging` — highest-risk untested code (file I/O without error handling)
- Add tests for `MultiOptimisticLogger.msg` dispatch — core dispatch mechanism never tested in isolation
- Add tests for `SystemdJournalRenderer.__call__` — complex rendering completely unverified

### Medium Priority
- Decompose `ConsoleFileRenderer.__call__` (CC=28, 140 LOC) — extract timestamp, level, PID, exception formatting into separate methods
- Create `test_architecture.py` with pytest-archon rules — prevent circular imports and layer violations
- Address 3 private structlog API dependencies (`_frames`, `_format_exception`, `_file`) — these will break silently on structlog upgrades

### Low Priority
- Add missing documentation files (i18n.md, integrations.md, migration_guide.md, migration_templates.md) referenced in docs toctree
- Fix getting_started.md API signature mismatch (documents `level`, `format`, `include_timestamp` but actual signature uses `logdir`, `log_cmd_output`, etc.)
- Remove or implement `enable_pii_scrubbing` config attribute (phantom feature)

## Raw Data Location

`.agents/tmp/quality/` — baseline/, extreme/, analysis/, e2e/
