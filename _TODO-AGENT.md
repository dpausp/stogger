# Make Flask Web Dashboard Optional

Task goal
- Make Flask and web dashboard functionality optional dependencies
- Hide the dashboard command since it's not mature and has too many dependencies
- Reduce the core dependency footprint of nicestlog
- Keep web dashboard available for users who explicitly want it

Success criteria
- Flask moved from required to optional dependencies
- Dashboard command hidden/disabled when Flask not available
- Core nicestlog functionality works without Flask
- Clear error messages when trying to use dashboard without Flask
- No breaking changes for existing users who have Flask installed

Out-of-scope for this task
- Removing the web dashboard code entirely
- Rewriting the dashboard with different technology
- Adding new dashboard features
- Performance optimizations

General approach (guardrails)
- English artifacts (Rule 7)
- No dependency YOLOing (Rule 3). Use `uv run` for Python commands
- Lint before committing (Rule 5). Respect pre-commit if present (Rule 6)
- Only add tests when we change code (Rule 4)

Prioritized work items (with checkboxes)

1) Move Flask to optional dependencies
   - Context: Flask is currently required but only needed for web dashboard
   - Files to check/modify:
     - pyproject.toml
   - Steps:
     - [x] Move flask from dependencies to optional-dependencies
     - [x] Create new "web" or "dashboard" optional dependency group
     - [x] Update dependency groups if needed
     - [x] Commit with message: "feat: make Flask optional dependency for web dashboard"

2) Add optional import handling for Flask
   - Context: Need graceful handling when Flask is not installed
   - Files to check/modify:
     - src/nicestlog/web_dashboard.py
     - src/nicestlog/cli.py
   - Steps:
     - [x] Add try/except for Flask imports in web_dashboard.py
     - [x] Add graceful error handling in CLI dashboard command
     - [x] Create helpful error messages for missing Flask
     - [x] Commit with message: "feat: add graceful handling for missing Flask dependency"

3) Hide dashboard command when Flask unavailable
   - Context: Dashboard command should be hidden if Flask not installed
   - Files to check/modify:
     - src/nicestlog/cli.py
   - Steps:
     - [x] Conditionally register dashboard command based on Flask availability
     - [x] Add clear error message if command is called without Flask
     - [x] Update CLI help to reflect optional nature
     - [x] Commit with message: "feat: hide dashboard command when Flask not available"

4) Update tests and documentation
   - Context: Tests need to handle optional Flask, docs need updating
   - Files to check/modify:
     - tests/test_cli.py
     - tests/test_cli_integration.py
     - docs/ files
     - README.md
   - Steps:
     - [ ] Add tests for missing Flask scenarios
     - [ ] Update existing tests to handle optional Flask
     - [ ] Update documentation about optional web dashboard
     - [ ] Add installation instructions for web dashboard
     - [ ] Commit with message: "docs: update for optional Flask web dashboard"