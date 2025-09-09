# Implement New Rules in Project - Focus on Legacy Code and Try-Except Avoidance

Implement the new rules for AI agents defined in AGENTS.md. Focus on avoiding legacy code and try-except blocks that suppress exceptions.

## Description

*(Scope, Motivation, Research, Related work – no checkboxes here!)*

- Problem statement: The project contains try-except blocks that suppress exceptions, as well as legacy code patterns that create technical debt.
- Why we want to solve it: Cleaner codebase, easier maintenance, fewer bugs, and better visibility of errors.
- Research / references: Analysis of the codebase for try-except blocks and legacy patterns has been completed and documented in:
  - docs/development/try_except_analysis.md
  - docs/development/cleanup_plan.md
  - docs/development/analysis_summary.md
- Constraints: Don't break existing functionality, update tests, document breaking changes.

### Analysis Results

#### Try-Except Blocks That Suppress Exceptions
1. **Bare except clauses with pass** in `src/nicestlog/assistant.py` - Silently ignores all exceptions during AST node processing in PrintToStructlogTransformer.visit_Assign method.
2. **Exception handling with continue** in `src/nicestlog/assistant.py` - Silently skips files that cannot be read during migration in migrate_directory function.
3. **Exception handling with pass** in `src/nicestlog/systemd_integration.py` - Silently ignores systemd detection failures in detect_systemd_environment function.

#### Legacy Code Patterns
1. **Compatibility methods** in `src/nicestlog/advanced_assistant.py` - Duplicate properties (`issues` and `changes`) for API compatibility.
2. **Legacy filtering method** in `src/nicestlog/linter.py` - Outdated approach to file filtering with hardcoded exclude directories.
3. **Compatibility fields** in `src/nicestlog/core.py` - Duplicate data fields for backward compatibility (event field duplication).
4. **Compatibility method** in `src/nicestlog/systemd_integration.py` - Method for standard logging handler compatibility.

#### Cleanup Plan Overview
The cleanup is divided into three phases:
1. **Phase 1**: Fix try-except suppression issues (1-2 days) - Replace suppressed exceptions with proper error handling and logging.
2. **Phase 2**: Remove legacy patterns with low/medium risk (2-3 days) - Remove legacy filtering, improve systemd integration.
3. **Phase 3**: Remove legacy patterns with high risk (3-5 days) - Remove compatibility methods and fields, document breaking changes.

#### Breaking Changes
- Removal of `issues` and `changes` properties in `advanced_assistant.py` (use `potential_issues` and `changes_made` instead)
- Removal of the "event" field duplication in `core.py` (use "_translated_msg" field instead)
- Removal of legacy filtering method in `linter.py`
- Removal of compatibility `emit` method in `systemd_integration.py`

### Task Goal

- **Outcome we want**: Remove all try-except blocks that suppress exceptions and clean up all identified legacy patterns.
- **Success criteria**: No more suppressed exceptions, all tests pass, no regressions.

______________________________________________________________________

## Tasks

*(Top-level numbered tasks with checkboxes, each with sub-structure – explicit, not vague)*

1. [ ] **Implement the cleanup** – Remove the identified anti-patterns

   - **Context**: Based on the completed analysis, the identified anti-patterns are removed step by step following the cleanup plan.

   - **Success criteria** (must be checked to finish task)

     - [ ] All identified try-except suppressions removed
     - [ ] All identified legacy patterns cleaned up
     - [ ] Tests updated
     - [ ] Documentation updated

   - **Files to check/modify**

     - [ ] src/nicestlog/assistant.py
     - [ ] src/nicestlog/systemd_integration.py
     - [ ] src/nicestlog/advanced_assistant.py
     - [ ] src/nicestlog/linter.py
     - [ ] src/nicestlog/core.py
     - [ ] Tests for the affected modules
     - [ ] Documentation

   - **Steps** (always action verbs, explicit order)

     - [ ] Phase 1: Fix try-except suppression issues - Replace suppressed exceptions with proper error handling and logging
     - [ ] Phase 2: Remove legacy patterns with low/medium risk - Remove legacy filtering, improve systemd integration
     - [ ] Phase 3: Remove legacy patterns with high risk - Remove compatibility methods and fields
     - [ ] Update tests for all modified code
     - [ ] Update documentation for breaking changes

   - **Commit message hint**: "Remove try-except suppression and legacy patterns"

1. [ ] **Test and validate** – Run the full test suite

   - **Context**: Ensure that no functionality has been compromised after the cleanup.

   - **Success criteria**

     - [ ] All tests pass
     - [ ] No regressions
     - [ ] Sufficient test coverage

   - **Files to check/modify**

     - [ ] tests/ (all affected tests)

   - **Steps**

     - [ ] Run `uv run pytest`
     - [ ] Analyze failures and fix
     - [ ] Check test coverage

   - **Commit message hint**: "Test and validate after cleaning up anti-patterns"
