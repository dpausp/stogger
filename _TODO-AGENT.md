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
     - [x] Change log.error('interactive-transformation-error') to log.exception()
     - [x] Test that exception tracebacks are properly captured (revealed renderer issue)
     - [x] Commit with message: "fix: use log.exception for better error tracing in interactive_transformer"

2) Fix exception handling in factory.py
   - Context: Line 176 uses log.error() in except block, should use log.exception()
   - Files to check/modify:
     - src/nicestlog/factory.py
   - Steps:
     - [x] Change log.error('file-logging-setup-failed') to log.exception()
     - [x] Verify logging setup error handling works correctly
     - [x] Commit with message: "fix: use log.exception for file logging setup errors"

3) Fix exception handling in advanced_assistant.py (4 instances)
   - Context: Lines 576, 746, 848, 896 use log.error() in except blocks
   - Files to check/modify:
     - src/nicestlog/advanced_assistant.py
   - Steps:
     - [x] Fix line 576: transformation-error
     - [x] Fix line 746: file-analysis-failed  
     - [x] Fix line 848: file-transformation-failed
     - [x] Fix line 896: file-transformation-error
     - [x] Test AST analysis error handling (revealed renderer issue)
     - [x] Commit with message: "fix: use log.exception for better error tracing in advanced_assistant"

4) Fix exception handling in config.py and i18n.py
   - Context: Remaining log.error() calls in except blocks
   - Files to check/modify:
     - src/nicestlog/config.py (line 110)
     - src/nicestlog/i18n.py (lines 73, 124)
   - Steps:
     - [x] Fix config.py line 110: empty error message
     - [x] Fix i18n.py line 73: failed-to-load-translations
     - [x] Fix i18n.py line 124: translation-formatting-failed
     - [x] Test configuration and i18n error handling
     - [x] Commit with message: "fix: use log.exception for config and i18n error handling"

5) Validate improvements with dogfooding ✅ SUCCESS!
   - Context: Verify that our changes actually improve the logging quality
   - Files to check/modify:
     - Run nicestlog check on the codebase
   - Steps:
     - [x] Run `uv run python -m nicestlog check .` to verify improvements
     - [x] Ensure no new issues were introduced
     - [x] Document the improvement in logging quality
     - [x] Commit with message: "docs: validate logging quality improvements via dogfooding"

🎯 TASK COMPLETED SUCCESSFULLY!
- Fixed all 9 log.error() → log.exception() issues identified
- Dogfooding check confirms improvements: no more "should use log.exception()" warnings
- Tool now provides advanced suggestions about redundant error parameters
- Better exception handling with automatic tracebacks throughout codebase