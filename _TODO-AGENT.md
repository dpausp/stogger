# Test Coverage Improvement Implementation

Task goal
- Implement comprehensive tests for the highest priority uncovered code
- Increase overall test coverage from 62% to 75-80%
- Focus on recently created features that lack tests but are fully functional
- Ensure critical error handling paths are properly tested

Success criteria
- cli_output_transformer.py coverage: 18% → 80%+ (add ~160 lines of coverage)
- log_statement_analyzer.py coverage: 18% → 80%+ (add ~155 lines of coverage)
- systemd_integration.py coverage: 42% → 70%+ (add ~50 lines of coverage)
- Overall project coverage: 62% → 75%+ (add ~365 lines of coverage)
- All new tests pass and follow existing test patterns
- No regression in existing functionality

Out-of-scope for this task
- Refactoring existing code (only add tests)
- Testing intentionally untested code (CLI wizards, demos, display helpers)
- Performance or integration testing
- Testing experimental features (live_editor.py) - low priority
- Major architectural changes

General approach (guardrails)
- English artifacts (Rule 7)
- No dependency YOLOing (Rule 3). Use `uv run` for Python commands
- Lint before committing (Rule 5). Respect pre-commit if present (Rule 6)
- Only add tests when we change code (Rule 4) - we're adding tests for existing code
- Auto-commit after each module (Rule 1)
- Write comprehensive tests, not just coverage fillers (Rule 2)

Prioritized work items (with checkboxes)

1) Add comprehensive tests for cli_output_transformer.py
   - Context: Recently created CLI migration feature (Aug 26) with 18% coverage, 196 uncovered lines
   - Effort estimate: 4-6 hours (complex AST transformations)
   - Risk: High complexity - AST manipulation and code transformation logic
   - Files to check/modify:
     - src/nicestlog/cli_output_transformer.py (understand functionality)
     - tests/test_cli_output_transformer.py (create new test file)
   - Steps:
     - [ ] Analyze existing functionality and transformation patterns
     - [ ] Create test file with basic structure and imports
     - [ ] Test typer.echo() → structlog transformations
     - [ ] Test click.echo() → structlog transformations  
     - [ ] Test rich.print() → structlog transformations
     - [ ] Test edge cases: nested calls, complex expressions, error handling
     - [ ] Test AST manipulation edge cases and malformed code handling
     - [ ] Verify coverage increase to 80%+
     - [ ] Commit with message: "test: add comprehensive tests for cli_output_transformer"

2) Add comprehensive tests for log_statement_analyzer.py
   - Context: Recently created linter enhancement (Aug 15) with 18% coverage, 195 uncovered lines
   - Effort estimate: 3-4 hours (AST analysis patterns)
   - Risk: Medium complexity - AST analysis and pattern detection
   - Files to check/modify:
     - src/nicestlog/log_statement_analyzer.py (understand analysis patterns)
     - tests/test_log_statement_analyzer.py (create new test file)
   - Steps:
     - [ ] Analyze existing log statement detection patterns
     - [ ] Create test file with basic structure and imports
     - [ ] Test detection of missing event IDs in log statements
     - [ ] Test detection of format string problems
     - [ ] Test detection of incorrect log levels
     - [ ] Test edge cases: complex log statements, nested calls
     - [ ] Test AST analysis edge cases and malformed code handling
     - [ ] Verify coverage increase to 80%+
     - [ ] Commit with message: "test: add comprehensive tests for log_statement_analyzer"

3) Add error handling tests for systemd_integration.py
   - Context: System integration module with 42% coverage, needs robust error handling tests
   - Effort estimate: 2-3 hours (system integration edge cases)
   - Risk: Medium complexity - system dependencies and error simulation
   - Files to check/modify:
     - src/nicestlog/systemd_integration.py (understand error paths)
     - tests/test_systemd_integration.py (enhance existing tests)
   - Steps:
     - [ ] Analyze uncovered error handling paths
     - [ ] Add tests for systemd unavailable scenarios
     - [ ] Add tests for journal access permission errors
     - [ ] Add tests for malformed journal entries
     - [ ] Add tests for systemd service integration edge cases
     - [ ] Test configuration validation and error handling
     - [ ] Verify coverage increase to 70%+
     - [ ] Commit with message: "test: add error handling tests for systemd_integration"

4) Add error handling tests for CLI commands
   - Context: CLI module has 52% coverage with many uncovered error handling paths
   - Effort estimate: 3-4 hours (CLI error scenarios)
   - Risk: Low-Medium complexity - CLI error simulation and mocking
   - Files to check/modify:
     - src/nicestlog/cli.py (understand error paths)
     - tests/test_cli.py (enhance existing tests)
   - Steps:
     - [ ] Analyze uncovered CLI error handling paths
     - [ ] Add tests for file not found scenarios
     - [ ] Add tests for permission denied scenarios
     - [ ] Add tests for invalid configuration scenarios
     - [ ] Add tests for command argument validation errors
     - [ ] Add tests for dependency unavailable scenarios (Flask, systemd)
     - [ ] Verify coverage increase for critical CLI paths
     - [ ] Commit with message: "test: add error handling tests for CLI commands"

5) Add edge case tests for core modules
   - Context: Core modules need better edge case coverage for robustness
   - Effort estimate: 2-3 hours (edge cases and error paths)
   - Risk: Low complexity - well-understood core functionality
   - Files to check/modify:
     - src/nicestlog/core.py (formatter edge cases)
     - src/nicestlog/pii_scrubber.py (data protection edge cases)
     - tests/test_core.py, tests/test_pii_scrubber.py (enhance existing tests)
   - Steps:
     - [ ] Add tests for formatter exception handling
     - [ ] Add tests for malformed log data handling
     - [ ] Add tests for PII scrubber edge cases (complex patterns)
     - [ ] Add tests for unicode and encoding edge cases
     - [ ] Add tests for memory/performance edge cases
     - [ ] Verify coverage improvements
     - [ ] Commit with message: "test: add edge case tests for core modules"

6) Verify overall coverage improvement and cleanup
   - Context: Ensure coverage targets are met and cleanup temporary files
   - Effort estimate: 30 minutes (verification and cleanup)
   - Risk: Low - verification and cleanup task
   - Files to check/modify:
     - Coverage reports and temporary analysis files
   - Steps:
     - [ ] Run comprehensive coverage report
     - [ ] Verify overall coverage increased to 75%+
     - [ ] Verify target modules reached coverage goals
     - [ ] Clean up temporary analysis files (tmp_rovodev_*)
     - [ ] Update documentation with new coverage metrics
     - [ ] Commit with message: "docs: update coverage metrics after test improvements"