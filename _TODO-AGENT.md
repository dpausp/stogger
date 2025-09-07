# Fix Test Failures - Core Logging and CLI Issues

Task goal
- Fix 50 failing tests in the nicestlog test suite
- Focus on core logging DropEvent issues and missing CLI functions
- Don't build new features, only fix clear test issues

Out-of-scope for this task
- Building new features to satisfy tests
- Major architectural changes
- Fixing unrelated test failures

General approach (guardrails)
- English artifacts (Rule 7)
- No dependency YOLOing (Rule 3). Use `uv run` for Python commands
- Lint before committing (Rule 5). Respect pre-commit if present (Rule 6)
- Test-driven fixes (Rule 4)

Prioritized work items (with checkboxes)

1) Fix ConsoleFileRenderer DropEvent issues
   - Context: Many tests fail because ConsoleFileRenderer raises DropEvent by default when filtering log levels
   - Root cause: safe_drop=False by default causes DropEvent exceptions in logging pipeline
   - Files to modify:
     - src/nicestlog/core.py (change default safe_drop value)
     - tests/test_core.py (update test that expects DropEvent)
   - Steps:
     - [ ] Change safe_drop default from False to True in ConsoleFileRenderer.__init__
     - [ ] Update test_level_filtering to explicitly set safe_drop=False
     - [ ] Run tests to verify DropEvent issues are resolved

2) Add missing create_migration_backup function
   - Context: CLI tests expect create_migration_backup function that doesn't exist
   - Error: AttributeError: module 'src.nicestlog.cli' does not have attribute 'create_migration_backup'
   - Files to modify:
     - src/nicestlog/cli.py (add missing function)
   - Steps:
     - [ ] Add create_migration_backup function to CLI module
     - [ ] Implement basic functionality or stub as needed
     - [ ] Run CLI tests to verify fix

3) Fix CLI exit code mismatches
   - Context: Tests expect exit code 1 but getting 2 in several CLI scenarios
   - Affected tests: test_migrate_command_invalid_type, test_migrate_interactive_mode_error
   - Files to check:
     - src/nicestlog/cli.py (check exit code logic)
     - tests/test_cli.py (verify expected behavior)
   - Steps:
     - [ ] Analyze failing tests to understand expected vs actual exit codes
     - [ ] Fix CLI exit code logic where appropriate
     - [ ] Run tests to verify fixes

4) Fix journal viewer output format issues
   - Context: Journal viewer tests expect specific output format but getting different format
   - Affected tests: test_main_json_output, test_main_formatted_output
   - Files to check:
     - src/nicestlog/journal_viewer.py
     - tests/test_journal_viewer.py
   - Steps:
     - [ ] Analyze expected vs actual output format
     - [ ] Fix output formatting in journal viewer
     - [ ] Run tests to verify fixes

5) Run comprehensive test validation
   - Context: Ensure fixes don't break other functionality
   - Steps:
     - [ ] Run full test suite with `uv run pytest`
     - [ ] Verify significant reduction in test failures
     - [ ] Check that core functionality still works
     - [ ] Document any remaining test failures with reasons