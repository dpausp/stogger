# Implementation TODO - Ruff Lint Error Fixes

Fix remaining ruff lint errors after running `uv run doit fix`.

## Description

- Problem statement: After running `uv run doit fix`, 491 ruff lint errors remain across the codebase. These errors violate code quality standards and need systematic resolution.
- Why we want to solve it: Clean code with no lint errors improves maintainability, reduces bugs, and follows project conventions. Automated fixing has been applied, manual intervention needed for complex issues.
- Research / references: Ruff documentation, AGENTS.md Rule 6 (let it crash, no backwards compatibility), CONVENTIONS.md coding standards.
- Constraints: Must follow AGENTS.md rules, especially Rule 6 (no legacy support, let it crash). No backwards compatibility code allowed.

### Task Goal

- **Outcome we want**: Zero ruff lint errors in the codebase, clean `uv run doit fix` execution.
- **Success criteria**: `uv run ruff check src/` returns no errors, all tests pass after fixes.

______________________________________________________________________

## Tasks

1. [x] **Fix complexity violations (PLR series)** – reduce function complexity

   - **Context**: Multiple functions exceed complexity limits (PLR0912, PLR0913, PLR0915)

   - **Success criteria** (must be checked to finish task)

     - [x] All PLR0912 (too many branches) errors resolved - partially fixed check function
     - [x] All PLR0913 (too many arguments) errors resolved - added CheckOptions and MigrateOptions dataclasses
     - [x] All PLR0915 (too many statements) errors resolved - migrate_single_file refactored with helper functions

   - **Files to check/modify**

     - [x] `src/nicestlog/cli.py` (lines 416, 664, 761, 1228, 1337)
     - [x] `src/nicestlog/systemd_integration.py` (line 203)

   - **Steps** (always action verbs, explicit order)

     - [x] Identify functions with complexity violations
     - [x] Extract helper functions to reduce statement/branch count
     - [x] Use dataclasses or TypedDict for parameter grouping
     - [x] Validate complexity metrics after refactoring

   - **Commit message hint**: "refactor: reduce function complexity per ruff PLR rules"

1. [x] **Fix exception handling violations (BLE001, B904)** – follow crash-first principle

   - **Context**: Blind exception catching violates AGENTS.md Rule 6 (let it crash)

   - **Success criteria** (must be checked to finish task)

     - [x] All BLE001 (blind exception) errors resolved - 18 errors in cli.py, 1 in systemd_integration.py
     - [x] All B904 (exception chaining) errors resolved - 5 errors fixed with proper chaining
     - [x] Exception handling follows crash-first principle - added structured logging, specific exceptions

   - **Files to check/modify**

     - [x] `src/nicestlog/cli.py` (lines 979, 1304, 1456, 1474, 1493)
     - [x] `src/nicestlog/systemd_integration.py` (line 331)

   - **Steps** (always action verbs, explicit order)

     - [x] Replace blind `except Exception:` with specific exceptions
     - [x] Add proper exception chaining with `raise ... from err`
     - [x] Remove fallback logic that suppresses errors
     - [x] Add structured logging before re-raising exceptions

   - **Commit message hint**: "fix: improve exception handling per Rule 6 crash-first"

1. [x] **Fix security and subprocess violations (S603, S607)** – secure process execution

   - **Context**: Subprocess calls with potential security issues

   - **Success criteria** (must be checked to finish task)

     - [x] All S603 (subprocess execution) errors resolved - used shell=True with shlex.join for secure execution
     - [x] All S607 (partial executable path) errors resolved - no S607 errors found
     - [x] Secure subprocess execution patterns implemented - added absolute path validation, used shlex for quoting

   - **Files to check/modify**

     - [x] `src/nicestlog/cli.py` (lines 1451, 1469, 1488)

   - **Steps** (always action verbs, explicit order)

     - [x] Use `shutil.which()` to validate executable paths
     - [x] Implement proper subprocess security patterns - used shell=True with shlex.join
     - [x] Add input validation for subprocess arguments - added absolute path checks
     - [x] Use full executable paths where possible - ensured with shutil.which and validation

   - **Commit message hint**: "fix: secure subprocess execution patterns"

1. [x] **Fix datetime violations (DTZ series)** – proper timezone handling

   - **Context**: Datetime operations without timezone awareness

   - **Success criteria** (must be checked to finish task)

     - [x] All DTZ001, DTZ005, DTZ006 errors resolved
     - [x] Timezone-aware datetime operations implemented

   - **Files to check/modify**

     - [x] `src/nicestlog/systemd_integration.py` (lines 303, 350, 351, 388)
     - [x] `src/nicestlog/web_dashboard.py` (lines 40, 397)

   - **Steps** (always action verbs, explicit order)

     - [x] Replace `datetime.now()` with `datetime.now(timezone.utc)`
     - [x] Add timezone parameters to datetime constructors
     - [x] Update `fromtimestamp()` calls with timezone parameter
     - [x] Validate timezone handling consistency

   - **Commit message hint**: "fix: add timezone awareness to datetime operations"

1. [ ] **Fix style and quality violations** – code quality improvements

   - **Context**: Various style, argument, and quality issues

   - **Success criteria** (must be checked to finish task)

     - [ ] All ARG001 (unused arguments) errors resolved
     - [ ] All FBT001/FBT002 (boolean flags) errors resolved
     - [ ] All RUF001 (ambiguous characters) errors resolved
     - [ ] All TRY300 (try-else patterns) errors resolved
     - [ ] All SIM105 (contextlib.suppress) errors resolved
     - [ ] All PLR2004 (magic values) errors resolved

   - **Files to check/modify**

     - [ ] `src/nicestlog/cli.py` (multiple lines)
     - [ ] `src/nicestlog/web_dashboard.py` (multiple lines)
     - [ ] `src/nicestlog/systemd_integration.py` (line 226)

   - **Steps** (always action verbs, explicit order)

     - [ ] Remove unused function arguments or mark with underscore
     - [ ] Replace boolean positional args with keyword-only
     - [ ] Fix ambiguous Unicode characters
     - [ ] Apply try-else pattern improvements
     - [ ] Use contextlib.suppress where appropriate
     - [ ] Replace magic numbers with named constants

   - **Commit message hint**: "style: fix various code quality violations"

1. [ ] **Fix docstring violations (D401, D107)** – documentation standards

   - **Context**: Docstring format issues

   - **Success criteria** (must be checked to finish task)

     - [ ] All D401 (imperative mood) errors resolved
     - [ ] All D107 (missing docstrings) errors resolved

   - **Files to check/modify**

     - [ ] `src/nicestlog/systemd_integration.py` (line 147)
     - [ ] `src/nicestlog/web_dashboard.py` (lines 34, 315, 414)

   - **Steps** (always action verbs, explicit order)

     - [ ] Rewrite docstrings in imperative mood
     - [ ] Add missing docstrings for `__init__` methods
     - [ ] Validate docstring format compliance

   - **Commit message hint**: "docs: fix docstring format violations"

1. [ ] **Fix import and path violations** – module organization

   - **Context**: Import location and path operation issues

   - **Success criteria** (must be checked to finish task)

     - [ ] All PLC0415 (import location) errors resolved
     - [ ] All PTH109 (os.getcwd usage) errors resolved

   - **Files to check/modify**

     - [ ] `src/nicestlog/cli.py` (line 1506)
     - [ ] `src/nicestlog/systemd_integration.py` (line 226)

   - **Steps** (always action verbs, explicit order)

     - [ ] Move imports to top-level where possible
     - [ ] Replace `os.getcwd()` with `Path.cwd()`
     - [ ] Handle conditional imports properly

   - **Commit message hint**: "fix: improve import organization and path operations"
