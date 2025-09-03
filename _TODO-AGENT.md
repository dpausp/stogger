# Sphinx HTML Documentation Integration Task

Task goal
- Integrate Sphinx-generated HTML documentation into the package (like the existing MD files)
- Create a `docs-serve` command that opens the HTML documentation in a browser
- Ensure HTML docs are packaged and accessible when nicestlog is installed

Out-of-scope for this task
- Changing the existing Sphinx configuration or themes
- Modifying the existing `docs` command that handles MD files
- Major restructuring of documentation content

General approach (guardrails)
- English artifacts (Rule 7)
- No dependency YOLOing (Rule 3). Use `uv run` for Python commands
- Lint before committing (Rule 5). Respect pre-commit if present (Rule 6)
- Only add tests when we change code (Rule 4)

Prioritized work items (with checkboxes)

1) Examine current documentation setup and CLI structure
   - Context: Need to understand how MD docs are currently packaged and served
   - Files to check/modify:
     - src/nicestlog/cli.py (existing docs command)
     - pyproject.toml (packaging configuration)
     - docs/ directory structure
   - Steps:
     - [x] Check current CLI docs command implementation (found in cli.py lines 326-352)
     - [x] Understand how MD files are packaged via hatch.build.targets.wheel.force-include
     - [x] Check if Sphinx HTML build process exists (found in docs/_build/html/)

2) Build Sphinx HTML documentation
   - Context: Need to generate HTML docs that can be packaged
   - Files to check/modify:
     - docs/conf.py (Sphinx configuration)
     - Build process for HTML generation
   - Steps:
     - [x] Test Sphinx HTML build process (works with uv run --group docs)
     - [x] Determine output directory structure (docs/_build/html/)
     - [x] Ensure HTML docs are complete and functional

3) Update packaging to include HTML docs
   - Context: Extend existing force-include mechanism to include HTML docs
   - Files to check/modify:
     - pyproject.toml (add HTML docs to force-include)
   - Steps:
     - [x] Add HTML docs directory to hatch.build.targets.wheel.force-include
     - [x] Test that HTML docs are included in built package

4) Implement docs-serve command
   - Context: Create new CLI command that opens HTML docs in browser
   - Files to check/modify:
     - src/nicestlog/cli.py (add new command)
   - Steps:
     - [x] Add docs-serve command to CLI
     - [x] Implement logic to find packaged HTML docs
     - [x] Add browser opening functionality
     - [x] Handle both local development and installed package scenarios
     - [x] Add appropriate error handling and logging

5) Add tests for new functionality
   - Context: Ensure docs-serve command works correctly
   - Files to check/modify:
     - tests/test_cli.py or new test file
   - Steps:
     - [x] Add tests for docs-serve command
     - [x] Test HTML docs packaging
     - [x] Commit with message: "feat(cli): add docs-serve command with HTML documentation integration"