# Remove loguru references from codebase

Task goal
- Remove all loguru references from the codebase since it's not needed
- Clean up test files, documentation, and migration examples that mention loguru
- Ensure no functionality is broken after removal

Out-of-scope for this task
- Changing core logging functionality (nicestlog uses structlog, not loguru)
- Breaking existing migration capabilities for other logging libraries

General approach (guardrails)
- English artifacts (Rule 7)
- No dependency YOLOing (Rule 3). Use `uv run` for Python commands
- Lint before committing (Rule 5). Respect pre-commit if present (Rule 6)
- Only add tests when we change code (Rule 4)

Prioritized work items (with checkboxes)

1) Analyze current loguru references
   - Context: Found loguru references in tests, docs, and examples but not as dependency
   - Files with loguru references:
     - tests/test_log_statement_analyzer.py (import loguru, test assertions)
     - tests/test_cli_ast_integration.py (mock_deps.has_loguru = False)
     - docs/agents/migration_guide.md (mentions loguru migration)
     - docs/user_guide/migration_examples.md (loguru migration example)
     - docs/user_guide/cli_migration_guide.md (loguru migration table)
     - examples/migration_examples.py (loguru migration example)
     - src/nicestlog/log_statement_analyzer.py (comment mentioning loguru)
     - README.md (mentions loguru support)
   - Steps:
     - [x] Identify all loguru references
     - [x] Categorize by type (tests, docs, examples, code comments)
     - [x] Plan removal strategy for each category

2) Remove loguru from test files
   - Context: Tests reference loguru but it's not actually used
   - Files to modify:
     - tests/test_log_statement_analyzer.py
     - tests/test_cli_ast_integration.py
   - Steps:
     - [x] Remove loguru import and related test assertions
     - [x] Remove has_loguru mock references
     - [x] Run tests to ensure nothing breaks
     - [x] Update test coverage if needed

3) Clean up documentation references
   - Context: Documentation mentions loguru migration but user doesn't want it
   - Files to modify:
     - docs/agents/migration_guide.md
     - docs/user_guide/migration_examples.md
     - docs/user_guide/cli_migration_guide.md
     - README.md
   - Steps:
     - [x] Remove loguru migration examples
     - [x] Update migration guides to remove loguru references
     - [x] Update README.md to remove loguru mention
     - [x] Ensure documentation still makes sense

4) Remove loguru from examples
   - Context: Migration examples include loguru but it's not needed
   - Files to modify:
     - examples/migration_examples.py
   - Steps:
     - [x] Remove loguru migration example
     - [x] Ensure examples still demonstrate migration capabilities
     - [x] Test examples still work

5) Clean up code comments
   - Context: Source code has comments mentioning loguru
   - Files to modify:
     - src/nicestlog/log_statement_analyzer.py
   - Steps:
     - [ ] Remove loguru from comment examples
     - [ ] Update comment to reflect actual supported libraries
     - [ ] Ensure code functionality unchanged

6) Run comprehensive tests
   - Context: Ensure removal doesn't break anything
   - Steps:
     - [ ] Run full test suite with `uv run pytest`
     - [ ] Check that migration functionality still works for other libraries
     - [ ] Verify documentation builds correctly
     - [ ] Test CLI commands still work

7) Final cleanup and validation
   - Context: Ensure complete removal and no broken references
   - Steps:
     - [ ] Search for any remaining loguru references
     - [ ] Run linting and type checking
     - [ ] Update version if needed
     - [ ] Commit changes with proper message