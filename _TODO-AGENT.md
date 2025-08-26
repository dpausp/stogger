# Detect Log Wrappers Anti-Pattern

Task goal
- Implement detection of log wrapper anti-patterns in both `check` and `migrate` commands
- Identify code that unnecessarily wraps logging calls with additional indirection
- Warn users about these patterns without automatically fixing them
- Help developers recognize when they're building unnecessary abstractions around logging

Success criteria
- `check` command detects and reports log wrapper patterns
- `migrate` command warns about log wrappers during migration analysis
- Clear warning messages that explain why log wrappers are problematic
- No automatic fixes - just detection and warnings

Out-of-scope for this task
- Automatically fixing or migrating log wrapper patterns
- Complex static analysis beyond basic pattern recognition
- Performance optimizations
- Adding new CLI commands

General approach (guardrails)
- English artifacts (Rule 7)
- No dependency YOLOing (Rule 3). Use `uv run` for Python commands
- Lint before committing (Rule 5). Respect pre-commit if present (Rule 6)
- Only add tests when we change code (Rule 4)

Prioritized work items (with checkboxes)

1) Analyze existing codebase for log wrapper detection patterns
   - Context: Need to understand current architecture and where to add detection
   - Files to check/modify:
     - src/nicestlog/linter.py (likely place for check command logic)
     - src/nicestlog/cli.py (check and migrate commands)
     - src/nicestlog/project_analyzer.py (migration analysis)
   - Steps:
     - [x] Examine current linter and analyzer architecture
     - [x] Identify common log wrapper patterns to detect
     - [x] Research AST patterns for wrapper detection

2) Define log wrapper patterns to detect
   - Context: Need clear criteria for what constitutes a problematic log wrapper
   - Files to check/modify:
     - New pattern definitions (possibly in linter.py or separate module)
   - Steps:
     - [x] Define AST patterns for function wrappers around logging calls
     - [x] Identify indirect logging call patterns
     - [x] Create examples of good vs bad logging patterns
     - [x] Document detection criteria

3) Implement detection in check command
   - Context: Add log wrapper detection to existing linting functionality
   - Files to check/modify:
     - src/nicestlog/linter.py
     - tests/test_linter_*.py
   - Steps:
     - [x] Add log wrapper detection logic to linter
     - [x] Create appropriate warning messages
     - [x] Write tests for wrapper detection
     - [x] Commit with message: "feat: add log wrapper detection to check command"

4) Implement detection in migrate command
   - Context: Warn about log wrappers during migration analysis
   - Files to check/modify:
     - src/nicestlog/project_analyzer.py or relevant migration module
     - tests/test_cli_*.py (migration tests)
   - Steps:
     - [x] Add wrapper detection to migration analysis
     - [x] Create migration-specific warning messages
     - [x] Write tests for migration wrapper warnings
     - [x] Commit with message: "feat: add log wrapper warnings to migrate command"

5) Documentation and examples
   - Context: Help users understand what log wrappers are and why to avoid them
   - Files to check/modify:
     - docs/ files
     - examples/ (potentially)
   - Steps:
     - [ ] Document log wrapper anti-patterns
     - [ ] Add examples of problematic vs good logging patterns
     - [ ] Update CLI help text if needed
     - [ ] Commit with message: "docs: add log wrapper anti-pattern documentation"