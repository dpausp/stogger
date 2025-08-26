# Move Specialized Commands to Tools Subgroup

Task goal
- Move `review`, `journal`, `dashboard`, `demo`, `i18n` commands to `tools` subgroup
- Clean up main CLI interface to focus on core functionality (check, fix, migrate)
- Maintain backward compatibility where possible
- Improve CLI organization and discoverability

Success criteria
- Commands moved to tools subgroup: `tools review`, `tools journal`, etc.
- Main CLI shows only core commands: check, fix, migrate, init, docs
- All existing functionality preserved
- Tests updated to reflect new command structure
- Documentation updated with new command paths

Out-of-scope for this task
- Changing the underlying functionality of moved commands
- Removing any features
- Breaking existing scripts (provide deprecation warnings if needed)

General approach (guardrails)
- English artifacts (Rule 7)
- No dependency YOLOing (Rule 3). Use `uv run` for Python commands
- Lint before committing (Rule 5). Respect pre-commit if present (Rule 6)
- Only add tests when we change code (Rule 4)

Prioritized work items (with checkboxes)

1) Analyze current command structure
   - Context: Understand current CLI layout and identify commands to move
   - Files to check/modify:
     - src/nicestlog/cli.py
   - Steps:
     - [ ] List all current top-level commands
     - [ ] Identify core vs specialized commands
     - [ ] Plan the new structure
     - [ ] Commit with message: "docs: analyze current CLI command structure"

2) Move review command to tools
   - Context: Review is a specialized analysis tool
   - Files to check/modify:
     - src/nicestlog/cli.py
   - Steps:
     - [ ] Move review command to tools_app
     - [ ] Update command registration
     - [ ] Test the new command path
     - [ ] Commit with message: "feat: move review command to tools subgroup"

3) Move journal command to tools
   - Context: Journal viewer is a specialized systemd tool
   - Files to check/modify:
     - src/nicestlog/cli.py
   - Steps:
     - [ ] Move journal command to tools_app
     - [ ] Update command registration
     - [ ] Test the new command path
     - [ ] Commit with message: "feat: move journal command to tools subgroup"

4) Move dashboard command to tools (if Flask available)
   - Context: Dashboard is a specialized web tool
   - Files to check/modify:
     - src/nicestlog/cli.py
   - Steps:
     - [ ] Move dashboard command to tools_app
     - [ ] Update Flask availability check for tools context
     - [ ] Test the new command path
     - [ ] Commit with message: "feat: move dashboard command to tools subgroup"

5) Move demo command to tools
   - Context: Demo is a utility/educational tool
   - Files to check/modify:
     - src/nicestlog/cli.py
   - Steps:
     - [ ] Move demo command to tools_app
     - [ ] Update command registration
     - [ ] Test the new command path
     - [ ] Commit with message: "feat: move demo command to tools subgroup"

6) Move i18n subgroup to tools
   - Context: i18n is a specialized development tool
   - Files to check/modify:
     - src/nicestlog/cli.py
   - Steps:
     - [ ] Move i18n_app to be under tools_app
     - [ ] Update nested subgroup structure
     - [ ] Test the new command path: tools i18n check
     - [ ] Commit with message: "feat: move i18n commands to tools subgroup"

7) Update tests and documentation
   - Context: All references need to be updated to new command paths
   - Files to check/modify:
     - tests/test_cli.py
     - tests/test_cli_integration.py
     - docs/ files
     - README.md
   - Steps:
     - [ ] Update all test command invocations
     - [ ] Update documentation examples
     - [ ] Add migration notes for users
     - [ ] Test all new command paths
     - [ ] Commit with message: "docs: update for reorganized CLI command structure"