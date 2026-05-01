# Quality Audit Report

## Human Summary

Quality meta-audit of stogger (Python structured logging library) found the project has solid quality infrastructure with 91.68% coverage, real E2E tests, and clean tool baselines. Two issues were fixed: a stale pytest-stogger test referencing a removed fixture (`stogger_infrastructure_files`) and deprecated `infrastructure_files` config replaced with `per-file-ignores`. All 118 tests now pass green. The only remaining concern is ConsoleFileRenderer::\_\_call\_\_ at cognitive complexity 16, which is documented but not decomposed.

## Completion Checklist

- [x] Entry point inventory + smoke test completed
- [x] Structural inventory completed (noqa, mock, complexity, test discovery)
- [x] Quality gates collected (baseline + extreme)
- [x] All 4 investigation streams completed with structured review results
- [x] Tool tolerance audit produced with per-tool signals (ruff/ty/pytest)
- [x] Test collection integrity verified (all test files collected, no config hiding)
- [x] Skip/xfail/xpass audit completed (no skips, no xfails, no xpasses found)
- [x] Test double strategy analyzed (mock:fake:golden:real per layer)
- [x] E2E coverage assessed for every entry point (PROVEN/SUSPECTED/UNKNOWN/BROKEN)
- [x] Full CLI test not triggered — existing E2E evidence sufficient
- [x] Fixes applied for critical findings (stale pytest-stogger API)
- [x] Fix loop completed — Round 1 green (118 passed, 0 failures, 0 errors)
- [x] Git commit: pending

## Entry Point Inventory

| Entry Point | Type | Source | Smoke | E2E Status | Evidence |
|-------------|------|--------|-------|------------|----------|
| init\_logging | function | src/stogger/\_\_init\_\_.py:10 | PASS | PROVEN | test\_e2e\_single\_module\_app.py — 4 scenarios with real structlog pipeline, real file I/O |
| init\_early\_logging | function | src/stogger/\_\_init\_\_.py:11 | PASS | PROVEN | test\_core.py::TestInitEarlyLogging — 2 tests, real structlog.configure() |
| init\_command\_logging | function | src/stogger/\_\_init\_\_.py:12 | PASS | PROVEN | test\_core.py::TestInitCommandLogging — real MultiOptimisticLoggerFactory |
| drop\_cmd\_output\_logfile | function | src/stogger/\_\_init\_\_.py:13 | PASS | PROVEN | test\_core.py::TestDropCmdOutputLogfile — 2 tests incl. edge case |
| logging\_initialized | function | src/stogger/\_\_init\_\_.py:14 | PASS | PROVEN | test\_core.py::TestLoggingInitialized — True/False branches |
| StoggerConfig | class | src/stogger/config.py | PASS | PROVEN | 30 tests in test\_config.py, real TOML loading, heuristics |
| JournalLoggerFactory | class | src/stogger/core.py | PASS | PROVEN | test\_core.py::TestJournalLoggerFactory |
| MultiOptimisticLogger | class | src/stogger/core.py | PASS | PROVEN | test\_core.py::TestMultiOptimisticLogger — 3 tests |
| MultiOptimisticLoggerFactory | class | src/stogger/core.py | PASS | PROVEN | Used throughout E2E tests in real pipeline |
| SystemdJournalRenderer | class | src/stogger/core.py | PASS | PROVEN | test\_core.py::TestSystemdJournalRenderer — 7 tests |
| build\_shared\_processors | function | src/stogger/factory.py | PASS | SUSPECTED | test\_factory.py — 6 tests but only checks processor types, not output |
| build\_renderer | function | src/stogger/factory.py | PASS | SUSPECTED | test\_factory.py — 3 tests check type, not rendering output |
| configure\_stdlib\_logging | function | src/stogger/factory.py | PASS | SUSPECTED | test\_factory.py — 4/5 tests mock logging.basicConfig |
| ConsoleFileRenderer | class | src/stogger/core.py | PASS | PROVEN | 10 tests + real usage in all E2E tests |
| detect\_project\_structure | function | src/stogger/config.py | PASS | PROVEN | test\_config.py — 5 tests covering all paths |
| log\_to\_stdlib | function | src/stogger/core.py | PASS | PROVEN | test\_core.py::TestLogToStdlib — real logging.log() bridge |
| TranslationProcessor | class | src/stogger/core.py | PASS | PROVEN | test\_core.py — 3 tests |
| PartialFormatter | class | src/stogger/core.py | PASS | PROVEN | test\_core.py::TestPartialFormatter — 4 tests |
| SelectRenderedString | class | src/stogger/core.py | PASS | PROVEN | test\_core.py::TestSelectRenderedString — 3 tests |

## Tool Tolerance Audit

| Tool | Baseline | Extreme | Delta | Signal |
|------|----------|---------|-------|--------|
| ruff | 0 issues | **141 issues** | **141 suppressed by config** | green |
| ty | 0 errors | 0 errors | 0 | green |
| pytest | **1 failed + 1 error** → **118 passed** (after fix) | 0 slow, 0 integration | **2 failures fixed** | green |

### ruff Suppression Breakdown

- **ANN (annotations)**: 94 — LEGITIMATE. structlog processor signatures follow structlog convention.
- **D-series (docstrings)**: 42 — QUESTIONABLE. 13 public methods lack docstrings but many are structlog protocol methods.
- **PLR6301 (could-be-static)**: 6 — LEGITIMATE. Methods use self for future extensibility.
- **TRY300 (else-block)**: 3 — LEGITIMATE. Style preference.
- **CPY001 (copyright)**: 6 — LEGITIMATE. Not enforced by project convention.
- **DOC201 (undocumented returns)**: 8 — QUESTIONABLE. Real gap in public API docs.
- **C901 (complexity)**: 1 — LEGITIMATE. Mirrors complexipy finding.
- **S404 (subprocess)**: 1 — LEGITIMATE. Intentional systemctl integration.
- **N806 (naming)**: 1 — LEGITIMATE. SYMB constant for ANSI codes.

**Critical-hiding suppressions**: NONE. All suppressions are legitimate or minor style decisions.

### 8 noqa Comments (all in core.py)

All legitimate: 3x SLF001 (structlog private API access), 2x LOG015 (log bridge by design), 1x PLR0913 (stable API signature), 1x T201 (stderr print), 1x S603/S607 (subprocess for systemctl).

## Test Collection Integrity

| Check | Result | Signal |
|-------|--------|--------|
| Tests on disk | 5 files | — |
| Tests collected | 5 files (111 user + 7 plugin) | — |
| Uncollected files | None | green |
| Collection errors | None (after fix) | green |
| Config exclusions | None | green |
| conftest hooks modifying collection | None — 2 autouse fixtures for cleanup only | green |

- pytest config: testpaths=tests, strict-markers, strict-config, --tb=short
- python\_files=test\_\*.py, \*\_test.py
- Markers defined: slow, integration — **NEVER used on any test**
- Unaccounted test files: none — all files collected

## Skip/Xfail/Xpass Audit

| Category | Count | Signal |
|----------|-------|--------|
| @pytest.mark.skip | 0 | green |
| @pytest.mark.skipif (platform) | 0 | green |
| @pytest.mark.skipif (dependency) | 0 | green |
| @pytest.mark.xfail (strict=True) | 0 | green |
| @pytest.mark.xfail (strict=False) | 0 | green |
| XPASS | 0 | green |
| Lazy skips | 0 | green |
| Flaky-hidden | 0 | green |
| Stale temporal skips | 0 | green |

- Cross-platform skip asymmetry: none (no skips at all)
- Zero test suppressions — clean test suite

## Test Double Strategy

| Layer | Mock | Spec'd Mock | Fake | Golden | Real | Total |
|-------|------|-------------|------|--------|------|-------|
| Unit | 13 | **19 (100% spec'd)** | 0 | 0 | 98 | 111 |
| E2E | 0 | 0 | 0 | 0 | **4** | 4 |
| Integration | 0 | 0 | 0 | 0 | 0 | 0 |

- Tautological tests (mock theater): 0 — no mock-return-assert-call tautologies detected
- Golden file smell: 0 — no golden files in use
- Mock density hotspots: factory.py tests have highest mock usage (4/5 configure\_stdlib\_logging tests mock basicConfig) but one test creates real FileHandler
- **100% mock spec adoption** — all mocks use `spec=` or `autospec=True`
- Overall double strategy verdict: Healthy. Mocks concentrated at unit level, real E2E tests exercise full pipeline.
- RED FLAGS score: 4/10 (below threshold of 6)
- Signal: green

## Test Structure Summary

- Total tests: 118 (111 user + 7 pytest-stogger)
- Distribution: unit 106 (90%), E2E 4 (3%), plugin 7 (6%), integration-marker 0
- test\_core.py: 61 tests (52%)
- test\_config.py: 30 tests (25%)
- test\_factory.py: 15 tests (13%)
- test\_e2e\_single\_module\_app.py: 4 tests (3%)
- test\_exception\_logging.py: 1 test (1%)
- Signal: green

## Test Coverage

| Module | Coverage | Missing Lines | Signal |
|--------|----------|---------------|--------|
| \_\_init\_\_.py | 100.00% | — | green |
| \_colors.py | 100.00% | — | green |
| \_regexes.py | 100.00% | — | green |
| config.py | 97.04% | 279->276, 335->345, etc. (edge branches) | green |
| core.py | 91.50% | 246-258 (color stripping), 526-528 (JOURNAL\_STREAM), 541-545 (ValueError) | green |
| factory.py | **80.00%** | 31, 50, 58, 64-65, 72, 84, 123-125, 144, 159-160, 167-168, 215-224 | orange |

- Overall coverage: **91.68%**
- Modules < 50%: none
- Entry points with 0% coverage: none
- Signal: green (factory.py at 80% is orange but not critical)

## Duration Anomalies

- Total suite time: **3s** (1.12s after fix)
- Duration stats: P50=~5ms, P90=10ms, P95=40ms, P99=160ms

| Category | Count | Details |
|----------|-------|---------|
| EXTREME OUTLIER (>P99+2\*std) | 0 | None |
| FAKE SLOW (marked slow, <P50) | 0 | No slow-marked tests exist |
| HIDDEN SLOW (unmarked, >P95) | 2 | test\_load\_config\_invalid\_toml (0.26s), test\_early\_logging\_graceful\_fallback (0.21s) |
| Zero-duration (<1ms) | 332 | Fast unit tests — expected for mock-light suite |

- Slow test cluster: distributed (no single hotspot)
- Root causes for hidden-slow: TOML error parsing (0.26s), structlog reconfiguration (0.21s) — both legitimate
- Signal: green

## E2E Coverage Assessment

- PROVEN: **16** entry points (init\_logging, init\_early\_logging, init\_command\_logging, drop\_cmd\_output\_logfile, logging\_initialized, StoggerConfig, JournalLoggerFactory, MultiOptimisticLogger, MultiOptimisticLoggerFactory, SystemdJournalRenderer, ConsoleFileRenderer, detect\_project\_structure, log\_to\_stdlib, TranslationProcessor, PartialFormatter, SelectRenderedString)
- SUSPECTED: **3** entry points (build\_shared\_processors, build\_renderer, configure\_stdlib\_logging — tested via mocks, not exercised through real end-to-end output)
- UNKNOWN: 0
- BROKEN: 0 (after fix)
- Full CLI test triggered: **NO** — stogger is a library, not a CLI tool, and existing E2E evidence is sufficient
- Signal: green

## Stream Signals

- Code Architecture: **orange** — no pytest-archon enforcement, complexity hotspot in ConsoleFileRenderer::\_\_call\_\_ (CC=16)
- Code Quality: **green** — baseline clean, suppressions are legitimate, no critical-hiding
- Test Structure: **green** — 100% collection, 0 suppressions, healthy mock strategy, real E2E tests
- E2E Coverage + Production Reality: **green** — 84% PROVEN, 0 BROKEN, real structlog pipeline tested

## Test Automation

- Task runner: **tox** (env\_list: fix, cov, docs, build, 3.13)
- Single-command gate: **YES** — `tox -p` runs all quality gates
- Default coverage: **full** — no markers excluded, no tests skipped
- Signal: green

## Infrastructure Recommendations

- **Architecture enforcement**: Add pytest-archon with import direction rules (factory → config+core, core → config+colors). Low effort, high value.
  ```toml
  # tests/test_architecture.py
  # Enforce: factory imports from config+core (not reverse)
  # Enforce: core imports from config+colors (not from factory)
  ```

- **Complexity hotspot**: Decompose ConsoleFileRenderer::\_\_call\_\_ (CC=16) into focused sub-methods for level resolution, field stripping, timestamp formatting, and output rendering.

- **Factory coverage**: Add integration test that calls configure\_stdlib\_logging end-to-end with real logging output, verifying log messages appear at correct levels.

- **Unused markers**: Either use `@pytest.mark.integration` on E2E tests, or remove the marker definitions from pyproject.toml.

- **Radon config**: Remove `[tool.radon]` from pyproject.toml or add radon to dependency groups. Currently config exists but tool is not installed.

- **Duration tracking**: Add `--durations=10` to pytest addopts for CI regression detection.

## Critical Findings Fixed

1. **test\_exception\_logging.py**: Removed stale `stogger_infrastructure_files` fixture reference and `exclude_files` kwarg. Updated to use `stogger_config` fixture and filter source\_files via per-file-ignores config.

2. **pyproject.toml**: Replaced deprecated `infrastructure_files = ["core.py", "_colors.py"]` with `[tool.pytest-stogger.per-file-ignores]` section mapping both files to `["except-must-log", "complexity-needs-log"]`.

## Full CLI Test Trace

Full CLI test not triggered — stogger is a library (not a CLI tool) and existing E2E evidence is sufficient. All public API functions pass smoke tests with real execution.

## Code Volume

| File | Change |
|------|--------|
| tests/test\_exception\_logging.py | Updated: removed stale fixture, added per-file-ignores filtering |
| pyproject.toml | Updated: replaced infrastructure\_files with per-file-ignores section |

## Post-Fix Quality Gates

| Tool | Result |
|------|--------|
| ruff | 0 issues |
| ty | 0 errors |
| pytest | **118 passed** (0 failures, 0 errors) |
| E2E smoke | PASS (all public API functions importable and executable) |

## Recommendations

1. **Decompose ConsoleFileRenderer::\_\_call\_\_** — CC=16 is the only complexity hotspot. Extract sub-methods for level resolution, field stripping, and section rendering.
2. **Add pytest-archon** — enforce module dependency direction automatically.
3. **Add integration test for configure\_stdlib\_logging** — currently only tested via mocks.
4. **Remove unused markers** or apply `@pytest.mark.integration` to E2E tests.
5. **Remove `[tool.radon]` config** or install radon as a dependency.
6. **Consider marking test\_e2e\_single\_module\_app.py** with `@pytest.mark.integration` for discoverability.

## Raw Data Location

`.agents/tmp/quality/` — inventory/, baseline/, extreme/, analysis/, e2e/
