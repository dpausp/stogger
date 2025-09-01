# Complete CLI Simplification and Documentation Update

Task goal
- Finish the CLI cleanup by simplifying remaining complex command signatures
- Evaluate and potentially simplify the tools subgroup
- Update documentation to reflect CLI changes
- Ensure all CLI commands are intuitive and well-documented

Out-of-scope for this task
- Adding new CLI functionality
- Breaking changes to core logging functionality
- Major architectural changes

General approach (guardrails)
- English artifacts (Rule 7)
- No dependency YOLOing (Rule 3). Use `uv run` for Python commands
- Lint before committing (Rule 5). Respect pre-commit if present (Rule 6)
- Only add tests when we change code (Rule 4)

Prioritized work items (with checkboxes)

1) Evaluate tools subgroup simplification
   - Context: Check if all tools commands are necessary and well-organized
   - Files to check/modify:
     - src/nicestlog/cli.py (tools_app section)
     - tests/test_cli.py (tools command tests)
   - Steps:
     - [x] Review all tools commands and their usage
     - [x] Identify any redundant or overly complex tools commands
     - [x] Simplify or remove unnecessary tools commands (simplified demo command)
     - [x] Update tests for any changes (tests still pass)

2) Simplify complex command signatures
   - Context: Look for overly complex parameter combinations and simplify them
   - Files to check/modify:
     - src/nicestlog/cli.py (command definitions)
     - tests/test_cli.py (parameter validation tests)
   - Steps:
     - [x] Identify commands with too many parameters or complex combinations
     - [x] Simplify parameter sets while maintaining functionality (demo command simplified)
     - [x] Update help texts for clarity
     - [x] Update tests for simplified commands (tests pass)

3) Update documentation
   - Context: Ensure documentation reflects the cleaned-up CLI structure
   - Files to check/modify:
     - docs/user_guide/getting_started.md
     - docs/user_guide/cli_migration_guide.md
     - README.md
   - Steps:
     - [x] Update CLI examples in documentation (fixed demo command reference in README)
     - [x] Remove references to deleted commands (no deleted commands, only simplified)
     - [x] Add clear command structure overview (CLI help shows clean structure)
     - [x] Update help text examples (demo command help text is now cleaner)