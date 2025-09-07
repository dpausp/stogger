# Align nicestlog with reference logger implementation

Task goal
- Analyze differences between current nicestlog and the provided reference logger
- Identify key architectural patterns that should be adopted from the reference
- Implement missing components like MultiOptimisticLogger, SystemdJournalRenderer, etc.
- Ensure nicestlog follows the same robust multi-target logging approach

Out-of-scope for this task
- Complete rewrite of the existing codebase
- Breaking existing API compatibility
- Adding new features not present in reference logger

General approach (guardrails)
- English artifacts (Rule 7)
- No dependency YOLOing (Rule 3). Use `uv run` for Python commands
- Lint before committing (Rule 5). Respect pre-commit if present (Rule 6)
- Only add tests when we change code (Rule 4)

Prioritized work items (with checkboxes)

1) Analyze key differences between implementations
   - Context: Need to understand what's missing or different in current nicestlog
   - Files to check/modify:
     - logging.py (reference)
     - src/nicestlog/core.py
     - src/nicestlog/factory.py
   - Steps:
     - [x] Document missing components (MultiOptimisticLogger, SystemdJournalRenderer, etc.)
     - [x] Identify architectural differences
     - [x] List specific functions/classes to implement or modify

2) Implement missing core components
   - Context: Reference has MultiOptimisticLogger pattern that's missing
   - Files to check/modify:
     - src/nicestlog/core.py
     - src/nicestlog/factory.py
   - Steps:
     - [x] Add MultiOptimisticLogger and MultiOptimisticLoggerFactory
     - [x] Add SystemdJournalRenderer
     - [x] Add proper journal integration components
     - [x] Test basic functionality

3) Align console rendering and formatting
   - Context: Ensure output format matches reference implementation
   - Files to check/modify:
     - src/nicestlog/core.py (ConsoleFileRenderer)
   - Steps:
     - [x] Compare and align console output formatting
     - [x] Ensure prefix() function works like reference
     - [x] Test output formatting

4) Add missing utility functions
   - Context: Reference has several utility functions for command logging, etc.
   - Files to check/modify:
     - src/nicestlog/core.py
   - Steps:
     - [x] Add init_command_logging function
     - [x] Add drop_cmd_output_logfile function
     - [x] Add proper systemd detection and integration
     - [x] Test utility functions

5) Update init_logging to match reference pattern
   - Context: Reference init_logging has different signature and behavior
   - Files to check/modify:
     - src/nicestlog/core.py
   - Steps:
     - [x] Align function signature with reference
     - [x] Implement multi-target logger factory pattern
     - [x] Ensure backward compatibility
     - [x] Test initialization
     - [x] Commit with message: "feat: align nicestlog with reference logger architecture"