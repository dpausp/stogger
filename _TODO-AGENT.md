# Implementation TODO - Fix Remaining 19 Test Failures

Fix the 19 remaining test failures to achieve a clean test suite.

## Description

- Problem statement: After fixing the logging initialization issue, 19 tests still fail, primarily in AST integration tests (check, fix, migrate commands) and some integration tests. These failures prevent a clean test run and indicate underlying issues in project analysis, command execution, and test expectations.
- Why we want to solve it: A clean test suite ensures code reliability, catches regressions early, validates functionality, and builds confidence in the codebase. Resolving these failures will improve overall code quality and maintainability.
- Research / references: Test failure logs, AGENTS.md rules (especially Rule 6: let it crash), existing test patterns in the codebase, project structure detection logic.
- Constraints: Must follow AGENTS.md rules, no legacy support, let exceptions crash with proper logging. Maintain existing functionality while fixing root causes.

### Task Goal

- **Outcome we want**: Zero test failures, all 444 tests pass.
- **Success criteria**: `uv run pytest` returns 0 failures, no regressions in existing functionality, proper error handling per Rule 6.

______________________________________________________________________

## Tasks

1. [ ] **Analyze and debug "Analysis failed" errors in AST integration tests**

   - **Context**: 14 tests in `test_cli_ast_integration.py` fail with SystemExit(1) or 2 due to "Analysis failed" in migrate/check/fix commands. Root cause appears to be issues in `analyze_project_for_agents` or project structure detection.

   - **Success criteria** (must be checked to finish task)

     - [ ] All "Analysis failed" errors resolved
     - [ ] AST commands (check, fix, migrate) execute successfully in tests
     - [ ] Project structure detection works correctly in test environments

   - **Files to check/modify**

     - [ ] `src/nicestlog/project_analyzer.py` (analyze_project_for_agents function)
     - [ ] `src/nicestlog/config.py` (detect_project_structure function)
     - [ ] `tests/test_cli_ast_integration.py` (test setup and expectations)

   - **Steps** (always action verbs, explicit order)

     - [ ] Debug why `analyze_project_for_agents` fails in test environments
     - [ ] Fix project structure detection for empty/temporary directories
     - [ ] Ensure proper initialization of logging and dependencies in tests
     - [ ] Update test expectations if behavior changes are intentional
     - [ ] Validate that fixes don't break existing functionality

   - **Commit message hint**: "fix: resolve analysis failures in AST integration tests"

1. [ ] **Fix integration test failures for journal, review, and dashboard**

   - **Context**: 4 tests in `test_cli_integration.py` fail with SystemExit(1), likely due to missing dependencies, configuration issues, or improper initialization.

   - **Success criteria** (must be checked to finish task)

     - [ ] All journal integration tests pass
     - [ ] All review integration tests pass
     - [ ] All dashboard integration tests pass
     - [ ] Proper handling of optional dependencies (systemd, flask)

   - **Files to check/modify**

     - [ ] `src/nicestlog/journal_viewer.py` (systemd integration)
     - [ ] `src/nicestlog/log_reviewer.py` (review functionality)
     - [ ] `src/nicestlog/web_dashboard.py` (dashboard functionality)
     - [ ] `tests/test_cli_integration.py` (test setup)

   - **Steps** (always action verbs, explicit order)

     - [ ] Check for missing optional dependencies in test environment
     - [ ] Ensure graceful handling when dependencies are unavailable
     - [ ] Fix initialization issues in integration commands
     - [ ] Update tests to handle optional features properly
     - [ ] Validate that fixes maintain backward compatibility

   - **Commit message hint**: "fix: resolve integration test failures for optional features"

1. [ ] **Fix early logging initialization test failure**

   - **Context**: `test_early_logging_initialization` in `test_core.py` expects exactly 1 log message but receives 2, indicating an issue with logging setup.

   - **Success criteria** (must be checked to finish task)

     - [ ] Early logging initialization produces exactly 1 message
     - [ ] Logging configuration is consistent across test environments
     - [ ] No duplicate or missing log messages

   - **Files to check/modify**

     - [ ] `src/nicestlog/core.py` (init_early_logging function)
     - [ ] `tests/test_core.py` (test expectations)

   - **Steps** (always action verbs, explicit order)

     - [ ] Debug why 2 messages are generated instead of 1
     - [ ] Fix logging initialization to produce correct number of messages
     - [ ] Ensure consistency between development and test environments
     - [ ] Update test assertions if behavior change is correct
     - [ ] Validate that logging still works properly in all scenarios

   - **Commit message hint**: "fix: correct early logging initialization message count"

1. [ ] **Validate all fixes and ensure no regressions**

   - **Context**: After fixing individual issues, need to ensure all tests pass and no new failures are introduced.

   - **Success criteria** (must be checked to finish task)

     - [ ] All 444 tests pass
     - [ ] No regressions in existing functionality
     - [ ] Code follows project conventions and AGENTS.md rules

   - **Files to check/modify**

     - [ ] All modified files from previous tasks
     - [ ] Test files for updated expectations

   - **Steps** (always action verbs, explicit order)

     - [ ] Run full test suite after each major fix
     - [ ] Check for any new failures or regressions
     - [ ] Validate that fixes don't violate AGENTS.md rules
     - [ ] Ensure proper error handling and logging per Rule 6
     - [ ] Update documentation if behavior changes significantly

   - **Commit message hint**: "test: validate all fixes and ensure clean test suite"
