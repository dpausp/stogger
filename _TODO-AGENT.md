# Test Coverage Improvement Implementation

Task goal
- Implement comprehensive tests for the highest priority uncovered code
- Add interactive CLI integration tests with pexpect for user-centric testing
- Add end-to-end integration tests for CLI migration and linter functionality
- Increase overall test coverage from 62% to 75-80%
- Focus on recently created features that lack tests but are fully functional
- Ensure critical error handling paths are properly tested
- Cover interactive CLI functions that were previously "intentionally untested"

Success criteria
- cli_output_transformer.py coverage: 18% → 80%+ (add ~160 lines of coverage)
- log_statement_analyzer.py coverage: 18% → 80%+ (add ~155 lines of coverage)
- systemd_integration.py coverage: 42% → 70%+ (add ~50 lines of coverage)
- Interactive CLI functions tested with pexpect (init_config, docs, demos)
- End-to-end migration testing with real file transformations
- Integration testing for linter with realistic codebases
- Overall project coverage: 62% → 75%+ (add ~365+ lines of coverage)
- All new tests pass and follow existing test patterns
- No regression in existing functionality
- Interactive functions work reliably in real user scenarios

Out-of-scope for this task
- Refactoring existing code (only add tests)
- Performance benchmarking or stress testing
- Testing experimental features (live_editor.py) - low priority  
- Major architectural changes
- Web dashboard testing (Flask optional dependency)

General approach (guardrails)
- English artifacts (Rule 7)
- No dependency YOLOing (Rule 3). Use `uv run` for Python commands
- Lint before committing (Rule 5). Respect pre-commit if present (Rule 6)
- Only add tests when we change code (Rule 4) - we're adding tests for existing code
- Auto-commit after each module (Rule 1)
- Write comprehensive tests, not just coverage fillers (Rule 2)

Prioritized work items (with checkboxes)

1) Add comprehensive tests for cli_output_transformer.py ✅ COMPLETED
   - Context: Recently created CLI migration feature (Aug 26) with 18% coverage, 196 uncovered lines
   - Effort estimate: 4-6 hours (complex AST transformations)
   - Risk: High complexity - AST manipulation and code transformation logic
   - Files to check/modify:
     - src/nicestlog/cli_output_transformer.py (understand functionality)
     - tests/test_cli_output_transformer.py (create new test file)
   - Steps:
     - [x] Analyze existing functionality and transformation patterns
     - [x] Create test file with basic structure and imports
     - [x] Test typer.echo() → structlog transformations
     - [x] Test click.echo() → structlog transformations  
     - [x] Test rich.print() → structlog transformations
     - [x] Test edge cases: nested calls, complex expressions, error handling
     - [x] Test AST manipulation edge cases and malformed code handling
     - [x] Verify coverage increase to 80%+
     - [x] Commit with message: "test: add comprehensive tests for cli_output_transformer"

   **OUTSTANDING RESULTS:**
   - **Coverage improvement: 18% → 93% (75 percentage point increase!)**
   - **Lines covered: 221/238 (only 17 lines remaining uncovered)**
   - **48 comprehensive tests created** covering all major functionality:
     - CLIOutputCall dataclass and transformer initialization
     - String slugification and event name generation
     - AST visitor methods for imports and assignments
     - Detection and transformation for all CLI frameworks:
       * typer.echo() with styling options
       * click.echo() with stderr support
       * rich.print() and Console.print() with styles
       * argparse.error() and sys.write() calls
     - Edge cases: complex expressions, multiple calls, error handling
     - Integration testing with migrate_cli_outputs_file() and analyze_cli_outputs_in_file()
   
   **Target exceeded: 93% > 80% target**

2) Add comprehensive tests for log_statement_analyzer.py ✅ COMPLETED
   - Context: Recently created linter enhancement (Aug 15) with 18% coverage, 195 uncovered lines
   - Effort estimate: 3-4 hours (AST analysis patterns)
   - Risk: Medium complexity - AST analysis and pattern detection
   - Files to check/modify:
     - src/nicestlog/log_statement_analyzer.py (understand analysis patterns)
     - tests/test_log_statement_analyzer.py (create new test file)
   - Steps:
     - [x] Analyze existing log statement detection patterns
     - [x] Create test file with basic structure and imports
     - [x] Test detection of missing event IDs in log statements
     - [x] Test detection of format string problems
     - [x] Test detection of incorrect log levels
     - [x] Test edge cases: complex log statements, nested calls
     - [x] Test AST analysis edge cases and malformed code handling
     - [x] Verify coverage increase to 80%+
     - [x] Commit with message: "test: add comprehensive tests for log_statement_analyzer"

   **OUTSTANDING RESULTS:**
   - **Coverage improvement: 18% → 84% (66 percentage point increase!)**
   - **Lines covered: 200/238 (only 38 lines remaining uncovered)**
   - **42 comprehensive tests created** covering all major functionality:
     - LogStatement and LogAnalysisResult dataclasses
     - LogStatementAnalyzer initialization and configuration
     - AST visitor methods for imports, assignments, and calls
     - Logger factory call detection and logger variable tracking
     - Event ID format detection (dash-case, snake_case, camelCase, PascalCase, invalid)
     - Event ID format conversion utilities
     - Comprehensive issue detection:
       * Missing event IDs
       * Event ID format violations
       * Single string argument anti-patterns
       * F-string usage in event IDs
       * Debug with _replace_msg issues
       * Too many keyword arguments
       * Missing structured data
       * Log level and event severity mismatches
       * Potential secret leakage detection
       * Overly long event IDs
     - Complete log statement parsing for various scenarios:
       * Simple and complex log statements
       * Magic arguments (_replace_msg, exc_info)
       * Multiple statements in files
       * Chained logger calls (structlog.get_logger().info())
       * Self.logger attribute access
       * Complex expressions in arguments
     - File analysis integration testing:
       * Valid Python files with good logging
       * Files with various logging issues
       * Syntax error handling
       * Non-existent file handling
       * Snake_case preference configuration
     - Print analysis summary functionality with verbose mode
   
   **Target exceeded: 84% > 80% target**

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

4) Add error handling tests for CLI commands ✅ COMPLETED
   - Context: CLI module has 52% coverage with many uncovered error handling paths
   - Effort estimate: 3-4 hours (CLI error scenarios)
   - Risk: Low-Medium complexity - CLI error simulation and mocking
   - Files to check/modify:
     - src/nicestlog/cli.py (understand error paths)
     - tests/test_cli.py (enhance existing tests)
   - Steps:
     - [x] Analyze uncovered CLI error handling paths
     - [x] Add tests for file not found scenarios
     - [x] Add tests for permission denied scenarios
     - [x] Add tests for invalid configuration scenarios
     - [x] Add tests for command argument validation errors
     - [x] Add tests for dependency unavailable scenarios (Flask, systemd)
     - [x] Verify coverage increase for critical CLI paths
     - [x] Commit with message: "test: add error handling tests for CLI commands"

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

6) Add interactive CLI integration tests with pexpect
   - Context: Interactive CLI functions (init_config, docs browser, demos) need user-centric integration testing
   - Effort estimate: 3-4 hours (interactive testing setup and scenarios)
   - Risk: Medium complexity - user interaction simulation and timing issues
   - Files to check/modify:
     - src/nicestlog/cli.py (interactive functions: init_config_cmd, _show_docs_interactive, tools_demo)
     - tests/test_cli_interactive.py (create new test file)
     - pyproject.toml (add pexpect dependency for testing)
   - Steps:
     - [ ] Add pexpect to test dependencies in pyproject.toml
     - [ ] Create interactive test infrastructure with pexpect
     - [ ] Test init_config_cmd wizard: user inputs, file creation, validation
     - [ ] Test docs browser: navigation, search, exit scenarios
     - [ ] Test demo runners: interactive prompts, user choices, error handling
     - [ ] Test CLI help and --help interactions
     - [ ] Test keyboard interrupts (Ctrl+C) and graceful exits
     - [ ] Test invalid user inputs and error recovery
     - [ ] Test timeout scenarios and hanging processes
     - [ ] Verify interactive functions work end-to-end
     - [ ] Commit with message: "test: add interactive CLI integration tests with pexpect"

7) Add CLI migration integration tests
   - Context: CLI migration commands need end-to-end testing with real file transformations
   - Effort estimate: 2-3 hours (file-based integration testing)
   - Risk: Medium complexity - file system operations and real code transformations
   - Files to check/modify:
     - src/nicestlog/cli.py (migrate command)
     - src/nicestlog/cli_output_transformer.py (transformation logic)
     - tests/test_cli_migration_integration.py (create new test file)
   - Steps:
     - [ ] Create test fixtures with sample Python files containing typer.echo(), click.echo(), rich.print()
     - [ ] Test end-to-end migration: `nicestlog migrate --type cli-outputs-to-structlog`
     - [ ] Verify file transformations are correct and preserve functionality
     - [ ] Test migration with different file structures and edge cases
     - [ ] Test migration error handling: permission denied, invalid files, backup failures
     - [ ] Test migration dry-run mode and preview functionality
     - [ ] Test migration with gitignore integration
     - [ ] Verify no data loss and proper backup creation
     - [ ] Commit with message: "test: add CLI migration integration tests"

8) Add linter integration tests with real codebases
   - Context: Linter functionality needs testing with realistic code examples
   - Effort estimate: 2-3 hours (realistic codebase testing)
   - Risk: Low-Medium complexity - code analysis on real examples
   - Files to check/modify:
     - src/nicestlog/linter.py (linting logic)
     - src/nicestlog/log_statement_analyzer.py (analysis patterns)
     - tests/test_linter_integration.py (create new test file)
   - Steps:
     - [ ] Create test fixtures with realistic Python codebases
     - [ ] Test end-to-end linting: `nicestlog lint --analyze-statements`
     - [ ] Test linter with various log statement patterns and issues
     - [ ] Test linter performance with larger codebases
     - [ ] Test linter configuration and customization options
     - [ ] Test linter output formatting and reporting
     - [ ] Test linter integration with pre-commit hooks
     - [ ] Verify linter catches real issues and provides helpful suggestions
     - [ ] Commit with message: "test: add linter integration tests with real codebases"

9) Verify overall coverage improvement and cleanup
   - Context: Ensure coverage targets are met and cleanup temporary files
   - Effort estimate: 30 minutes (verification and cleanup)
   - Risk: Low - verification and cleanup task
   - Files to check/modify:
     - Coverage reports and temporary analysis files
     - pyproject.toml (test dependencies)
   - Steps:
     - [ ] Run comprehensive coverage report including integration tests
     - [ ] Verify overall coverage increased to 75%+
     - [ ] Verify target modules reached coverage goals
     - [ ] Verify interactive and integration tests provide meaningful coverage
     - [ ] Clean up temporary analysis files (tmp_rovodev_*)
     - [ ] Update documentation with new coverage metrics and test types
     - [ ] Commit with message: "docs: update coverage metrics after comprehensive test improvements"