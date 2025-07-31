# 🤖 Agent Rules (DO NOT MODIFY)

These rules are set by the human maintainer.
AI agents must follow them but may not edit this file.

❌ DON'T:

- ❌ Edit .agent.md, .gitignore, or security configs without review
- ❌ try pip, requirements.txt, setup.cfg and setup.py things
- ❌ Call pip or python without uv run prefix (WRONG: `python -m ...` vs. RIGHT: `uv run python -m ...`)
- ❌ Run commands without timeout
- ❌ Make large structural changes without discussion
- ❌ Run sudo commands (NEVER)
- ❌ Commit without clear messages


## ✅ DO

- ✅ Always use English language for artifacts
- ✅ Follow the conventions in CONVENTIONS.md. You are allowed to propose changes to that file.
- ✅ Commit significant changes automatically
- ✅ use uv for dependency management
- ✅ Use `uv run` for all Python commands
- ✅ Use `timeout 60` prefix for all long-running commands
- ✅ Look at pyproject.toml for tool and packaging related topics
- ✅ Update README.md
- ✅ Consider and document architectural decisions in ARCHITECTURE.md


## 🧭 Guidance

- 🧭 Be critical and report missing pieces (don't oversell work)
- 🧭 Present multiple numbered options when in doubt
- 🧭 Give concise answers in English
- 🧭 Focus on edge cases and error conditions in tests

Last updated: 2025-07-30
by human dev
