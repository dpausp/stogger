# Fix AST Integration Issues in Check Command

Task goal
- Fix the broken AST integration in the check command that's analyzing irrelevant code and flagging normal functions
- Implement proper gitignore respect for AST analysis
- Improve AST output to be more focused on logging-related issues
- Remove irrelevant complexity checks that flag normal functions like `init` with 6 parameters

Success criteria
- AST analysis only analyzes project files (respects .gitignore)
- AST analysis focuses on logging-related patterns, not general code complexity
- Clean, organized output that's actually useful for logging improvements
- No false positives about function parameter counts for non-logging functions

Out-of-scope for this task
- Rewriting the entire AST system
- Changing the core AdvancedAssistant functionality beyond filtering
- Adding new AST patterns (focus on fixing existing integration)

General approach (guardrails)
- English artifacts (Rule 7)
- No dependency YOLOing (Rule 3). Use `uv run` for Python commands
- Lint before committing (Rule 5). Respect pre-commit if present (Rule 6)
- Only add tests when we change code (Rule 4)

Prioritized work items (with checkboxes)

1) Investigate current AST integration issues
   - Context: Understand why AST is analyzing irrelevant code and flagging normal functions
   - Files to check/modify:
     - src/nicestlog/cli.py (check command)
     - src/nicestlog/advanced_assistant.py
     - src/nicestlog/linter.py
   - Steps:
     - [x] Create test file to reproduce issues
     - [x] Run check --ast to see current behavior
     - [x] Analyze why it's flagging init function with 6 parameters
     - [x] Check if gitignore is being respected
     - [ ] Commit with message: "docs: analyze AST integration issues in check command"

2) Fix gitignore respect in AST analysis
   - Context: AST should not analyze files that are in .gitignore
   - Files to check/modify:
     - src/nicestlog/cli.py
     - src/nicestlog/advanced_assistant.py
   - Steps:
     - [ ] Add gitignore parsing functionality
     - [ ] Filter files before AST analysis
     - [ ] Test with common gitignore patterns
     - [ ] Commit with message: "feat: respect .gitignore in AST analysis"

3) Focus AST patterns on logging-related issues
   - Context: Remove irrelevant complexity checks, focus on logging quality
   - Files to check/modify:
     - src/nicestlog/advanced_assistant.py
     - src/nicestlog/cli.py
   - Steps:
     - [ ] Disable general complexity patterns for check command
     - [ ] Enable only logging-related patterns
     - [ ] Update pattern filtering logic
     - [ ] Test with logging-focused analysis
     - [ ] Commit with message: "feat: focus AST analysis on logging patterns in check command"

4) Improve AST output formatting and organization
   - Context: Make output more useful and less cluttered
   - Files to check/modify:
     - src/nicestlog/cli.py
   - Steps:
     - [ ] Improve issue categorization (logging vs general)
     - [ ] Add better descriptions for logging-specific issues
     - [ ] Clean up output formatting
     - [ ] Add summary of logging improvements suggested
     - [ ] Commit with message: "feat: improve AST analysis output for logging focus"

5) Add configuration for AST analysis scope
   - Context: Allow users to control what AST analyzes
   - Files to check/modify:
     - src/nicestlog/config.py
     - src/nicestlog/cli.py
   - Steps:
     - [ ] Add AST configuration options
     - [ ] Allow disabling specific pattern categories
     - [ ] Add logging-only mode
     - [ ] Update documentation
     - [ ] Commit with message: "feat: add configuration for AST analysis scope"