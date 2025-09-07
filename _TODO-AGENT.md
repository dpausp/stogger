# Add log string length validation to nicestlog

Task goal
- Add validation for log strings with too many elements/words (like 'debug-logging-is-enabled-check-logs-above-for-http-details')
- Warn when log strings have 5+ elements, error when 7+ elements
- Improve readability of log messages by encouraging shorter, more structured logging

Out-of-scope for this task
- Changing existing log messages in the codebase
- Modifying other linting rules
- Breaking existing API compatibility

General approach (guardrails)
- English artifacts (Rule 7)
- No dependency YOLOing (Rule 3). Use `uv run` for Python commands
- Lint before committing (Rule 5). Respect pre-commit if present (Rule 6)
- Only add tests when we change code (Rule 4)

Prioritized work items (with checkboxes)

1) Implement log string length validation
   - Context: Users report seeing very long log strings with many dashes that are hard to read
   - Files to check/modify:
     - src/nicestlog/log_statement_analyzer.py
   - Steps:
     - [x] Add function to count elements in log strings (split by dashes/underscores)
     - [x] Add validation in _detect_issues method
     - [x] Add appropriate issue types for 5+ and 7+ elements
     - [x] Test the new validation logic

2) Add tests for the new validation
   - Context: Need to ensure the new rule works correctly
   - Files to check/modify:
     - tests/test_log_statement_analyzer.py (or create if needed)
   - Steps:
     - [x] Write test cases for strings with different element counts
     - [x] Test edge cases (empty strings, single words, etc.)
     - [x] Run tests with `uv run pytest`

3) Update documentation and commit
   - Context: Document the new validation rule
   - Files to check/modify:
     - src/nicestlog/log_statement_analyzer.py (docstrings)
   - Steps:
     - [x] Update docstrings to mention the new validation
     - [x] Commit with message: "feat: add validation for overly long log strings with many elements"