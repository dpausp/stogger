# Early Logging Format Initialization

Task goal
- Initialize internal log format early to reduce uninitialized structlog messages
- Minimize or eliminate the block of uninitialized structlog messages at startup
- Allow graceful fallback to structlog standard format if initialization fails
- Improve user experience by having consistent logging from the very beginning

Success criteria
- Significantly reduced uninitialized structlog messages at startup
- Early format initialization before any logging occurs
- Graceful fallback to standard format if initialization fails
- No breaking changes to existing functionality

Out-of-scope for this task
- Complete logging system redesign
- Changes to external logging configuration APIs
- Performance optimizations beyond initialization timing

General approach (guardrails)
- English artifacts (Rule 7)
- No dependency YOLOing (Rule 3). Use `uv run` for Python commands
- Lint before committing (Rule 5). Respect pre-commit if present (Rule 6)
- Only add tests when we change code (Rule 4)

Prioritized work items (with checkboxes)

1) Analyze current logging initialization
   - Context: Understand where and when logging format is currently set up
   - Files to check/modify:
     - src/nicestlog/__init__.py
     - src/nicestlog/__main__.py
     - src/nicestlog/cli.py
     - src/nicestlog/core.py
     - src/nicestlog/config.py
   - Steps:
     - [x] Examine current logging setup flow
     - [x] Identify where uninitialized messages occur
     - [x] Find current format initialization points
     - [x] Document current behavior

2) Design early initialization strategy
   - Context: Plan how to initialize logging format as early as possible
   - Files to check/modify:
     - src/nicestlog/__init__.py (likely main entry point)
     - src/nicestlog/core.py (core logging setup)
   - Steps:
     - [x] Design early initialization approach
     - [x] Plan fallback strategy for failed initialization
     - [x] Identify minimal dependencies for early setup
     - [x] Create implementation plan

3) Implement early logging initialization
   - Context: Actually implement the early initialization
   - Files to check/modify:
     - src/nicestlog/__init__.py (added early init call)
     - src/nicestlog/core.py (added init_early_logging function)
     - src/nicestlog/factory.py (fixed verbose debug messages)
   - Steps:
     - [x] Implement early format initialization
     - [x] Add graceful fallback handling
     - [x] Test with various scenarios
     - [x] Commit with message: "feat: initialize logging format early to reduce uninitialized messages"

4) Test and validate
   - Context: Ensure the changes work correctly and don't break anything
   - Files to check/modify:
     - tests/test_early_logging_init.py (new test file)
   - Steps:
     - [x] Add tests for early initialization
     - [x] Test fallback scenarios
     - [x] Verify no regression in existing functionality
     - [x] Run full test suite
     - [x] Commit with message: "test: add tests for early logging initialization"