# Coverage Analysis and Code Classification

Task goal
- Analyze test coverage for each code file in the nicestlog project
- Classify uncovered code to determine if it's unused code or needs tests
- Create classification for each function/class/method per module
- Identify gaps in test coverage and prioritize what needs testing
- Ensure no unused modules exist (hopefully!)

Success criteria
- Complete coverage analysis of all source code files
- Classification of every uncovered function/class/method
- Documented decisions: unused code vs needs tests vs intentionally untested
- Improved understanding of test coverage gaps
- Action plan for improving critical coverage areas

Out-of-scope for this task
- Actually writing new tests (separate task)
- Major refactoring of existing code
- Coverage of dependencies in .venv/
- Performance testing or integration testing analysis

General approach (guardrails)
- English artifacts (Rule 7)
- No dependency YOLOing (Rule 3). Use `uv run` for Python commands
- Lint before committing (Rule 5). Respect pre-commit if present (Rule 6)
- Only add tests when we change code (Rule 4)

Prioritized work items (with checkboxes)

1) Generate comprehensive test coverage report ✅ COMPLETED
   - Context: Need baseline coverage data to analyze what's not covered
   - Files to check/modify:
     - All src/nicestlog/ files
     - Coverage report generation
   - Steps:
     - [x] Run coverage analysis with detailed reporting
     - [x] Generate HTML coverage report for visual analysis
     - [x] Export coverage data in machine-readable format
     - [ ] Commit with message: "docs: add comprehensive coverage analysis report"

   **Coverage Summary:**
   - **Overall Coverage: 62% (3154/5127 lines)**
   - **High Coverage (>80%):** 9 modules
   - **Medium Coverage (50-80%):** 8 modules  
   - **Low Coverage (<50%):** 7 modules
   
   **Critical Findings:**
   - cli.py: 52% coverage (554/1153 lines uncovered) - largest gap
   - cli_output_transformer.py: 18% coverage (196/238 lines uncovered)
   - live_editor.py: 24% coverage (135/178 lines uncovered)
   - log_statement_analyzer.py: 18% coverage (195/238 lines uncovered)
   - web_dashboard.py: 22% coverage (79/101 lines uncovered)

2) Analyze uncovered code in core modules ⚠️ IN PROGRESS
   - Context: Identify what code lacks test coverage and why
   - Files to check/modify:
     - src/nicestlog/core.py
     - src/nicestlog/config.py
     - src/nicestlog/cli.py
     - Other high-priority core modules
   - Steps:
     - [x] Classify each uncovered function/method/class
     - [x] Determine: unused vs needs-tests vs intentionally-untested
     - [ ] Document findings with reasoning
     - [ ] Commit with message: "docs: classify uncovered code in core modules"

   **CLI.py Analysis (52% coverage, 554 missing lines):**
   - **INTENTIONALLY UNTESTED:** Interactive CLI functions (docs, init_config wizard, demo runners)
   - **NEEDS TESTS:** Error handling paths, edge cases in CLI commands
   - **CONDITIONAL CODE:** Flask dashboard (only when Flask available), systemd journal (only when systemd available)
   - **HELPER FUNCTIONS:** Many display/formatting functions used by CLI commands
   
   **Core.py Analysis (83% coverage, 53 missing lines):**
   - **NEEDS TESTS:** Exception handling paths, edge cases in formatters
   - **INTENTIONALLY UNTESTED:** Some utility functions and error recovery paths
   
   **Config.py Analysis (93% coverage, 4 missing lines):**
   - **EXCELLENT:** Only 4 missing lines, mostly error handling

3) Analyze uncovered code in feature modules
   - Context: Feature modules may have optional/experimental code
   - Files to check/modify:
     - src/nicestlog/advanced_assistant.py
     - src/nicestlog/web_dashboard.py
     - src/nicestlog/systemd_integration.py
     - Other feature modules
   - Steps:
     - [ ] Classify uncovered feature code
     - [ ] Identify experimental vs stable vs deprecated features
     - [ ] Document test coverage priorities
     - [ ] Commit with message: "docs: classify uncovered code in feature modules"

4) Analyze uncovered code in utility modules
   - Context: Utility modules often have edge cases or error handling
   - Files to check/modify:
     - src/nicestlog/i18n.py
     - src/nicestlog/pii_scrubber.py
     - src/nicestlog/linter.py
     - Other utility modules
   - Steps:
     - [ ] Classify uncovered utility functions
     - [ ] Identify error handling vs edge cases vs dead code
     - [ ] Prioritize critical vs nice-to-have coverage
     - [ ] Commit with message: "docs: classify uncovered code in utility modules"

5) Create coverage improvement action plan
   - Context: Synthesize findings into actionable recommendations
   - Files to check/modify:
     - Coverage analysis summary document
     - Test priority recommendations
   - Steps:
     - [ ] Summarize coverage gaps by priority
     - [ ] Identify truly unused code for removal
     - [ ] Create test writing priorities
     - [ ] Document coverage targets and rationale
     - [ ] Commit with message: "docs: create coverage improvement action plan"