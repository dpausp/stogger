# Implementation TODO - Fix Remaining Ruff Lint Errors

Fix the 286 remaining ruff lint errors after running `uv run doit fix`.

## Description

- Problem statement: After running `uv run doit fix`, 286 ruff lint errors remain across the codebase, primarily in `cli.py`, `project_analyzer.py`, `systemd_integration.py`, and `web_dashboard.py`. These errors violate code quality standards and must be systematically resolved.
- Why we want to solve it: Clean code with zero lint errors improves maintainability, reduces bugs, follows project conventions, and ensures consistent code quality across the entire codebase.
- Research / references: Ruff documentation for specific error codes, AGENTS.md Rule 6 (let it crash, no backwards compatibility), CONVENTIONS.md coding standards.
- Constraints: Must follow AGENTS.md rules, especially Rule 6 (no legacy support, let it crash). No backwards compatibility code allowed. Must maintain existing functionality while improving code quality.

### Task Goal

- **Outcome we want**: Zero ruff lint errors in the codebase, clean `uv run ruff check src/` execution.
- **Success criteria**: `uv run ruff check src/` returns no errors, all tests pass after fixes, code follows project conventions.

______________________________________________________________________

## Tasks

1. [ ] **Fix complexity violations (PLR series)** – reduce function complexity

   - **Context**: Multiple functions exceed complexity limits including PLR0911 (too many returns), PLR0912 (too many branches), PLR0913 (too many arguments), PLR0915 (too many statements)

   - **Success criteria** (must be checked to finish task)

     - [ ] All PLR0911 (too many returns) errors resolved
     - [ ] All PLR0912 (too many branches) errors resolved
     - [ ] All PLR0913 (too many arguments) errors resolved
     - [ ] All PLR0915 (too many statements) errors resolved

   - **Files to check/modify**

     - [ ] `src/nicestlog/cli.py` (lines 464, 765, 862, 1325, 1435, 1657, 1738, 1986, 2150)
     - [ ] `src/nicestlog/project_analyzer.py` (lines 791, 931)

   - **Steps** (always action verbs, explicit order)

     - [ ] Extract helper functions from complex functions
     - [ ] Use dataclasses for parameter grouping where applicable
     - [ ] Split large functions into smaller, focused functions
     - [ ] Reduce branching logic through early returns and guard clauses
     - [ ] Validate complexity metrics after refactoring

   - **Commit message hint**: "refactor: reduce function complexity per ruff PLR rules"

1. [x] **Fix logging violations (G201)** – use proper logging methods

   - **Context**: Multiple instances of using `.error(..., exc_info=True)` instead of `.exception(...)` and redundant `error=` parameters in `.exception()` calls

   - **Success criteria** (must be checked to finish task)

     - [x] All G201 errors resolved by replacing with `.exception()`
     - [x] All redundant `error=` parameters removed from `.exception()` calls
     - [x] Consistent logging patterns across codebase

   - **Files to check/modify**

     - [ ] `src/nicestlog/cli.py` (lines 1477, 1727, 2279, 2353, 2413, 2534, 2613)

   - **Steps** (always action verbs, explicit order)

     - [x] Replace `logger.error(..., exc_info=True)` with `logger.exception(...)`
     - [x] Remove redundant `error=` parameters from `.exception()` calls
     - [x] Remove `exc_info=True` parameter from error calls
     - [x] Verify logging output remains consistent

   - **Commit message hint**: "fix: use logger.exception() instead of error with exc_info"

1. [x] **Fix logging f-string violations (G004)** – replace f-strings in logging

   - **Context**: Multiple instances of using f-strings in logging statements which can impact performance and log parsing

   - **Success criteria** (must be checked to finish task)

     - [x] All G004 errors resolved by replacing f-strings with proper logging
     - [x] Consistent logging patterns across codebase

   - **Files to check/modify**

     - [x] `src/nicestlog/config.py` (lines 62, 64, 98, 102, 109, 112, 142, 145, 152)

   - **Steps** (always action verbs, explicit order)

     - [x] Replace f-string logging with structured logging or format strings
     - [x] Ensure log parsing compatibility is maintained
     - [x] Verify logging output remains informative

   - **Commit message hint**: "fix: replace f-strings in logging statements"

1. [ ] **Fix security violations (S602, S311, S106, S112)** – address security issues

- **Context**: Security issues including subprocess shell usage, hardcoded secrets, weak random generation, and exception suppression

- **Success criteria** (must be checked to finish task)

  - [ ] All S602 (subprocess shell) errors resolved
  - [ ] All S311 (weak random) errors resolved
  - [ ] All S106 (hardcoded password) errors resolved
  - [ ] All S112 (try-except-continue) errors resolved

- **Files to check/modify**

  - [ ] `src/nicestlog/cli.py` (lines 1548, 1564, 1582, 1893, 1896)
  - [ ] `src/nicestlog/web_dashboard.py` (lines 460, 461, 468, 469, 470, 473)
  - [ ] `src/nicestlog/project_analyzer.py` (line 702)

- **Steps** (always action verbs, explicit order)

  - [ ] Replace subprocess shell=True with safer alternatives
  - [ ] Use secrets module for cryptographic random generation
  - [ ] Replace hardcoded passwords with placeholders or constants
  - [ ] Add proper logging to exception handling per Rule 6

- **Commit message hint**: "fix: resolve security violations per ruff S-series rules"

1. [ ] **Fix magic value violations (PLR2004)** – replace magic numbers with constants

   - **Context**: Multiple magic numbers used in comparisons throughout the codebase

   - **Success criteria** (must be checked to finish task)

     - [ ] All PLR2004 errors resolved with named constants
     - [ ] Constants defined at module level with descriptive names

   - **Files to check/modify**

     - [ ] `src/nicestlog/project_analyzer.py` (lines 709, 711, 778, 902, 903, 908)

   - **Steps** (always action verbs, explicit order)

     - [ ] Define module-level constants for all magic numbers
     - [ ] Replace magic values in comparisons with named constants
     - [ ] Use descriptive constant names that explain their purpose

   - **Commit message hint**: "refactor: replace magic numbers with named constants"

1. [ ] **Fix performance violations (PERF401)** – optimize list operations

   - **Context**: Multiple instances of inefficient list operations that can be replaced with list.extend

   - **Success criteria** (must be checked to finish task)

     - [ ] All PERF401 errors resolved with list.extend
     - [ ] Maintain existing functionality and behavior

   - **Files to check/modify**

     - [ ] `src/nicestlog/cli.py` (lines 737, 2314)
     - [ ] `src/nicestlog/project_analyzer.py` (lines 675, 769)

   - **Steps** (always action verbs, explicit order)

     - [ ] Replace for loops with list.extend where applicable
     - [ ] Use list comprehensions for filtered extends
     - [ ] Verify performance improvements maintain correctness

   - **Commit message hint**: "perf: optimize list operations with list.extend"

1. [ ] **Fix style and naming violations** – code style improvements

   - **Context**: Various style issues including FBT001 (boolean flags), N806 (variable naming), SIM108 (ternary operators), RUF012 (mutable class attributes)

   - **Success criteria** (must be checked to finish task)

     - [ ] All FBT001 (boolean flags) errors resolved
     - [ ] All N806 (variable naming) errors resolved
     - [ ] All SIM108 (ternary operator) errors resolved
     - [ ] All RUF012 (mutable class attributes) errors resolved

   - **Files to check/modify**

     - [ ] `src/nicestlog/cli.py` (lines 541, 2016, 2190, 2266)
     - [ ] `src/nicestlog/systemd_integration.py` (line 37)

   - **Steps** (always action verbs, explicit order)

     - [ ] Convert boolean positional arguments to keyword-only
     - [ ] Fix variable naming to follow conventions
     - [ ] Replace if-else blocks with ternary operators where appropriate
     - [ ] Add ClassVar annotations to mutable class attributes

   - **Commit message hint**: "style: fix naming and style violations"

1. [ ] **Fix exception handling violations (BLE001)** – follow crash-first principle

   - **Context**: Blind exception catching violates AGENTS.md Rule 6 (let it crash)

   - **Success criteria** (must be checked to finish task)

     - [ ] All BLE001 (blind exception) errors resolved
     - [ ] Exception handling follows crash-first principle with structured logging

   - **Files to check/modify**

     - [ ] `src/nicestlog/project_analyzer.py` (line 702)

   - **Steps** (always action verbs, explicit order)

     - [ ] Replace blind `except Exception:` with specific exceptions
     - [ ] Add structured logging before re-raising exceptions
     - [ ] Ensure exceptions crash properly per Rule 6

   - **Commit message hint**: "fix: improve exception handling per Rule 6 crash-first"

1. [ ] **Fix datetime violations (DTZ005)** – proper timezone handling

   - **Context**: Datetime operations without timezone awareness

   - **Success criteria** (must be checked to finish task)

     - [ ] All DTZ005 errors resolved with timezone parameters
     - [ ] Consistent timezone handling across codebase

   - **Files to check/modify**

     - [ ] `src/nicestlog/project_analyzer.py` (line 923)

   - **Steps** (always action verbs, explicit order)

     - [ ] Replace `datetime.now()` with `datetime.now(timezone.utc)`
     - [ ] Ensure consistent timezone usage across the project

   - **Commit message hint**: "fix: add timezone awareness to datetime operations"

1. [ ] **Fix docstring violations (D401)** – documentation standards

   - **Context**: Docstring format issues with imperative mood

   - **Success criteria** (must be checked to finish task)

     - [ ] All D401 (imperative mood) errors resolved
     - [ ] Docstrings follow project conventions

   - **Files to check/modify**

     - [ ] `src/nicestlog/project_analyzer.py` (line 931)

   - **Steps** (always action verbs, explicit order)

     - [ ] Rewrite docstrings in imperative mood
     - [ ] Validate docstring format compliance

   - **Commit message hint**: "docs: fix docstring format violations"

1. [ ] **Fix line length violations (E501)** – code formatting

   - **Context**: Lines exceeding 120 character limit

   - **Success criteria** (must be checked to finish task)

     - [ ] All E501 errors resolved with proper line breaks
     - [ ] Code remains readable and properly formatted

   - **Files to check/modify**

     - [ ] `src/nicestlog/project_analyzer.py` (line 905)

   - **Steps** (always action verbs, explicit order)

     - [ ] Break long lines at appropriate points
     - [ ] Maintain code readability and logical grouping

   - **Commit message hint**: "style: fix line length violations"
