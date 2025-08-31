# Coverage Scope Improvement - Exclude Tests from Logging Analysis

Task goal
- Configure coverage and linting tools to only scan `src/` directory for "too little logging" checks
- Tests should not be analyzed for logging coverage since they have different requirements
- Maintain current test coverage functionality but scope logging analysis appropriately

Out-of-scope for this task
- Changing existing test coverage metrics or pytest configuration
- Modifying the actual linting logic for source code
- Removing tests from code coverage entirely

General approach (guardrails)
- English artifacts (Rule 7)
- No dependency YOLOing (Rule 3). Use `uv run` for Python commands
- Lint before committing (Rule 5). Respect pre-commit if present (Rule 6)
- Only add tests when we change code (Rule 4)

Prioritized work items (with checkboxes)

1) Analyze current coverage configuration
   - Context: Understand how coverage is currently configured and what's scanning tests
   - Files to check/modify:
     - pyproject.toml (check for coverage config)
     - dodo.py (check coverage tasks)
     - src/nicestlog/linter.py (understand how directories are scanned)
     - src/nicestlog/cli.py (check command behavior)
   - Steps:
     - [x] Check current coverage configuration in pyproject.toml
     - [x] Examine dodo.py coverage tasks
     - [x] Review linter.py to understand directory scanning
     - [x] Check CLI check command implementation

2) Implement smart project structure detection ✅ COMPLETED
   - Context: Auto-detect source and test directories instead of relying on manual configuration
   - Files to check/modify:
     - src/nicestlog/config.py (add detection logic)
     - src/nicestlog/project_analyzer.py (enhance project analysis)
   - Steps:
     - [x] Add function to detect source directory from pyproject.toml (hatch config, src_dir, etc.)
     - [x] Add function to detect test directories (tests/, test/, pytest config)
     - [x] Add function to auto-detect exclude patterns (docs/, examples/, .venv/, build/)
     - [x] Create ProjectStructure dataclass to hold detected information
     - [x] make sure that final results (where are we looking for log messages, what is included/excluded) are displayed to the user early. 
     - [x] if structure unclear: let the CLI die and user is asked to configure stuff.
     - [x] Commit with message: "feat: add smart project structure detection with fallback heuristics"

3) Implement transparent CLI reporting ✅ COMPLETED
   - Context: User must know what context/config is being used and why decisions were made
   - Files to check/modify:
     - src/nicestlog/cli.py (update check command output)
     - src/nicestlog/linter.py (add reporting to lint_directory)
   - Steps:
     - [x] Add project context reporting at start of check command
     - [x] Show detected vs configured vs default values with source attribution
     - [x] Display what's being scanned vs excluded with reasoning
     - [x] Add summary of scope differences (code coverage vs logging analysis)
     - [x] Ensure all detection decisions are clearly communicated to user
     - [x] Commit with message: "feat: add transparent project context reporting to CLI commands"

4) Configure coverage to exclude tests from logging analysis using smart defaults
   - Context: Apply the smart detection to actually exclude tests from logging analysis
   - Files to check/modify:
     - src/nicestlog/linter.py (modify directory scanning logic)
     - src/nicestlog/cli.py (integrate smart detection)
   - Steps:
     - [ ] Integrate ProjectStructure detection into linter.py
     - [ ] Modify lint_directory to use smart exclusions
     - [ ] Update CLI check command to use smart detection
     - [ ] Test that tests are excluded from logging analysis but included in code coverage
     - [ ] Commit with message: "feat: exclude tests from logging coverage analysis using smart project detection"

5) Verify and document the change
   - Context: Ensure the change works as expected and document the behavior
   - Files to check/modify:
     - README.md or docs/ (document the behavior)
     - Test the functionality
   - Steps:
     - [ ] Run `uv run nicestlog check .` and verify tests are not analyzed for logging
     - [ ] Run `uv run pytest --cov` and verify code coverage still includes tests
     - [ ] Update documentation to explain the difference between code coverage and logging coverage
     - [ ] Commit with message: "docs: document logging coverage vs code coverage scope differences"
