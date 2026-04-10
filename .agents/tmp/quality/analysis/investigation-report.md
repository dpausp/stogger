# Quality Meta-Audit Investigation Report

**Date:** 2026-04-10
**Target:** stogger project (5-package uv workspace)
**Scope:** Full codebase quality meta-audit across 4 streams

---

## Stream A: Code Architecture

**Signal: ORANGE**

### Architecture Enforcement: NONE

- `test_architecture.py` does **not exist**. Zero architecture rules enforced.
- Architecture is documented via workspace structure but has no automated guard.
- The workspace split is validated only by `test_workspace_split.py` (27 tests checking package layout, imports, exports) — this provides structural coverage but is not pytest-archon.

### Cyclomatic Complexity Hotspots

434 blocks analyzed. Average: A (4.97). Two Grade F functions:

| Function | Grade | File | Root Cause |
|----------|-------|------|------------|
| `lint_directory` | **F** | `linter.py:619` | 150-line function with backward-compat branching, dual code paths (project_structure vs legacy), format detection, per-file analysis loop, table rendering |
| `_detect_issues` | **F** | `log_statement_analyzer.py:263` | ~140 lines of issue detection with triple backward-compat dispatch (options object, old positional, old kwargs), 12 sequential issue checks |

Grade D hotspots:
- `ConsoleFileRenderer.__call__` (core.py:174) — rendering dispatcher
- `JournalViewer.query_journal` (journal_viewer.py:232)
- `ProjectAnalyzer._generate_recommendation` (project_analyzer.py:801)
- `CLIOutputToStructlogTransformer.detect_cli_output_call` (cli_output_transformer.py:131)

### Why Grade F Functions Are Complex

**`lint_directory`**: Maintains backward compatibility with two different call signatures (LintOptions object vs positional args). Has parallel code paths for project-structure-aware filtering vs legacy glob exclusion. The function also handles output formatting (table/json/toml), per-file statistics aggregation, and log statement analysis — at least 4 responsibilities in one function.

**`_detect_issues`**: Triple dispatch for backward compatibility (options object, old positional unpacking, old kwargs). The 12 issue checks themselves are each reasonable, but the dispatch adds significant branching before the real logic starts.

**Verdict:** Both F-grade functions suffer from accumulated backward compatibility shims layered on top of their core logic. The complexity is not inherent — it's accreted.

---

## Stream B: Code Quality — Tool Tolerance Audit

### Ruff

| Metric | Value |
|--------|-------|
| Baseline errors (project config) | 4 (all in `vendor/mydevtools/`) |
| Extreme errors (full ruleset) | 1,056 total, 735 in `packages/` |
| Signal | **ORANGE** |

**Baseline analysis:** Project code passes ruff cleanly (0 errors in `packages/`). The 4 baseline errors are all in vendored code (`vendor/mydevtools/task_helpers.py`) — line-too-long and unused loop variable. Acceptable.

**Extreme analysis (top error codes in `packages/`):**

| Rule | Count | Category | Assessment |
|------|-------|----------|------------|
| DOC201 (return not documented) | 186 | Documentation | QUESTIONABLE — doc strictness |
| E402 (import not at top) | 24 | Style | LEGITIMATE — conditional imports for optional deps |
| ANN001 (missing arg annotation) | 23 | Typing | LEGITIMATE — structlog processor signatures use `_` and `__` |
| CPY001 (missing copyright) | 22 | Documentation | QUESTIONABLE — style preference |
| PLC2701 (private import) | 18 | Design | LEGITIMATE — `_colors` is internal API |
| D107/D102/D103 (missing docstrings) | 31 | Documentation | QUESTIONABLE |
| ANN003/ANN204 (missing type annotations) | 23 | Typing | LEGITIMATE — structlog callback conventions |
| S603 (subprocess call) | 6 | Security | CRITICAL-HIDING — suppressed but worth reviewing |

**CRITICAL-HIDING findings:** 6 `S603 subprocess` warnings suppressed by not being selected. The project calls subprocess indirectly via some tooling. Low risk since this is a developer tool, not a web service.

### Ty (Type Checker)

| Metric | Value |
|--------|-------|
| Total diagnostics | 50 |
| Signal | **ORANGE** |

**Error categories:**

| Category | Count | Severity | Assessment |
|----------|-------|----------|------------|
| `unresolved-import` (systemd, eliot) | 3 | LOW | Optional dependencies — `type: ignore[import-not-found]` already present |
| `invalid-assignment` (None fallbacks) | 9 | MEDIUM | Pattern: `try: import X except: X = None` — works at runtime but type-unsafe |
| `unsupported-operator` (color constants) | 8 | LOW | `_colors.py` constants have `Literal[1, ""]` union type from colorama fallback |
| `unresolved-attribute` (journal) | 6 | LOW | Optional systemd deps |
| `invalid-argument-type` (AST) | 5 | MEDIUM | AST node type narrowing issues |
| `unknown-argument` (console.print) | 2 | **HIGH** | `console.print(reason=..., _replace_msg=...)` — passing kwargs to Rich's `print()` that it doesn't accept |

**HIGH severity finding:** `linter.py:982-983` passes `reason=` and `_replace_msg=` as keyword arguments to `console.print()`. Rich's `print()` doesn't accept these. This is a runtime bug — those kwargs are silently ignored by `**objects` catching them. The linter is trying to log via structlog conventions through a Rich console call.

### Type Ignore Analysis

19 `type: ignore` comments found. **All include error codes** — no bare ignores. Well-disciplined suppression usage.

Distribution:
- `i18n_check.py`: 6 (dict.get returning object, not typed)
- `systemd_integration.py`: 2 (import-not-found for optional dep)
- `journal_viewer.py`: 1 (import-not-found)
- `eliot_integration.py`: 1 (import-untyped)
- `cli.py`: 3 (assignment, misc)
- `assistant.py`: 1 (attr-defined on AST node)
- `advanced_assistant.py`: 3 (return-value, arg-type for AST)

### Noqa Comments

**Zero `noqa` comments** in the entire project. Clean.

### Tool Tolerance Summary

| Tool | Baseline Issues | Extreme Issues (packages) | Signal |
|------|----------------|---------------------------|--------|
| Ruff | 4 (vendor only) | 735 | ORANGE — heavy suppression via rule selection |
| Ty | 50 | N/A | ORANGE — mostly optional deps, 1 real bug |
| Tox | FAIL (all 3 envs) | N/A | RED — cannot detect project name |

**Tox is broken.** All three environments fail with "Could not detect project name." The root `pyproject.toml` is a workspace manifest without `[project]` section — tox cannot find a target. This is a workspace configuration issue.

---

## Stream C: Test Structure

**Signal: ORANGE**

### Test Inventory

| Metric | Value |
|--------|-------|
| Total tests | 516 |
| Slow tests | 2 (pexpect interactive) |
| Test files | 26 |
| Source modules (stoggertools) | 12 |

### Mock Ratio: CRITICAL

| Metric | Value |
|--------|-------|
| Test files using mocks | 13 of 26 (50%) |
| Total mock references | 112 |
| Mock references with `spec=` or `autospec=` | **2 of 112 (1.8%)** |
| Mock ratio (files with mocks / all test files) | 50% |
| Slippery mock ratio (unspecced / total) | **98.2%** |

**RED FLAG — Slippery mocks.** 98.2% of mock usages have no `spec=` or `autospec=True`. These mocks silently accept any attribute access and any call, hiding real API breakage.

**Heaviest mock consumers:**

| Test File | Mock References | What It Tests |
|-----------|----------------|---------------|
| `test_journal_viewer.py` | 89 | Journal querying/formating (systemd unavailable in CI) |
| `test_cli_ast_integration.py` | 66 | CLI commands with AST transforms |
| `test_eliot_integration.py` | 30 | Eliot context managers (eliot unavailable in CI) |
| `test_cli.py` | 28 | CLI parameter validation |
| `test_cli_integration.py` | 16 | CLI integration scenarios |

**Justification for heavy mocking:** `systemd`, `eliot`, and `Flask` are optional dependencies not installed in the test environment. Mocking these is legitimate — there's no way to test journal queries without systemd, no way to test eliot actions without eliot.

**But:** `test_cli_ast_integration.py` mocks the core `AdvancedAssistant` and transformation results extensively (66 references). This tests that the CLI wiring calls the right functions, but provides zero confidence that the AST transformations actually work correctly. The actual transformation logic IS tested in `test_advanced_assistant.py` (18 tests) and `test_assistant.py` (4 tests) — those use real AST code, not mocks.

### Test Suppressions

| Type | Count | Detail |
|------|-------|--------|
| `skipif` (Flask unavailable) | 3 | Legitimate — optional dep |
| `skip` (eliot not installed) | 1 | Legitimate — optional dep |
| `skip` (log reviewer unsupported) | 3 | **SUSPICIOUS** — entire module skipped |

**3 tests permanently skipped in `test_log_reviewer.py`** with `@pytest.mark.skip("Log reviewer is currently unsupported")`. These are class-level skips that disable entire test classes (lines 14, 37, 437). The log_reviewer module is in the codebase and exported publicly but has no working tests.

### Source-to-Test Mapping

| Source Module | Test Coverage | Gap |
|---------------|---------------|-----|
| `advanced_assistant.py` | `test_advanced_assistant.py` (18 tests) | Covered |
| `assistant.py` | `test_assistant.py` (4 tests) | Covered |
| `cli.py` | `test_cli.py`, `test_cli_ast_integration.py`, `test_cli_integration.py`, `test_cli_demos.py`, `test_cli_more_demos.py`, `test_cli_pexpect.py` | Covered (6 files) |
| `cli_output_transformer.py` | `test_cli_output_transformer.py` (34 tests) | Covered |
| `config.py` | `test_config.py` (9 tests) | Covered |
| `core.py` | `test_core.py` (8 tests) | Covered |
| `factory.py` | `test_factory.py` (16 tests) | Covered |
| `i18n.py` | `test_i18n_simple.py` (7 tests) | Covered |
| `i18n_check.py` | `test_i18n_check.py` (5 tests) | Covered |
| `interactive_transformer.py` | `test_interactive_transformer.py` (17 tests) | Covered |
| `linter.py` | `test_linter_simple.py`, `test_linter_additional.py`, `test_linter_wrapper_detection.py` | Covered |
| `live_editor.py` | **NO TEST FILE** | **GAP** |
| `log_reviewer.py` | `test_log_reviewer.py` (SKIPPED) | **BROKEN** |
| `log_statement_analyzer.py` | `test_log_statement_analyzer.py` (40 tests) | Covered |
| `project_analyzer.py` | **NO TEST FILE** | **GAP** |

**Gaps:**
1. **`live_editor.py`** — `LiveCodeEditor` class with 0 tests. Public API exported in `__all__`.
2. **`project_analyzer.py`** — `ProjectAnalyzer` class with 0 tests. Public API exported in `__all__`. Grade D complexity in `_generate_recommendation`.

### Integration Test Marker Usage

The `@pytest.mark.integration` marker is defined in `pyproject.toml` but **zero tests use it**. There's no way to distinguish unit from integration tests via markers.

The `test_cli_integration.py` file exists with 16 tests that run CLI commands via subprocess, but they're not marked as integration tests.

---

## Stream D: E2E Coverage + Production Reality

**Signal: GREEN**

### Smoke Test Results

12/12 CLI commands pass with exit code 0. All entry points functional.

### Entry Point Coverage Table

| Entry Point | Type | E2E Status | Test Evidence |
|-------------|------|------------|---------------|
| `stoggertools --help` | CLI | **PROVEN** | Smoke test PASS, `test_help_command` |
| `stoggertools check` | CLI subcommand | **PROVEN** | Smoke test PASS, `test_cli_ast_integration.py` (4 tests), `test_linter_simple.py` (8 tests), `test_linter_additional.py` (4 tests) |
| `stoggertools migrate` | CLI subcommand | **PROVEN** | Smoke test PASS, `test_cli_ast_integration.py` (7 migrate tests) |
| `stoggertools docs` | CLI subcommand | **PROVEN** | Smoke test PASS, `test_docs_serve.py` (6 tests), `test_cli_pexpect.py` (2 interactive) |
| `stoggertools docs-serve` | CLI subcommand | **PROVEN** | `test_docs_serve.py` (6 tests) |
| `stoggertools init` | CLI subcommand | **PROVEN** | Smoke test PASS, `test_cli_integration.py::TestInitConfigIntegration`, `test_cli.py::TestInitConfig` |
| `stoggertools tools generate-service` | CLI subcommand | **PROVEN** | `test_cli_integration.py::TestGenerateServiceIntegration`, `test_cli.py::TestGenerateServiceCommand` |
| `stoggertools tools check-advanced` | CLI subcommand | **SUSPECTED** | No dedicated test; shares code path with `check` |
| `stoggertools tools review` | CLI subcommand | **SUSPECTED** | `test_cli_integration.py::TestReviewIntegration` exists but `LogQualityReviewer` tests are **skipped** |
| `stoggertools tools journal` | CLI subcommand | **SUSPECTED** | `test_cli_integration.py::TestJournalIntegration` — mocked (no systemd) |
| `stoggertools tools dashboard` | CLI subcommand | **SUSPECTED** | `test_cli_integration.py::TestDashboardIntegration` — requires Flask, `skipif` guarded |
| `stoggertools tools demo` | CLI subcommand | **PROVEN** | Smoke test PASS, `test_cli_demos.py` (4 tests), `test_cli_more_demos.py` (4 tests) |
| `stoggertools tools i18n check` | CLI subcommand | **PROVEN** | `test_cli.py::TestCliI18nCheck`, `test_cli.py::TestCliI18nFailOnExtra` |
| `python -m stoggertools` | Script | **PROVEN** | Smoke test PASS |
| `stogger.init_logging()` | Library API | **SUSPECTED** | `test_config.py` and `test_core.py` test setup but not full integration |
| `stogger.create_pii_processor()` | Library API | **PROVEN** | `test_pii_scrubber.py` (30 tests) |
| `stogger_web.run_dashboard()` | Library API | **UNKNOWN** | Flask-dependent, no real test |
| `stogger_systemd.setup_systemd_logging()` | Library API | **SUSPECTED** | `test_systemd_integration.py` — partially mocked |
| `stogger_eliot.setup_eliot_logging()` | Library API | **SUSPECTED** | `test_eliot_integration.py` — mostly mocked |

### Integration Test Exclusion

No tests use `@pytest.mark.integration`. The `integration` marker exists but is unused. All 516 tests run by default — no integration tests are excluded from default runs.

### Paths with Only Mock Tests

- `stogger_web.web_dashboard` — Flask unavailable, entire dashboard tested via mocks
- `stogger_eliot.eliot_integration` — Eliot unavailable, action/context managers tested via mocks
- `stogger_systemd.journal_viewer` — systemd unavailable, journal queries tested via mocks

These are **justified** mock-only paths (optional dependencies). The risk is API drift between mock assumptions and actual library behavior.

---

## Tool Tolerance Audit

| Tool | Baseline Issues | Extreme Issues (packages) | Signal |
|------|----------------|---------------------------|--------|
| Ruff | 4 (vendor only) | 735 | ORANGE |
| Ty | 50 | N/A | ORANGE |
| Tox | FAIL (all envs) | N/A | RED |

---

## Test Structure Report

- **Total tests:** 516
- **Mock ratio:** 50% of test files use mocks
- **Slippery mock ratio:** 98.2% of mocks lack `spec=` or `autospec=`
- **Distribution estimate:** ~380 unit tests, ~130 mock-dependent tests, ~6 integration tests
- **Permanently skipped:** 3 test classes in `test_log_reviewer.py`
- **Missing test files:** `live_editor.py`, `project_analyzer.py`
- **Slow tests:** 2 (pexpect)

---

## Synthesis

**Overall signal: ORANGE**

**Full CLI test needed:** NO — smoke test covers 12/12 commands. The CLI surface is well-tested.

### Critical Findings

1. **Tox is broken** (RED) — All 3 environments fail with "Could not detect project name." Workspace root has no `[project]` section. Tox needs per-package configuration or `requires = [".[dev]"]` with a target package.

2. **98.2% slippery mocks** (RED) — 110 of 112 mock references have no `spec=` or `autospec=True`. API contract drift will not be caught by tests. Highest density in `test_journal_viewer.py` (89 refs) and `test_cli_ast_integration.py` (66 refs).

3. **2 untested public modules** (ORANGE) — `live_editor.py` and `project_analyzer.py` are exported in `__all__` with zero test coverage. `project_analyzer.py` has a Grade D complexity function.

4. **3 permanently skipped test classes** (ORANGE) — `test_log_reviewer.py` has 3 `@pytest.mark.skip("Log reviewer is currently unsupported")` at class level. If unsupported, the source module should be removed or the tests fixed.

5. **1 real type bug** (ORANGE) — `linter.py:982-983` passes `reason=` and `_replace_msg=` to `console.print()` which silently ignores them. The linter intends to use structlog-style kwargs but calls Rich's print instead.

6. **No architecture enforcement** (ORANGE) — No `test_architecture.py` exists. Package structure is validated by `test_workspace_split.py` but there are no layer or dependency rules.

7. **2 Grade F complexity functions** (ORANGE) — `lint_directory` and `_detect_issues` both suffer from backward-compatibility dispatch layered over core logic. The complexity is accreted, not inherent.

### Non-Critical Findings

- Ruff baseline is clean (0 errors in packages). Extreme mode shows 735 errors dominated by documentation rules (DOC201: 186) and annotation rules — quality strictness, not bugs.
- Type ignores are well-disciplined: all 19 have error codes, no bare ignores.
- Zero noqa comments.
- E2E smoke test: 12/12 PASS.
