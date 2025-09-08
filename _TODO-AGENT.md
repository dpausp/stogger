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

1. [ ] **Analyze try-except blocks** – Identify blocks that suppress exceptions

   - **Context**: Try-except blocks that ignore or suppress exceptions prevent early detection of errors.

   - **Success criteria** (must be checked to finish task)

     - [ ] All try-except blocks in the codebase identified
     - [ ] Blocks classified (suppressing vs. correctly handled)
     - [ ] Documentation of found patterns

   - **Files to check/modify**

     - [ ] src/nicestlog/core.py
     - [ ] src/nicestlog/systemd_integration.py
     - [ ] src/nicestlog/assistant.py
     - [ ] src/nicestlog/cli.py
     - [ ] src/nicestlog/web_dashboard.py
     - [ ] src/nicestlog/project_analyzer.py
     - [ ] src/nicestlog/log_statement_analyzer.py
     - [ ] src/nicestlog/log_reviewer.py
     - [ ] src/nicestlog/live_editor.py
     - [ ] src/nicestlog/advanced_assistant.py
     - [ ] src/nicestlog/linter.py

   - **Steps** (always action verbs, explicit order)

     - [ ] Search for all try-except blocks in the codebase
     - [ ] Analyze if exceptions are correctly handled or suppressed
     - [ ] Classify the found blocks
     - [ ] Document the findings

   - **Commit message hint**: "Analyze try-except blocks that suppress exceptions"

2. [ ] **Analyze legacy code patterns** – Identify legacy patterns in the code

   - **Context**: Legacy patterns in the code create technical debt and hinder further development.

   - **Success criteria**

     - [ ] All legacy patterns identified
     - [ ] Impact documented
     - [ ] Breaking changes documented

   - **Files to check/modify**

     - [ ] src/nicestlog/core.py
     - [ ] src/nicestlog/systemd_integration.py
     - [ ] src/nicestlog/assistant.py
     - [ ] src/nicestlog/cli.py
     - [ ] src/nicestlog/advanced_assistant.py
     - [ ] src/nicestlog/linter.py

   - **Steps**

     - [ ] Search for legacy, workaround, compatibility, and hack patterns
     - [ ] Analyze the found patterns
     - [ ] Document the findings

   - **Commit message hint**: "Analyze legacy code patterns"

3. [ ] **Plan the cleanup** – Create a plan to remove the anti-patterns

   - **Context**: Based on the analysis, concrete steps for cleanup need to be planned.

   - **Success criteria**

     - [ ] Detailed cleanup plan created
     - [ ] Prioritization of tasks
     - [ ] Risk assessment performed

   - **Files to check/modify**

     - [ ] _TODO-AGENT.md (this file)

   - **Steps**

     - [ ] Create a detailed cleanup plan
     - [ ] Prioritize the identified issues
     - [ ] Perform risk assessment for each change
     - [ ] Document the plan

   - **Commit message hint**: "Plan cleanup of try-except suppression and legacy patterns"

4. [ ] **Implement the cleanup** – Remove the identified anti-patterns

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

5. [ ] **Test and validate** – Run the full test suite

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