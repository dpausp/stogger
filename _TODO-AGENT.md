# Fix Log Statement Analysis in AST Integration

Task goal
- Focus AST analysis exclusively on log statements (Log, Error, Info, Logger calls)
- Fix event ID case recommendations to use kebab-case or KeepUpCase (never underscore)
- Integrate --ast into check command by default with --no-ast option
- Combine fixers to provide comprehensive suggestions (log level + event ID case together)
- Remove irrelevant function parameter analysis that's not related to logging

Success criteria
- AST analysis only analyzes actual log statements, not general functions
- Event ID case recommendations are correct (kebab-case/KeepUpCase, no underscores)
- check command runs AST analysis by default, --no-ast to disable
- Combined suggestions when multiple issues exist (e.g., wrong level + wrong case)
- No false positives about non-logging function parameters

Out-of-scope for this task
- General code complexity analysis
- Non-logging function parameter checking
- Rewriting the entire AST system architecture

General approach (guardrails)
- English artifacts (Rule 7)
- No dependency YOLOing (Rule 3). Use `uv run` for Python commands
- Lint before committing (Rule 5). Respect pre-commit if present (Rule 6)
- Only add tests when we change code (Rule 4)

Prioritized work items (with checkboxes)

1) Analyze current AST check output and identify issues
   - Context: Understand what's currently being flagged incorrectly
   - Files to check/modify:
     - src/nicestlog/cli.py (check command)
     - src/nicestlog/advanced_assistant.py
     - src/nicestlog/log_statement_analyzer.py
   - Steps:
     - [x] Run `uv run python -m nicestlog check --ast` to see current output
     - [x] Identify non-logging issues being flagged
     - [x] Check event ID case recommendation logic
     - [x] Commit with message: "docs: analyze current AST check issues"

2) Focus AST analysis on log statements only
   - Context: Remove analysis of non-logging functions and focus on logger calls
   - Files to check/modify:
     - src/nicestlog/advanced_assistant.py
     - src/nicestlog/log_statement_analyzer.py
   - Steps:
     - [x] Identify log statement detection logic
     - [x] Filter out non-logging function analysis
     - [x] Ensure only Log, Error, Info, Logger calls are analyzed
     - [x] Test with sample code containing both logging and non-logging functions
     - [x] Improved logging function detection to require multiple logging calls
     - [x] Added CLI command patterns to exclude from complexity analysis
     - [x] Added line numbers to warning messages
     - [x] Commit with message: "feat: focus AST analysis on log statements only"

3) Fix event ID case recommendations
   - Context: Ensure recommendations use kebab-case or KeepUpCase, never underscores
   - Files to check/modify:
     - src/nicestlog/advanced_assistant.py
     - src/nicestlog/log_statement_analyzer.py
   - Steps:
     - [x] Find event ID case checking logic
     - [x] Fix recommendations to suggest kebab-case/KeepUpCase
     - [x] Remove underscore suggestions
     - [x] Test with various event ID formats
     - [x] Commit with message: "fix: correct event ID case recommendations"

4) Integrate AST into check command by default
   - Context: Make --ast the default behavior with --no-ast option to disable
   - Files to check/modify:
     - src/nicestlog/cli.py
   - Steps:
     - [x] Change check command to run AST by default
     - [x] Add --no-ast boolean flag to disable
     - [x] Update help text and documentation
     - [x] Test both modes work correctly
     - [x] Commit with message: "feat: integrate AST analysis into check command by default"

5) Combine fixers for comprehensive suggestions
   - Context: When multiple issues exist, provide combined fix suggestions
   - Files to check/modify:
     - src/nicestlog/advanced_assistant.py
     - src/nicestlog/log_statement_analyzer.py
   - Steps:
     - [x] Identify how suggestions are generated
     - [x] Combine multiple fixes into single comprehensive suggestion
     - [x] Test with log statements having multiple issues
     - [x] Ensure final suggestion has correct level + correct case
     - [x] Commit with message: "feat: combine multiple fixes into comprehensive suggestions"