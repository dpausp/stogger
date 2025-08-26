# Remove Redundant Lint Command

Task goal
- Remove the redundant `lint` command since `check` command provides all linting functionality and more
- Simplify CLI interface by consolidating functionality
- Ensure no functionality is lost in the migration
- Update documentation and tests accordingly

Success criteria
- `lint` command removed from CLI
- All `lint` functionality available through `check` command
- Tests updated to use `check` instead of `lint`
- Documentation updated to reflect the change
- No breaking changes for users (clear migration path)

Out-of-scope for this task
- Changing the underlying linting logic
- Modifying the check command functionality
- Adding new features

General approach (guardrails)
- English artifacts (Rule 7)
- No dependency YOLOing (Rule 3). Use `uv run` for Python commands
- Lint before committing (Rule 5). Respect pre-commit if present (Rule 6)
- Only add tests when we change code (Rule 4)

Prioritized work items (with checkboxes)

1) Analyze current lint vs check functionality
   - Context: Need to understand what lint does vs check to ensure no functionality is lost
   - Files to check/modify:
     - src/nicestlog/cli.py
     - src/nicestlog/linter.py
   - Steps:
     - [x] Compare lint and check command implementations
     - [x] Identify any unique lint functionality
     - [x] Document the migration path for users
     - [x] Commit with message: "docs: analyze lint vs check command functionality"

2) Remove lint command from CLI
   - Context: Remove the redundant lint command registration
   - Files to check/modify:
     - src/nicestlog/cli.py
   - Steps:
     - [ ] Remove @app.command() lint function
     - [ ] Remove run_linter function if not used elsewhere
     - [ ] Update help text and command listings
     - [ ] Commit with message: "feat: remove redundant lint command, use check instead"

3) Update tests to use check instead of lint
   - Context: All lint tests should be migrated to use check command
   - Files to check/modify:
     - tests/test_cli.py
     - tests/test_cli_integration.py
     - Any other test files using lint
   - Steps:
     - [ ] Find all tests using lint command
     - [ ] Update tests to use check command with appropriate flags
     - [ ] Ensure test coverage is maintained
     - [ ] Commit with message: "test: migrate lint tests to use check command"

4) Update documentation and migration guide
   - Context: Users need to know about the change and how to migrate
   - Files to check/modify:
     - README.md
     - docs/ files
     - CLI help text
   - Steps:
     - [ ] Update documentation to remove lint references
     - [ ] Add migration note for users currently using lint
     - [ ] Update examples to use check instead of lint
     - [ ] Commit with message: "docs: remove lint command references, update to use check"