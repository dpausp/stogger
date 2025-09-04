# Add --version CLI Option and Document Version Management

Task goal
- Add a `--version` option to the CLI to display the current version
- Document in CONVENTIONS.md that version is managed with `uv version`
- Document in AGENTS.md that version should be bumped appropriately (minor/major) when making changes

Out-of-scope for this task
- Changing the current version number (0.3.1 is already set)
- Setting up automated version bumping
- Adding version validation

General approach (guardrails)
- English artifacts (Rule 7)
- No dependency YOLOing (Rule 3). Use `uv run` for Python commands
- Lint before committing (Rule 5). Respect pre-commit if present (Rule 6)
- Test-driven approach (Rule 4) - verify migrate command works correctly

Prioritized work items (with checkboxes)

1) Add --version option to CLI
   - Context: Users sometimes get confused about which version they're running
   - Files to check/modify:
     - src/nicestlog/cli.py (add version command)
     - pyproject.toml (check current version setup)
   - Steps:
     - [x] Add version import from package metadata
     - [x] Add --version option to main CLI app
     - [x] Test the version command works
     - [x] Commit with message: "feat(cli): add --version option"

2) Document version management in CONVENTIONS.md
   - Context: Need to clarify that uv manages the version
   - Files to check/modify:
     - CONVENTIONS.md
   - Steps:
     - [x] Add section about version management with uv
     - [x] Document `uv version` command usage
     - [x] Commit with message: "docs: document version management with uv"

3) Update AGENTS.md with version bumping guidance
   - Context: Agents should know to bump version appropriately
   - Files to check/modify:
     - AGENTS.md
   - Steps:
     - [x] Add guidance about version bumping in appropriate section
     - [x] Specify when to use minor vs major bumps
     - [ ] Commit with message: "docs: add version bumping guidance for agents"