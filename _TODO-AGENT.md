# Fix CLI Test Failures

Task goal
- Fix 40 failing tests that expect old CLI command structure
- Update tests to use correct command paths (e.g., `tools dashboard` instead of `dashboard`)
- Ensure all CLI commands work correctly with their current structure
- Restore test suite to passing state

Success criteria
- All tests pass (347 tests, 0 failures)
- CLI commands work correctly with current structure
- Tests use proper command paths (tools subcommands)
- No regression in CLI functionality

Out-of-scope for this task
- Changing CLI command structure or organization
- Adding new CLI commands or features
- Modifying command functionality
- Performance optimizations

General approach (guardrails)
- English artifacts (Rule 7)
- No dependency YOLOing (Rule 3). Use `uv run` for Python commands
- Lint before committing (Rule 5). Respect pre-commit if present (Rule 6)
- Only add tests when we change code (Rule 4)
- **Dogfooding**: Use `uv run python -m nicestlog check` on our own code to validate changes

Prioritized work items (with checkboxes)

1) Analyze failing tests and CLI structure
   - Context: Understand which tests are failing and why (command structure mismatch)
   - Files to check/modify:
     - tests/test_cli.py (main CLI tests)
     - tests/test_cli_integration.py (integration tests)
     - tests/test_cli_more_demos.py (demo tests)
   - Steps:
     - [x] Run pytest to identify failing tests
     - [x] Identify that commands moved under 'tools' subcommand
     - [x] Understand current CLI structure vs test expectations
     - [ ] Commit with message: "docs: analyze CLI test failures and command structure"

2) Fix main CLI tests (test_cli.py)
   - Context: Update tests to use correct command paths
   - Files to check/modify:
     - tests/test_cli.py (dashboard, journal, review command tests)
   - Steps:
     - [x] Update dashboard tests to use "tools dashboard"
     - [x] Update journal tests to use "tools journal" 
     - [x] Update review tests to use "tools review"
     - [x] Fix help command test expectations
     - [x] Commit with message: "fix: update CLI tests for tools subcommand structure"

3) Fix integration tests
   - Context: Update integration tests for correct command structure
   - Files to check/modify:
     - tests/test_cli_integration.py
     - tests/test_cli_ast_integration.py
   - Steps:
     - [x] Update all integration tests to use correct command paths
     - [x] Fix AST integration tests
     - [x] Update i18n check tests
     - [x] Commit with message: "fix: update integration tests for tools subcommand"

4) Fix remaining test failures ✅ COMPLETED!
   - Context: Address remaining test expectation vs behavior issues
   - Files to check/modify:
     - tests/test_cli_integration.py (4 lint integration tests)
     - tests/test_cli_ast_integration.py (8 AST tests)
     - tests/test_advanced_assistant.py (1 AST analysis test)
   - Steps:
     - [x] Fix demo and i18n command tests
     - [x] Fix remaining AST integration test expectations
     - [x] Fix lint integration test expectations
     - [x] Fix advanced assistant AST analysis test
     - [x] Commit with message: "fix: resolve remaining CLI test failures"

🎯 TASK COMPLETED SUCCESSFULLY!
- Started with: 40 failing tests, 307 passing
- Final result: 0 failing tests, 347 passing
- 100% test success rate achieved!