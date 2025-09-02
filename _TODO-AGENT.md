# Add Logging to Journal Viewer

Task goal
- Add comprehensive logging to journal_viewer.py (464 lines, currently no logging)
- Follow established logging patterns from other modules
- Ensure proper error handling and debug instrumentation
- Test the logging additions work correctly

Out-of-scope for this task
- Changing existing functionality
- Performance optimization
- Adding new features beyond logging

General approach (guardrails)
- English artifacts (Rule 7)
- No dependency YOLOing (Rule 3). Use `uv run` for Python commands
- Lint before committing (Rule 5). Respect pre-commit if present (Rule 6)
- Only add tests when we change code (Rule 4)

Prioritized work items (with checkboxes)

1) Analyze journal_viewer.py structure
   - Context: Understand the module structure and identify key logging points
   - Files to check/modify:
     - src/nicestlog/journal_viewer.py
   - Steps:
     - [x] Examine module structure and main functions
     - [x] Identify error handling locations
     - [x] Find initialization and connection points
     - [x] Plan logging strategy

2) Add logging infrastructure
   - Context: Add structlog logger and follow established patterns
   - Files to check/modify:
     - src/nicestlog/journal_viewer.py
   - Steps:
     - [x] Add structlog import and logger setup
     - [x] Add debug logging for initialization
     - [x] Add info logging for major operations
     - [x] Add warning/error logging for failure cases

3) Test logging additions
   - Context: Verify logging works and follows patterns
   - Files to check/modify:
     - tests/test_journal_viewer.py (exists - 41 tests)
   - Steps:
     - [x] Run existing tests to ensure no breakage
     - [x] Test logging output manually if needed
     - [x] Verify logging levels and messages

## Task Complete ✅

**Successfully added comprehensive logging to journal_viewer.py:**

- **Added 20+ logging statements** across all major functions
- **Structured logging** using established patterns (debug, info, warning, error)
- **Key logging points covered:**
  - Module initialization and systemd availability
  - Journal viewer creation and configuration
  - Journal query setup and execution
  - Entry parsing and processing
  - Error handling and time parsing
  - Main CLI function lifecycle

**All 41 existing tests pass** - no functionality broken
**Import test successful** - no syntax errors
**Logging follows nicestlog patterns** - structured with key-value pairs and _replace_msg