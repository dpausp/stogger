# Legacy Code Cleanup - Remove Technical Debt

Clean up legacy workarounds and compatibility issues that create technical debt.

## Description

*(Scope, Motivation, Research, Related work – no checkboxes here!)*

- Problem statement: Legacy code in core.py, systemd_integration.py, assistant.py etc. creates maintenance burden and technical debt.
- Why we want to solve it: Cleaner codebase, easier maintenance, fewer bugs.
- Research / references: Found through code search for legacy|workaround|compatibility|hack.
- Constraints: Don't break existing functionality, update tests, document breaking changes.

### Task Goal

- **Outcome we want**: All legacy workarounds removed, codebase cleaned.
- **Success criteria**: No legacy code left, all tests pass, no regressions.

______________________________________________________________________

## Tasks

*(Top-level numbered tasks with checkboxes, each with sub-structure – explicit, not vague)*

1. [ ] **Analyze legacy dependencies** – Identify dependencies on legacy features

   - **Context**: Before removing, need to know what's affected.

   - **Success criteria** (must be checked to finish task)

     - [ ] Tests found that use legacy features
     - [ ] Breaking changes documented

   - **Files to check/modify**

     - [ ] tests/test_core.py (Legacy init_logging tests)
     - [ ] tests/test_systemd_integration.py (cgroup hack tests)
     - [ ] tests/test_assistant.py (translations_file tests)

   - **Steps** (always action verbs, explicit order)

     - [ ] Search for tests that call init_logging_legacy
     - [ ] Search for tests that use cgroup hack
     - [ ] Search for tests that use translations_file parameter
     - [ ] Document all found dependencies

   - **Commit message hint**: "Analyze legacy code dependencies"

2. [ ] **Remove init_logging_legacy** – Clean up legacy compatibility in core.py

   - **Context**: init_logging has legacy support for old signatures, creating technical debt.

   - **Success criteria**

     - [ ] init_logging_legacy function removed
     - [ ] Legacy kwargs detection removed
     - [ ] New signature as default

   - **Files to check/modify**

     - [ ] src/nicestlog/core.py
     - [ ] src/nicestlog/__init__.py (remove export)
     - [ ] tests/test_core.py (remove or update legacy tests)

   - **Steps**

     - [ ] Remove init_logging_legacy function
     - [ ] Remove legacy kwargs logic from init_logging
     - [ ] Remove export from __init__.py
     - [ ] Update affected tests

   - **Commit message hint**: "Remove init_logging_legacy compatibility"

3. [ ] **Remove hacky cgroup code** – Clean up systemd integration

   - **Context**: Hacky /proc/self/cgroup reading is ugly and error-prone.

   - **Success criteria**

     - [ ] Hacky cgroup code removed
     - [ ] Alternative implementation or fallback

   - **Files to check/modify**

     - [ ] src/nicestlog/systemd_integration.py
     - [ ] tests/test_systemd_integration.py

   - **Steps**

     - [ ] Replace hacky cgroup code with clean alternative
     - [ ] Update tests

   - **Commit message hint**: "Remove hacky cgroup reading in systemd integration"

4. [ ] **Remove unused parameters** – translations_file and others

   - **Context**: translations_file in assistant.py is unused but kept for compatibility.

   - **Success criteria**

     - [ ] Unused parameters removed
     - [ ] CLI compatibility broken (documented)

   - **Files to check/modify**

     - [ ] src/nicestlog/assistant.py
     - [ ] src/nicestlog/cli.py (migration command)
     - [ ] tests/test_assistant.py

   - **Steps**

     - [ ] Remove translations_file parameter
     - [ ] Update CLI interface
     - [ ] Update tests

   - **Commit message hint**: "Remove unused translations_file parameter"

5. [ ] **Clean up TODO/FIXME patterns** – Clean up log reviewer

   - **Context**: Patterns for TODO/FIXME/XXX might be unnecessary.

   - **Success criteria**

     - [ ] Unnecessary patterns removed
     - [ ] Useful ones kept

   - **Files to check/modify**

     - [ ] src/nicestlog/log_reviewer.py
     - [ ] tests/test_log_reviewer.py

   - **Steps**

     - [ ] Evaluate patterns
     - [ ] Remove unnecessary ones
     - [ ] Update tests

   - **Commit message hint**: "Clean up TODO/FIXME patterns in log reviewer"

6. [ ] **Clean up generated code** – Remove TODO from advanced_assistant.py

   - **Context**: TODO in generated code is ugly.

   - **Success criteria**

     - [ ] TODO removed from generated code

   - **Files to check/modify**

     - [ ] src/nicestlog/advanced_assistant.py
     - [ ] tests/test_advanced_assistant.py

   - **Steps**

     - [ ] Remove TODO from generated code
     - [ ] Update tests

   - **Commit message hint**: "Remove TODO from generated code"

7. [ ] **Update tests and validate** – Run full test suite

   - **Context**: Ensure nothing is broken.

   - **Success criteria**

     - [ ] All tests pass
     - [ ] No regressions

   - **Files to check/modify**

     - [ ] tests/ (all affected tests)

   - **Steps**

     - [ ] Run uv run pytest
     - [ ] Analyze failures and fix
     - [ ] Check coverage

   - **Commit message hint**: "Update tests for legacy cleanup"