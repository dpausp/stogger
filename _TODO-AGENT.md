# Unused Code Analysis and Cleanup

Task goal
- Analyze unused code found by vulture in the nicestlog project
- Create checklist for each unused code location to evaluate if it can be meaningfully used
- Focus on project code (src/, tests/, examples/, docs/) not dependencies (.venv/)
- Determine which unused code should be kept, refactored, or removed

Success criteria
- Complete analysis of all unused code in project files
- Documented decision for each unused code item
- Improved code quality by removing truly dead code or finding ways to use valuable code

Out-of-scope for this task
- Dependencies in .venv/ (those are external libraries)
- Major refactoring that would change public APIs
- Adding new features just to use unused code

General approach (guardrails)
- English artifacts (Rule 7)
- No dependency YOLOing (Rule 3). Use `uv run` for Python commands
- Lint before committing (Rule 5). Respect pre-commit if present (Rule 6)
- Only add tests when we change code (Rule 4)

Prioritized work items (with checkboxes)

1) Filter vulture output to project files only ✅ COMPLETED
   - Context: Vulture found 6621 items, but most are in .venv/. Need to focus on actual project code
   - Files to check/modify:
     - Run vulture with better filtering
   - Steps:
     - [x] Run vulture only on src/, tests/, examples/, docs/, dodo.py
     - [x] Create filtered list of unused code in project files (147 items found)
     - [x] Create detailed analysis report in tmp_rovodev_unused_code_analysis.md
     - [ ] Commit with message: "docs: add filtered unused code analysis"

2) Analyze unused code in src/nicestlog/
   - Context: Core library code that might have unused functions/classes that could be valuable
   - Files to check/modify:
     - All files in src/nicestlog/ with unused code
   - Steps:
     - [ ] Review each unused item for potential value
     - [ ] Document decision: keep, refactor, or remove
     - [ ] Commit with message: "refactor: cleanup unused code in core library"

3) Analyze unused code in tests/
   - Context: Test utilities and fixtures that might be unused but valuable
   - Files to check/modify:
     - Test files with unused code
   - Steps:
     - [ ] Review unused test utilities
     - [ ] Remove truly dead test code
     - [ ] Commit with message: "test: cleanup unused test code"

4) Analyze unused code in examples/ and docs/
   - Context: Example code and documentation that might be outdated
   - Files to check/modify:
     - Example files and documentation
   - Steps:
     - [ ] Review unused example code
     - [ ] Update or remove outdated examples
     - [ ] Commit with message: "docs: cleanup unused example and documentation code"

5) Analyze dodo.py unused functions
   - Context: Build system tasks that might be unused but valuable
   - Files to check/modify:
     - dodo.py
   - Steps:
     - [ ] Review unused dodo tasks
     - [ ] Document which tasks are intentionally available vs truly unused
     - [ ] Commit with message: "build: cleanup unused dodo tasks"