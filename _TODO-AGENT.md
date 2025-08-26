# Unified AST Analysis Output Integration

Task goal
- Merge the two separate tables from `nicestlog check` with AST analysis into one unified table
- Integrate AST analysis insights directly into the main metrics table and suggestions
- Remove the second table that is currently not helpful
- Create a single, comprehensive output that combines basic metrics with AST findings

Success criteria
- Only one table showing combined metrics (basic + AST analysis)
- AST insights flow into the main suggestions section above the table
- Better user experience with clearer, more actionable output
- No loss of useful information from current AST analysis

Out-of-scope for this task
- Changing the underlying AST analysis logic
- Modifying the core analysis algorithms
- Adding new AST patterns or transformations
- Performance optimizations

General approach (guardrails)
- English artifacts (Rule 7)
- No dependency YOLOing (Rule 3). Use `uv run` for Python commands
- Lint before committing (Rule 5). Respect pre-commit if present (Rule 6)
- Only add tests when we change code (Rule 4)
- **Dogfooding**: Use `uv run python -m nicestlog check` on our own code to validate changes

Prioritized work items (with checkboxes)

1) Analyze current table structure
   - Context: Understand the current two-table output and identify what's useful vs redundant
   - Files to check/modify:
     - src/nicestlog/cli.py (check command and display functions)
     - src/nicestlog/advanced_assistant.py (AST analysis results)
   - Steps:
     - [x] Run check command on various files to see current output
     - [x] Identify the two tables and their content
     - [x] Determine which information is valuable and which is redundant
     - [x] Map out the desired unified structure
     - [x] Commit with message: "docs: analyze current AST table output structure"

2) Design unified table structure
   - Context: Create a single table that combines the best of both current tables
   - Files to check/modify:
     - src/nicestlog/cli.py (_display_check_analysis_result function)
   - Steps:
     - [x] Design new unified table schema
     - [x] Plan how AST insights integrate into suggestions section
     - [x] Ensure all useful information is preserved
     - [x] Create mockup of desired output format
     - [x] Commit with message: "design: unified AST analysis table structure"

3) Implement unified table display
   - Context: Modify the display functions to show single unified table
   - Files to check/modify:
     - src/nicestlog/cli.py (_display_check_analysis_result, _display_check_directory_analysis)
   - Steps:
     - [x] Modify _display_check_analysis_result to show unified table
     - [x] Update _display_check_directory_analysis for consistency
     - [x] Integrate AST insights into suggestions section
     - [x] Remove redundant second table
     - [x] Commit with message: "feat: unified AST analysis table display"

4) Test and validate changes
   - Context: Ensure the new output is better and contains all necessary information
   - Files to check/modify:
     - Test with various Python files
   - Steps:
     - [x] Test on files with different complexity levels
     - [x] Test on files with and without logging issues
     - [x] Validate that all useful information is still present
     - [x] Ensure suggestions are actionable and clear
     - [x] Commit with message: "test: validate unified AST analysis output"