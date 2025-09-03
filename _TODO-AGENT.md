# Documentation Translation to English Task

Task goal
- Translate all documentation files to English (following Rule 7: English artifacts)
- Ensure consistent English language across all docs, comments, and text content
- Check and update any German or other non-English content

Out-of-scope for this task
- Changing functionality or code logic
- Modifying translation files in translations/ directory (these are for runtime i18n)
- Restructuring documentation organization

General approach (guardrails)
- English artifacts (Rule 7)
- No dependency YOLOing (Rule 3). Use `uv run` for Python commands
- Lint before committing (Rule 5). Respect pre-commit if present (Rule 6)
- Only add tests when we change code (Rule 4)

Prioritized work items (with checkboxes)

1) Scan documentation for non-English content
   - Context: Need to identify what needs translation
   - Files to check/modify:
     - All .md and .rst files in docs/
     - README.md and other root documentation
     - Any comments or text in code files
   - Steps:
     - [x] Search for German text patterns in documentation
     - [x] Check translations directory structure
     - [x] Identify specific files needing translation
     - Found: todo_ast_integration.md contains German content

2) Translate identified content to English
   - Context: Convert non-English content to proper English
   - Files to check/modify: 
     - todo_ast_integration.md (German → English)
   - Steps:
     - [x] Translate todo_ast_integration.md from German to English
     - [x] Ensure consistent English terminology
     - [x] Commit with message: "docs: translate all documentation to English"