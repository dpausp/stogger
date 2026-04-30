# Quality Audit Report

## Human Summary

Quality meta-audit of the stogger logging library (standalone repo, HEAD `e2f2342`). All baseline quality gates pass cleanly: tox 5/5 envs green, ruff 0 issues, ty 0 errors, pytest 43/43 pass. No fixes were needed. The project has excellent mock hygiene (100% spec'd, 0 bare MagicMock) and genuine E2E tests for the core logging pipeline. Main concern: 54.62% code coverage with 6 public API symbols completely untested (including filesystem I/O code). Ruff config suppresses all complexity rules, hiding the exact issues that complexipy flags as failures. Grade: **B-**.

## Completion Checklist

- [x] Entry point inventory completed (all 10 `__all__` exports catalogued)
- [x] E2E smoke test completed (4/4 PASS — import, config, early_logging, init_logging)
- [x] Structural inventory completed (noqa, mock, complexity, type:ignore)
- [x] Quality gates collected (baseline + extreme)
- [x] All 4 investigation streams completed with structured review results
- [x] Tool tolerance audit produced with per-tool signals (ruff: orange, ty: green, pytest: green)
- [x] Test structure report with mock health metrics
- [x] E2E coverage assessed for every entry point (2 PROVEN, 4 SUSPECTED, 4 UNKNOWN)
- [x] Full CLI test not triggered — library project, core paths proven via E2E tests + smoke tests
- [x] No fixes needed — all baseline gates already green
- [x] Fix loop not required — nothing to fix
- [x] Git commit: pending (report only)

## Entry Point Inventory

| Entry Point | Type | Source | Smoke | E2E Status | Evidence |
|-------------|------|--------|-------|------------|----------|
| StoggerConfig | class | config.py:83 | PASS | PROVEN | test_config.py (8 tests) |
| init_logging | function | core.py:455 | PASS | PROVEN | test_e2e_single_module_app.py (4 E2E tests) |
| init_early_logging | function | core.py:554 | PASS | SUSPECTED | 1 unit test only |
| logging_initialized | function | core.py:905 | — | SUSPECTED | 1 test (early logging fallback) |
| init_command_logging | function | core.py:810 | — | UNKNOWN | Zero tests (imported but never called) |
| drop_cmd_output_logfile | function | core.py:861 | — | UNKNOWN | Zero tests (imported but never called) |
| JournalLoggerFactory | class | core.py:592 | — | UNKNOWN | Stub returning None, zero tests |
| MultiOptimisticLogger | class | core.py:775 | — | SUSPECTED | Indirect E2E via init_logging |
| MultiOptimisticLoggerFactory | class | core.py:753 | — | SUSPECTED | Indirect E2E via init_logging |
| SystemdJournalRenderer | class | core.py:634 | — | UNKNOWN | Zero tests, ~76 LOC renderer |

## Tool Tolerance Audit

| Tool | Baseline | Extreme | Delta | Signal |
|------|----------|---------|-------|--------|
| ruff | 0 issues | **177 issues** | **+177 suppressed** | orange |
| ty | 0 errors | — | 0 | green |
| pytest | 43 passed | 41P/2F (plugin bug) | 2 plugin failures | green |
| tox | 5/5 envs PASS | — | — | green |
| coverage | 54.62% | — | — | orange |

### Ruff Suppression Analysis

- **35 rules ignored** in pyproject.toml — intentional project decisions
- **Legitimate** (22 rules): D-rules (docstring style), COM812 (formatter conflict), E402 (log init order), FBT (boolean trap), N806 (ANSI naming), TRY300 (style)
- **Questionable** (8 rules): A002 (builtin shadowing), ARG001 (unused args), SLF001 (private access — hides 4 structlog internal dependencies), SIM115 (context managers), BLE001 (broad except), S603/S607 (subprocess security), LOG015 (root logger — hides 2 violations)
- **Critical hiding** (5 rules): PLR0911/PLR0912/PLR0913/PLR0915/PLR2004 — **silences ALL complexity rules**, hiding the exact issues complexipy flags as failures (CC 43, 36, 18)
- **Inline suppressions**: 1 noqa (core.py:531 T201 — intentional print to stderr)
- **type:ignore**: 0 in source code
- **skip/xfail**: 0 in test code

### ty Analysis

- Clean baseline — 0 errors, 0 warnings
- 2 targeted `# ty: ignore` comments for structlog internal API access
- No issues found

### pytest-stogger Plugin Bug

Running `pytest -m ""` (select all) reveals 2 failures in the external `pytest-stogger` plugin:
- `UnboundLocalError: cannot access local variable 'qualname'` in `rules.py:355`
- These are NOT stogger bugs — they're in the test plugin itself

## Test Structure

- Total tests: 43 (36 in test files + 7 stogger doctests)
- Distribution: unit ~34 (79%), integration 0, e2e 4 (9%), smoke/doctest 5 (12%)
- Mock health: 0 bare MagicMock, 17 spec=/autospec= constraints (100% spec'd)
- Skip/xfail: 0
- RED FLAGS: 0/10 — not a mock-only suite
- Signal: orange (54.62% coverage, 6 untested public API symbols)

### Coverage by Module

| Module | Coverage | Gap |
|--------|----------|-----|
| `__init__.py` | 100% | — |
| `factory.py` | 79.37% | 16/94 stmts uncovered |
| `_colors.py` | 31.25% | Terminal color constants — acceptable |
| `core.py` | 60.36% | 129/377 stmts uncovered (renderers, command logging) |
| `config.py` | 30.04% | 114/185 stmts, 0/58 branches (entire detection pipeline) |
| `_regexes.py` | 0% | Regex patterns only — acceptable |

### Untested Public API Symbols (6)

1. `init_command_logging` — 48 LOC, filesystem I/O, no error handling tests
2. `drop_cmd_output_logfile` — 52 LOC, file deletion, PermissionError handling
3. `SystemdJournalRenderer` — ~76 LOC renderer, syslog priority mapping
4. `JournalLoggerFactory` — stub (low risk)
5. `MultiOptimisticLogger` — core dispatch, only indirect E2E
6. `MultiOptimisticLoggerFactory` — factory, only indirect E2E

## E2E Coverage Assessment

- PROVEN: 2 entry points (StoggerConfig, init_logging)
- SUSPECTED: 4 entry points (init_early_logging, logging_initialized, MultiOptimisticLogger, MultiOptimisticLoggerFactory)
- UNKNOWN: 4 entry points (init_command_logging, drop_cmd_output_logfile, JournalLoggerFactory, SystemdJournalRenderer)
- BROKEN: 0 entry points
- Full CLI test triggered: NO (library project)
- Signal: orange

## Stream Signals

- Code Architecture: orange — no test_architecture.py, ConsoleFileRenderer.\_\_call\_\_ CC=43
- Code Quality: orange — 177 suppressed ruff issues, config silences all complexity rules
- Test Structure: orange — excellent mock health but 54.62% coverage, 6 untested exports
- E2E Coverage + Production Reality: orange — core path PROVEN, command logging + journal rendering untested

## Test Automation

- Task runner: tox
- Single-command gate: YES (`CI=1 uv run tox -p`)
- Default coverage: full (no markers deselect tests — `slow`/`integration` markers exist but unused)
- Signal: green

## Complexity Hotspots (complexipy)

| Function | Complexity | File |
|----------|------------|------|
| ConsoleFileRenderer.\_\_call\_\_ | **43** | core.py:163 |
| \_detect_from_pyproject | **36** | config.py:251 |
| configure_stdlib_logging | **18** | factory.py:111 |

All 3 flagged functions are in modules with the highest complexity and the lowest test coverage. The ruff config's PLR ignore rules guarantee these will never be flagged by linter.

## Critical Findings Fixed

None — all baseline quality gates were already green. No fixes applied.

## Code Volume

No code changes in this audit cycle.

## Post-Fix Quality Gates

| Tool | Result |
|------|--------|
| tox (all 5 envs) | PASS — fix OK, 3.13 OK, cov OK, docs OK (28 warnings), build OK |
| pytest | 43 passed, 0 failed |
| ruff check | 0 issues |
| ty check | 0 errors |
| coverage | 54.62% |
| architecture tests | N/A — test_architecture.py does not exist |
| E2E smoke | PASS (4/4) |

## Recommendations

### High Priority

- Add tests for `init_command_logging` — highest-risk untested code (filesystem I/O, systemd detection, factory registration)
- Add tests for `MultiOptimisticLogger.msg` dispatch — core dispatch mechanism never tested in isolation
- Add tests for `SystemdJournalRenderer.__call__` — complex rendering completely unverified

### Medium Priority

- Decompose `ConsoleFileRenderer.__call__` (CC=43, 140 LOC) — extract timestamp, level, PID, exception formatting into separate methods
- Re-enable PLR0912/PLR0913/PLR0915 in ruff config to get automated complexity warnings, or add complexipy to CI
- Create `test_architecture.py` with pytest-archon rules — prevent circular imports and layer violations
- Address 3 private structlog API dependencies (`_frames`, `_format_exception`, `_file`) — will break silently on structlog upgrades
- Add tests for `config.py` detection pipeline (`detect_project_structure`, `_detect_from_pyproject`, `_detect_from_heuristics`) — 0/58 branches covered

### Low Priority

- Remove unused `slow` and `integration` pytest markers (defined but no tests use them)
- Investigate `pytest-stogger` plugin `UnboundLocalError` bug (rules.py:355)
- Remove or implement `enable_pii_scrubbing` config attribute (phantom feature)

## Raw Data Location

`.agents/tmp/quality/` — inventory/, baseline/, extreme/, analysis/, e2e/
