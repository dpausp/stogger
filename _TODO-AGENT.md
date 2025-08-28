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

2) Analyze unused code in src/nicestlog/ ⚠️ IN PROGRESS
   - Context: Core library code that might have unused functions/classes that could be valuable
   - Files to check/modify:
     - src/nicestlog/advanced_assistant.py (12 items - constants and methods)
     - src/nicestlog/cli.py (13 items - CLI commands and internal functions)
     - src/nicestlog/config.py (8 items - configuration attributes)
     - Other src/ files (9 items - various functions/variables)
   - Steps:
     - [x] Analyze advanced_assistant.py: TransformationStage enum and constants are unused
     - [x] Analyze cli.py: Several CLI commands are defined but not accessible
     - [x] Remove TransformationStage enum (completely unused)
     - [x] Remove unused NodeType constants (kept CALL which is used)
     - [x] Remove rollback_data field (unused feature)
     - [ ] Review remaining unused items for potential value
     - [ ] Document decision: keep, refactor, or remove
     - [ ] Commit with message: "refactor: cleanup unused code in core library"

   **Key Findings:**
   - ✅ TransformationStage enum: REMOVED (completely unused)
   - ✅ NodeType constants: REMOVED unused ones, kept CALL (used by tests)
   - ✅ rollback_data field: REMOVED (unused feature placeholder)
   - ⚠️ CLI commands like tools_generate_service, tools_review, etc.: Need investigation
   - ⚠️ transform_directory method in AdvancedAssistant: Public API that could be valuable
   - ⚠️ Config attributes: May be planned features or dead configuration options

   **Progress:** Successfully removed 3 categories of unused code, saving ~15 lines

3) Analyze unused code in tests/ ⚠️ IN PROGRESS
   - Context: Test utilities and fixtures that might be unused but valuable
   - Files to check/modify:
     - tests/test_config.py: create_pyproject_toml fixture (lines 13, 31, 41)
     - tests/test_cli_demos.py: mock_init_logging variable (line 32)
     - tests/test_eliot_integration.py: mock_eliot_unavailable fixture (multiple lines)
     - tests/test_log_reviewer.py: mock_is_dir, mock_is_file variables (multiple lines)
     - Other test files with unused mock attributes
   - Steps:
     - [x] Analyze test_config.py: create_pyproject_toml is a fixture used in function parameters
     - [x] Analyze test_cli_demos.py: mock_init_logging is assigned but not used in test
     - [ ] Review unused test utilities
     - [ ] Remove truly dead test code
     - [ ] Commit with message: "test: cleanup unused test code"

   **Key Findings:**
   - create_pyproject_toml: This is a pytest fixture - vulture doesn't understand fixture usage
   - mock_init_logging: Variable assigned but not explicitly used (test may rely on side effects)
   - Many mock.side_effect and mock attributes: These are pytest/unittest patterns vulture doesn't recognize
   - Most test "unused" code is actually used by pytest framework

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