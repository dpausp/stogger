# 🤖 AGENTS.md (DO NOT MODIFY)

These rules are set by the human maintainer. AI agents must abide all rules here. We can discuss rules, of course, but don't try any workarounds yourself!

## 🎯 Core Principles (The Big 7)

1. **Auto-commit** - FIRST check `git status` and list any uncommitted changes to the user. If there are unrelated uncommitted files, ask user what to do with them before proceeding. NEVER use `git add -A` blindly - only add files that are part of your current task. ALWAYS commit your changes after finishing your turn and print commit ID, last line, bold, full ID. Auto-commit before asking the user for next steps. In your reply, the commit line MUST be the absolute last line of the entire message. No content and no empty line after it. Use this exact format and bold: COMMIT: <full_sha>
2. **_TODO-AGENT.md** before starting a new task, write down your analysis about things we are planning. State the goal of the task. Format: Markdown, checkboxes for every step. Add relevant files you have checked that are relevant to the task. (files to check/modify, for example). **FIRST STEP: Copy TEMPLATE_TODO-AGENT.md to _TODO-AGENT.md as your starting point, then customize it for your specific task.**. When continuing the task, update the TODO file along the way to track progress at any time.
3. **No dependency YOLOing** - Never pip install, always use `uv run` prefix for all Python commands. When you see dependency problems, permission denied or shell tools don't work as expected: STOP IMMEDIATELY and ask the user! Use `uv sync --all-groups --all-extras` for dependency management.
4. **Test- and logging-driven development** - Always write tests and add structured debug logging when adding/changing code. Run tests with `uv run pytest`. Aim for 90% coverage target. Use NumPy-style docstrings for all public APIs.
5. **No commit without linting** - If linters are broken or missing: stop and ask the user for instructions. Use ruff for linting and formatting (88 char line length). Run mypy for strict type checking.
6. **Respect pre-commit hooks** - Observe pre-commit checks! Fix lint errors yourself. IMPORTANT: When pre-commit makes fixes, preserve the original commit message unchanged using `git commit --amend --no-edit`. Pre-commit fixes are just cleanup and should not alter the meaningful commit message. 
7. **English artifacts** - Code, docs, commits must be in English. Use conventional commits format: `type(scope): description`

## 📋 Quick Checklist 

Check the following at the very end of your turn. Place this checklist immediately above the final commit line: 

## 🧭 Additional Guidelines

### Development Best Practices

- **Communication**: Tell the user what you are planning to change in the code before you are doing it and talk about potential problems. Print just a short executive summary at the end of your turn.
- **Tone**: We can have fun while working but don't get too excited and avoid overselling success.
- **Structural Changes**: Ask user before making large structural changes.
- **Testing Focus**: Focus on edge cases and error handling in tests. Test both happy path and error conditions.

### Version Management

When making changes that affect functionality, bump the version appropriately using `uv version`:
- `uv version patch` for bug fixes and small improvements
- `uv version minor` for new features and enhancements  
- `uv version major` for breaking changes or major refactors

### Commit Standards

- **Commit Message Preservation**: When pre-commit hooks make automatic fixes (ruff, black, etc.), use `git commit --amend --no-edit` to keep the original commit message unchanged. Pre-commit fixes are just cleanup work and should not be mentioned in commit messages.
- **Clean Commits**: Always check `git status` first and list uncommitted changes. Only commit files related to your current task. Never use `git add -A` blindly as it can mix unrelated changes into your commit.

**Examples:**
- ✅ Good: Keep original "feat: add voice feedback system" unchanged
- ✅ Good: Keep original "fix: resolve timeout issue in notification pipeline" unchanged  
- ❌ Bad: "ruff fixes" (loses original context)
- ❌ Bad: "feat: add voice feedback system (pre-commit fixes)" (unnecessary noise)
- ✅ Good: `git add AGENTS.md _TODO-AGENT.md` (only task-related files)
- ❌ Bad: `git add -A` (might include unrelated .rgignore, config files, etc.)

### Error Handling and Debugging

- **Meaningful Error Messages**: Make errors actionable - say what failed and how to fix it
- **Structured Logging**: Use structured logging with event IDs and context data
- **Exception Handling**: Log exceptions with `logger.exception()` for automatic stack traces
- **Exit Codes**: Use 0 for success, 1 for user errors, 2 for system errors

## 📋 Standard User Commands (German Prompts)

These are user prompts in German - agent also responds in German.

- **"neue todo:"** → Create new _TODO-AGENT.md from template (must be in TODO phase) do research and add content as requested by user
- **"todo:"** → Add something to existing _TODO-AGENT.md (must be in TODO phase)
- **"was ist noch offen?"** → Check _TODO-AGENT.md, report remaining tasks briefly
- **"weiter gehts"** → Continue implementing current _TODO-agent.md
- **"implementier"** → Start implementing _TODO-AGENT.md (TODO must not have checked checkboxes, yet)
- **"mach"** → Choose first available option and do it now

## 🔗 Reference to Development Conventions

Agents must follow all project-wide development conventions as defined in CONVENTIONS.md.
This includes (but is not limited to):

- **Git**: All commits must follow Conventional Commits (see CONVENTIONS.md → Git).
- **Logging**: Structured logging format must follow CONVENTIONS.md → Logging.
- **Testing**: All tests must follow pytest conventions and aim for ≥90% coverage (see CONVENTIONS.md → Testing).
- **Dependencies**: Use uv for all dependency management (see CONVENTIONS.md → Dependencies).
- **CLI Design**: Generated CLI code must follow CONVENTIONS.md → CLI Design.
- **Documentation**: Use NumPy-style docstrings for all public APIs (see CONVENTIONS.md → Documentation).

In case of conflict between AGENTS.md and CONVENTIONS.md, AGENTS.md takes precedence (agent guardrails).

## Message Footer Format (MANDATORY)

- Always end your message with:
  1) The Quick Checklist (completed), and then
  2) A single final line containing the bolded commit line.

- If you made changes:
  - Final line must be exactly:
    - COMMIT: <full_sha>
  - This line must be the last line in the whole message (no trailing newline/empty line).

- If you made no changes this turn:
  - Final line must be exactly:
    - NO COMMIT THIS TURN
  - This line must be the last line in the whole message (no trailing newline/empty line).

Example (end of message only):
- [x] Used English for all artifacts?
- [x] Written tests for new functionality?
- [x] pre-commit active? all errors fixed?
- [x] _TODO-AGENT.md up-to-date? What's left, are we finished?
- [x] Can you (the agent) continue with the next obvious sub task from _TODO-AGENT.md without asking the user? Tell the user and just Do it!
- [x] Committed changes without asking and printed commit ID?
COMMIT: 372d620472e6062bf70e916753a85bff9c64cbd8

Last updated: 2025-08-25
by human dev
