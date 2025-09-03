# Documentation Verification and Quality Check Task

Task goal
- Thoroughly verify all documentation for correctness and accuracy
- Eliminate redundancy and inconsistencies across documentation
- Ensure all documented commands and examples still work correctly
- Validate that documentation reflects current codebase state

Out-of-scope for this task
- Major restructuring of documentation organization
- Adding new features or functionality
- Modifying translation files in translations/ directory (runtime i18n)

General approach (guardrails)
- English artifacts (Rule 7)
- No dependency YOLOing (Rule 3). Use `uv run` for Python commands
- Lint before committing (Rule 5). Respect pre-commit if present (Rule 6)
- Test-driven approach (Rule 4) - verify all commands work

Prioritized work items (with checkboxes)

1) Inventory and scan all documentation files
   - Context: Need complete overview of documentation structure
   - Files to check/modify:
     - README.md
     - All .md files in docs/ subdirectories
     - All .rst files in docs/
     - CONVENTIONS.md
     - Any other documentation files
   - Steps:
     - [x] List all documentation files systematically
     - [x] Check file structure and organization
     - [x] Identify potential redundancies
     - [x] **FOUND CRITICAL ERROR**: README.md shows incorrect i18n command format

2) Verify command examples and code snippets
   - Context: Ensure all documented commands actually work
   - Files to check/modify:
     - docs/user_guide/*.md
     - docs/development/*.md
     - README.md
     - examples/ directory
   - Steps:
     - [x] Extract all command examples from documentation
     - [x] Test CLI commands mentioned in docs
     - [x] Verify Python code examples work
     - [x] **CRITICAL FIX NEEDED**: README.md has wrong i18n command format
     - [ ] Check that example files in examples/ are referenced correctly

3) Check for redundancy and inconsistencies
   - Context: Eliminate duplicate information and conflicting instructions
   - Files to check/modify:
     - All documentation files
   - Steps:
     - [x] Compare similar sections across different files
     - [x] Identify duplicate content
     - [x] Check for conflicting information
     - [x] **FIXED**: Corrected i18n command format across all docs
     - [x] Standardize terminology and formatting

4) Validate technical accuracy
   - Context: Ensure documentation matches current codebase
   - Files to check/modify:
     - API documentation
     - Configuration examples
     - Installation instructions
   - Steps:
     - [ ] Cross-reference with actual code implementation
     - [ ] Verify configuration options are current
     - [ ] Check that installation steps work
     - [ ] Validate API examples against current interfaces

5) Final cleanup and organization
   - Context: Polish and finalize documentation
   - Files to check/modify:
     - All documentation files
   - Steps:
     - [ ] Fix any identified issues
     - [ ] Improve clarity where needed
     - [ ] Ensure consistent formatting
     - [ ] Commit with message: "docs: comprehensive verification and quality improvements"