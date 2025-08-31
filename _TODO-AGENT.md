# Build pexpect Tests Without Mocking for Direct Testing

Task goal
- Create pexpect-based tests that work without mocking and test directly
- Add real terminal interaction tests for CLI interactive features
- Mark these tests as slow using @pytest.mark.slow
- Ensure tests have proper timeouts and error handling

Out-of-scope for this task
- Changing the core logging functionality beyond fixing the 'exception' level issue
- Modifying non-test code unless necessary for test fixes
- Performance optimizations unrelated to test stability

General approach (guardrails)
- English artifacts (Rule 7)
- No dependency YOLOing (Rule 3). Use `uv run` for Python commands
- Lint before committing (Rule 5). Respect pre-commit if present (Rule 6)
- Only add tests when we change code (Rule 4)

Prioritized work items (with checkboxes)

1) Analyze and fix logging level issues ✅ COMPLETED
   - Context: Tests failing because 'exception' is not in the LEVELS list in core.py
   - Files to check/modify:
     - src/nicestlog/core.py (check LEVELS definition)
     - src/nicestlog/interactive_transformer.py (fix exception logging)
     - tests/test_interactive_transformer.py (verify error handling)
   - Steps:
     - [x] Check core.py LEVELS definition and add 'exception' if missing
     - [x] Fix interactive_transformer.py to use proper logging levels
     - [x] Update error handling to be graceful as tests expect
     - [x] Run interactive transformer tests to verify fixes

2) Identify hanging tests ✅ COMPLETED
   - Context: Test suite hangs around 13% completion, need to find which tests
   - Files to check/modify:
     - tests/test_cli.py (check interactive mode tests)
     - tests/test_cli_ast_integration.py (check interactive tests)
     - Any other tests that might use real user input
   - Steps:
     - [x] Run individual test files to isolate hanging tests
     - [x] Check for tests that use real input() calls instead of mocked input
     - [x] Identify tests that need pexpect for proper terminal interaction
   - Result: Hanging was caused by the logging level issue, not interactive tests

3) Implement pexpect for interactive tests ✅ COMPLETED
   - Context: Create new pexpect tests that test real terminal interaction without mocking
   - Files to check/modify:
     - tests/test_cli_pexpect.py (new file for pexpect-based CLI tests)
     - tests/test_interactive_pexpect.py (new file for interactive transformer tests)
     - Add pexpect test utilities and helpers
   - Steps:
     - [x] Create helper functions for pexpect-based testing
     - [x] Create new pexpect tests for CLI interactive commands
     - [x] Create pexpect tests for interactive transformer
     - [x] Ensure pexpect tests have proper timeouts and are marked as slow
     - [x] Test that pexpect tests run reliably

4) Fix specific failing tests
   - Context: Address the specific test failures identified
   - Files to check/modify:
     - tests/test_cli.py (fix empty directory and config parse error tests)
     - tests/test_advanced_assistant.py (fix error handling tests)
   - Steps:
     - [ ] Fix test_check_command_empty_directory expectations
     - [ ] Fix test_init_config_toml_parse_error expectations
     - [ ] Fix advanced assistant error handling tests
     - [ ] Verify all previously failing tests now pass

5) Verify and clean up
   - Context: Ensure all tests run without hanging and pass reliably
   - Steps:
     - [ ] Run full test suite to verify no hanging
     - [ ] Check that all tests pass or have expected failures
     - [ ] Clean up any temporary test files
     - [ ] Document any changes to test patterns or requirements