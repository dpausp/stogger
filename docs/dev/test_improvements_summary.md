# Test Improvements Summary

Test patterns, dependencies, and best practices for the stogger test suite.

## Test Patterns and Requirements

### New Test Categories
1. **Pexpect Tests** (`@pytest.mark.slow`)
   - Use real terminal interaction
   - Have proper timeouts (default 10 seconds)
   - Test actual CLI behavior without mocking
   - Located in `test_*_pexpect.py` files

2. **Interactive Tests**
   - Test user input scenarios
   - Verify graceful error handling
   - Test keyboard interrupt scenarios

### Test Execution Guidelines
- **Fast tests**: Run with `uv run pytest` (excludes slow tests)
- **All tests**: Run with `uv run pytest -m "not slow"` for fast tests only
- **Slow tests**: Run with `uv run pytest -m slow` for pexpect tests only
- **Full suite**: Run with `uv run pytest --tb=short` for complete testing

## Dependencies
- **pexpect**: Required for terminal interaction tests
- **pytest**: Test framework with slow marker support
- **typer**: CLI framework being tested

## Best Practices
1. Use pexpect for real terminal interaction testing
2. Mark slow tests with `@pytest.mark.slow`
3. Always include timeouts in pexpect tests
4. Test both success and error scenarios
5. Align test expectations with actual CLI behavior
