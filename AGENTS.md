# 🤖 AGENTS.md (DO NOT MODIFY)

These rules are set by the human maintainer.
AI agents must follow them but may not edit this file.

## 🎯 Core Principles (The Big 7)

1. **UV-only** - Never pip, always use `uv run` prefix for Python commands
2. **Test- and logging-driven** - always write tests and add structured debug logging when adding/changing code. Run tests with `uv run pytest`.
3. **no commit without linting** - If linters are broken or missing: stop and ask the user for instructions.
4. **respect pre-commit** - observe pre-commit checks! Fix lint errors yourself. 
5. **Auto-commit** - Commit at the end without asking and print commit ID. Tell the user about unknown uncommitted changes.
6. **Timeout everything** - Use `timeout 60` for all long-running commands
7. **English artifacts** - Code, docs, commits must be in English

## 📋 Quick Check (Before finishing any task)
- [ ] Used English for all artifacts?
- [ ] Written tests for new functionality?
- [ ] pre-commit active? all errors fixed?
- [ ] Committed changes without asking and printed commit ID? 
- [ ] can i continue with the next obvious task without asking the user? Do it!

## 🧭 Additional Guidelines

- Follow conventions in CONVENTIONS.md  
- when you see dependency problems or tools don't work as expected: STOP IMMEDIATELY and ask user!
- Tell the user what you are planning to change in the code before you are doing it and talk about potential problems. Print just a short executive summary at the end of your turn.
- We can have fun while working but don't get too excited and avoid overselling success.
- Ask user before making large structural changes.
- Focus on edge cases and error handling in tests

Last updated: 2025-08-25
by human dev
