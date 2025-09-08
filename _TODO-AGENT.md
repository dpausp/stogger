# Implement New Rules in Project - Focus on Legacy Code and Try-Except Avoidance

Implement the new rules for AI agents defined in AGENTS.md. Focus on avoiding legacy code and try-except blocks that suppress exceptions.

## Description

*(Scope, Motivation, Research, Related work – no checkboxes here!)*

- Problem statement: The project contains try-except blocks that suppress exceptions, as well as legacy code patterns that create technical debt.
- Why we want to solve it: Cleaner codebase, easier maintenance, fewer bugs, and better visibility of errors.
- Research / references: Analysis of the codebase for try-except blocks and legacy patterns.
- Constraints: Don't break existing functionality, update tests, document breaking changes.

### Task Goal

- **Outcome we want**: Remove all try-except blocks that suppress exceptions and clean up all identified legacy patterns.
- **Success criteria**: No more suppressed exceptions, all tests pass, no regressions.

______________________________________________________________________

## Tasks

*(Top-level numbered tasks with checkboxes, each with sub-structure – explicit, not vague)*

1. [x] **Analyze try-except blocks** – Identify blocks that suppress exceptions

   - **Context**: Try-except blocks that ignore or suppress exceptions prevent early detection of errors.

   - **Success criteria** (must be checked to finish task)

     - [x] All try-except blocks in the codebase identified
     - [x] Blocks classified (suppressing vs. correctly handled)
     - [x] Documentation of found patterns

   - **Files to check/modify**

     - [x] src/nicestlog/core.py
     - [x] src/nicestlog/systemd_integration.py
     - [x] src/nicestlog/assistant.py
     - [x] src/nicestlog/cli.py
     - [x] src/nicestlog/web_dashboard.py
     - [x] src/nicestlog/project_analyzer.py
     - [x] src/nicestlog/log_statement_analyzer.py
     - [x] src/nicestlog/log_reviewer.py
     - [x] src/nicestlog/live_editor.py
     - [x] src/nicestlog/advanced_assistant.py
     - [x] src/nicestlog/linter.py

   - **Steps** (always action verbs, explicit order)

     - [x] Search for all try-except blocks in the codebase
     - [x] Analyze if exceptions are correctly handled or suppressed
     - [x] Classify the found blocks
     - [x] Document the findings

   - **Commit message hint**: "Analyze try-except blocks that suppress exceptions"

1. [x] **Analyze legacy code patterns** – Identify legacy patterns in the code

   - **Context**: Legacy patterns in the code create technical debt and hinder further development.

   - **Success criteria**

     - [x] All legacy patterns identified
     - [x] Impact documented
     - [x] Breaking changes documented

   - **Files to check/modify**

     - [x] src/nicestlog/core.py
     - [x] src/nicestlog/systemd_integration.py
     - [x] src/nicestlog/assistant.py
     - [x] src/nicestlog/cli.py
     - [x] src/nicestlog/advanced_assistant.py
     - [x] src/nicestlog/linter.py

   - **Steps**

     - [x] Search for legacy, workaround, compatibility, and hack patterns
     - [x] Analyze the found patterns
     - [x] Document the findings

   - **Commit message hint**: "Analyze legacy code patterns"

1. [x] **Plan the cleanup** – Create a plan to remove the anti-patterns

   - **Context**: Based on the analysis, concrete steps for cleanup need to be planned.

   - **Success criteria**

     - [x] Detailed cleanup plan created
     - [x] Prioritization of tasks
     - [x] Risk assessment performed

   - **Files to check/modify**

     - [x] \_TODO-AGENT.md (this file)
     - [x] docs/development/cleanup_plan.md

   - **Steps**

     - [x] Create a detailed cleanup plan
     - [x] Prioritize the identified issues
     - [x] Perform risk assessment for each change
     - [x] Document the plan

   - **Commit message hint**: "Plan cleanup of try-except suppression and legacy patterns"

1. [ ] **Implement the cleanup** – Remove the identified anti-patterns

   - **Context**: After planning, the identified anti-patterns are removed step by step.

   - **Success criteria**

     - [ ] All identified try-except suppressions removed
     - [ ] All identified legacy patterns cleaned up
     - [ ] Tests updated
     - [ ] Documentation updated

   - **Files to check/modify**

     - [ ] All files with identified anti-patterns
     - [ ] Tests for the affected modules
     - [ ] Documentation

   - **Steps**

     - [ ] Remove try-except blocks that suppress exceptions
     - [ ] Replace with correct error handling or re-raising of exceptions
     - [ ] Remove legacy patterns
     - [ ] Update tests
     - [ ] Update documentation

   - **Commit message hint**: "Remove try-except suppression and legacy patterns"

1. [ ] **Test and validate** – Run the full test suite

   - **Context**: Ensure that no functionality has been compromised.

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
