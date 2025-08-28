# Improve Codebase Logging Quality (Dogfooding)

Task goal
- Fix logging quality issues found by our own nicestlog check tool
- Improve log.error() calls to use log.exception() in except blocks
- Address the 9 specific logging level issues identified
- Practice what we preach - use nicestlog to improve nicestlog itself

Success criteria
- All 9 log.error() → log.exception() issues fixed
- Dogfooding check shows improvement in logging quality
- No regression in functionality or tests
- Better exception handling with proper tracebacks

Out-of-scope for this task
- Adding more logging statements (would change coverage significantly)
- Restructuring logging architecture
- Changing logging levels beyond the specific issues identified
- Performance optimizations

General approach (guardrails)
- English artifacts (Rule 7)
- No dependency YOLOing (Rule 3). Use `uv run` for Python commands
- Lint before committing (Rule 5). Respect pre-commit if present (Rule 6)
- Only add tests when we change code (Rule 4)
- **Dogfooding**: Use `uv run python -m nicestlog check` to validate improvements

Prioritized work items (with checkboxes)

1) Fix exception handling in interactive_transformer.py
   - Context: Line 267 uses log.error() in except block, should use log.exception()
   - Files to check/modify:
     - src/nicestlog/interactive_transformer.py
   - Steps:
     - [ ] Change log.error('interactive-transformation-error') to log.exception()
     - [ ] Test that exception tracebacks are properly captured
     - [ ] Commit with message: "fix: use log.exception for better error tracing in interactive_transformer"

2) Fix exception handling in factory.py
   - Context: Line 176 uses log.error() in except block, should use log.exception()
   - Files to check/modify:
     - src/nicestlog/factory.py
   - Steps:
     - [ ] Change log.error('file-logging-setup-failed') to log.exception()
     - [ ] Verify logging setup error handling works correctly
     - [ ] Commit with message: "fix: use log.exception for file logging setup errors"

3) Fix exception handling in advanced_assistant.py (4 instances)
   - Context: Lines 576, 746, 848, 896 use log.error() in except blocks
   - Files to check/modify:
     - src/nicestlog/advanced_assistant.py
   - Steps:
     - [ ] Fix line 576: transformation-error
     - [ ] Fix line 746: file-analysis-failed  
     - [ ] Fix line 848: file-transformation-failed
     - [ ] Fix line 896: file-transformation-error
     - [ ] Test AST analysis error handling
     - [ ] Commit with message: "fix: use log.exception for better error tracing in advanced_assistant"

4) Fix exception handling in config.py and i18n.py
   - Context: Remaining log.error() calls in except blocks
   - Files to check/modify:
     - src/nicestlog/config.py (line 110)
     - src/nicestlog/i18n.py (lines 73, 124)
   - Steps:
     - [ ] Fix config.py line 110: empty error message
     - [ ] Fix i18n.py line 73: failed-to-load-translations
     - [ ] Fix i18n.py line 124: translation-formatting-failed
     - [ ] Test configuration and i18n error handling
     - [ ] Commit with message: "fix: use log.exception for config and i18n error handling"

5) Validate improvements with dogfooding
   - Context: Verify that our changes actually improve the logging quality
   - Files to check/modify:
     - Run nicestlog check on the codebase
   - Steps:
     - [ ] Run `uv run python -m nicestlog check .` to verify improvements
     - [ ] Ensure no new issues were introduced
     - [ ] Document the improvement in logging quality
     - [ ] Commit with message: "docs: validate logging quality improvements via dogfooding"