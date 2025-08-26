# 🤖 AGENTS.md (DO NOT MODIFY)

These rules are set by the human maintainer. AI agents must abide all rules here. We can discuss rules, of course, but don't try any workarounds yourself!

## 🎯 Core Principles (The Big 7)

1. **Auto-commit** - FIRST check `git status` and list any uncommitted changes to the user. If there are unrelated uncommitted files, ask user what to do with them before proceeding. NEVER use `git add -A` blindly - only add files that are part of your current task. ALWAYS commit your changes after finishing your turn and print commit ID, last line, bold, full ID. Auto-commit before asking the user for next steps. In your reply, the commit line MUST be the absolute last line of the entire message. No content and no empty line after it. Use this exact format and bold: COMMIT: <full_sha>
2. **_TODO-AGENT.md** before starting a new task, write down your analysis about things we are planning. State the goal of the task. Format: Markdown, checkboxes for every step. Add relevant files you have checked that are relevant to the task. (files to check/modify, for example). **FIRST STEP: Copy TEMPLATE_TODO-AGENT.md to _TODO-AGENT.md as your starting point, then customize it for your specific task.**. When continuing the task, update the TODO file along the way to track progress at any time.
3. **No dependency YOLOing** - Never pip install, always use `uv run` prefix for all Python commands. When you see dependency problems, permission denied or shell tools don't work as expected: STOP IMMEDIATELY and ask the user!
4. **Test- and logging-driven** - always write tests and add structured debug logging when adding/changing code. Run tests with `uv run pytest`.
5. **no commit without linting** - If linters are broken or missing: stop and ask the user for instructions.
6. **respect pre-commit** - observe pre-commit checks! Fix lint errors yourself. IMPORTANT: When pre-commit makes fixes, preserve the original commit message unchanged. Pre-commit fixes are just cleanup and should not alter the meaningful commit message. 
7. **English artifacts** - Code, docs, commits must be in English

## 📋 Quick Checklist 

Check the following at the very end of your turn. Place this checklist immediately above the final commit line: 

## 🧭 Additional Guidelines

- Tell the user what you are planning to change in the code before you are doing it and talk about potential problems. Print just a short executive summary at the end of your turn.
- We can have fun while working but don't get too excited and avoid overselling success.
- Ask user before making large structural changes.
- Focus on edge cases and error handling in tests
- **Commit Message Preservation**: When pre-commit hooks make automatic fixes (ruff, black, etc.), use `git commit --amend --no-edit` to keep the original commit message unchanged. Pre-commit fixes are just cleanup work and should not be mentioned in commit messages. Examples:
  - ✅ Good: Keep original "feat: add voice feedback system" unchanged
  - ✅ Good: Keep original "fix: resolve timeout issue in notification pipeline" unchanged  
  - ❌ Bad: "ruff fixes" (loses original context)
  - ❌ Bad: "feat: add voice feedback system (pre-commit fixes)" (unnecessary noise)
- **Clean Commits**: Always check `git status` first and list uncommitted changes. Only commit files related to your current task. Never use `git add -A` blindly as it can mix unrelated changes into your commit. Examples:
  - ✅ Good: `git add AGENTS.md _TODO-AGENT.md` (only task-related files)
  - ❌ Bad: `git add -A` (might include unrelated .rgignore, config files, etc.)

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
