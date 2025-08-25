# CLI Framework Output Functions to Structlog Migration

Task goal
- Extend nicestlog migration capabilities to handle CLI framework output functions
- Add support for typer.echo(), click.echo(), rich.print() and other common CLI output patterns
- Research and identify other widespread CLI output functions that should be migrated
- Create migration patterns that preserve CLI-specific functionality (colors, styling, etc.)

Success criteria
- New migration type for CLI framework outputs
- Automatic detection and transformation of typer.echo, click.echo, rich.print
- Preservation of styling and formatting in structlog equivalents
- Documentation and examples showing before/after transformations
- Integration with existing migration system

Out-of-scope for this task
- Changing existing migration functionality
- Complex CLI argument parsing migrations
- Performance optimizations
- Full CLI framework integration beyond output functions

General approach (guardrails)
- English artifacts (Rule 7)
- No dependency YOLOing (Rule 3). Use `uv run` for Python commands
- Lint before committing (Rule 5). Respect pre-commit if present (Rule 6)
- Only add tests when we change code (Rule 4)

Prioritized work items (with checkboxes)

1) Research CLI framework output functions
   - Context: Identify common CLI output patterns that should be migrated
   - Files to check/modify:
     - Research notes document
     - src/nicestlog/project_analyzer.py (pattern detection)
   - Steps:
     - [x] Research typer.echo() usage patterns and parameters
     - [x] Research click.echo() usage patterns and parameters  
     - [x] Research rich.print() usage patterns and parameters
     - [x] Identify other common CLI output functions (argparse, fire, etc.)
     - [x] Document styling/formatting preservation requirements
     - [x] Analyze how these differ from regular print() statements

2) Extend pattern detection in project analyzer
   - Context: Add detection for CLI framework output functions
   - Files to check/modify:
     - src/nicestlog/project_analyzer.py
     - src/nicestlog/assistant.py (if needed)
   - Steps:
     - [x] Add CLI framework output patterns to analyzer
     - [x] Create new pattern type for CLI outputs
     - [x] Test pattern detection with sample code
     - [x] Update migration recommendation logic

3) Implement CLI output migration transformations
   - Context: Create AST transformations for CLI framework outputs
   - Files to check/modify:
     - src/nicestlog/assistant.py or new CLI-specific module
     - src/nicestlog/advanced_assistant.py (AST patterns)
   - Steps:
     - [ ] Design structlog equivalents that preserve styling
     - [ ] Implement typer.echo() → structlog transformation
     - [ ] Implement click.echo() → structlog transformation
     - [ ] Implement rich.print() → structlog transformation
     - [ ] Handle color/styling parameters appropriately
     - [ ] Add new migration type "cli-outputs-to-structlog"

4) Create tests and examples
   - Context: Ensure transformations work correctly
   - Files to check/modify:
     - tests/test_cli_output_migration.py (new)
     - examples/cli_migration_demo.py (new)
     - docs/user_guide/migration_examples.md
   - Steps:
     - [ ] Write tests for each CLI framework transformation
     - [ ] Create before/after examples showing styling preservation
     - [ ] Test edge cases (nested calls, complex parameters)
     - [ ] Add CLI migration examples to documentation
     - [ ] Commit with message: "feat: add CLI framework output migration support"

5) Integration and documentation
   - Context: Integrate with existing CLI and update docs
   - Files to check/modify:
     - src/nicestlog/cli.py (add new migration type)
     - docs/user_guide/migration_examples.md
     - README.md
   - Steps:
     - [ ] Add CLI migration type to migrate command
     - [ ] Update help text and documentation
     - [ ] Add CLI migration examples to migration guide
     - [ ] Test full migration workflow
     - [ ] Commit with message: "docs: add CLI framework migration examples and integration"