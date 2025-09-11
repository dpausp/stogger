# 🤖 AGENTS.md

These rules for AI agents are set by the human maintainer. AI agents must abide all rules here. We can discuss rules, of course, but don't try any workarounds yourself!

## 🎯 Core Principles (The Big 7)

1. **Respect defined Agent workflow** (Rule 1) - Agents have to trigger mandatory Agent workflow events, see below.
1. **Analyze and Plan in \_TODO-AGENT.md** (Rule 2) - NO code changes in TODO phase. Only changes to \_TODO-AGENT.md allowed. This is the reference for implementing coding tasks later. When in TODO phase, stay in TODO phase.
1. **TODO-First, user is responsible for switch to IMPL** (Rule 3) - Never implement anything when in TODO phase, just continue working on TODO only. User switches to IMPL phase explicitly, NEVER assume that you can just start coding on your own!
1. **Always use Git** (Rule 4) - Always commit workdir changes, manage gitignore and remember to show the commit ID to the user directly after commit.
1. **No dependency YOLOing** (Rule 5) - FORBIDDEN, NOT YOUR BUSINESS: calling package managers like pip, apt or even docker. Assume that dependencies are properly handled externally. That also means: NEVER use "fallbacks" or "workarounds" in code when imports are not available. When you see dependency problems or permission issues: STOP IMMEDIATELY and ask the user!
1. **No legacy support, let it crash, log and test** (Rule 6) - NEVER add backwards compatibility code. Just don't support legacy stuff. Assume that legacy code/config is updated externally. Also, NEVER add `try...except` that doesn't re-raise exceptions, don't suppress errors or continue in any way when errors occur. Exceptions STOP program execution. We need to see failures, exceptions, stack traces first. Instead, use verbose structured debug logging that makes it easy to figure out what happened before the crash. Always write unit tests. VERY IMPORTANT: `except` clauses MUST be fully covered!
1. **English for artifacts** (Rule 7) - Everything commited to the repository, code, docs, commit messages, markdown files, TODO files must be in English.

## 🧩 Agent Workflow Events

Agent workflow events are `doit` tasks prefixed with `agent-`. You can check all tasks and descriptions using `uv run doit list | grep agent-`.

In this section, events are referred to without the `agent-` prefix sometimes.

**TODO phase Flow:** start → coding-start → coding-checkpoint(s) → pre-commit → post-commit
**IMPL phase Flow:** start → todo-start → pre-commit → post-commit
**DISCUSS phase Flow:** none, just answer

Calling workflow events will give further instructions aligned with the current state and agent rules in this document.

### Mandatory general events

All these general events MUST be called explicitly (report to user!) in any phase, in the following order.

- `uv run doit agent-start` - **Universal entry point** - Call this first as early as possible.
- `uv run doit agent-pre-commit` - Call this when changes are finished and you are ready for Git commit (run check/fix/test).
- `uv run doit agent-post-commit` - Call this when Git commit is done.

### TODO phase events

```
MUST be called when in TODO phase.
```

- `uv run doit agent-todo-start` - Continue working on TODOs (shows current TODO state)

### IMPL phase events

MUST be called when in IMPL phase.

- `uv run doit agent-coding-start` - Begin coding session, must be called before making any workspace changes (validates phase, git status, show TODO)
- `uv run doit agent-coding-checkpoint` - Quick validation during coding (format, syntax)

## DISCUSS Phase

```
- Discussion-only phase with no changes allowed.
- Agents must not modify any files or run commands that change the workspace.
- No commit, no commit checklist in this phase.
- Use for discussing ideas without implementation.
- No file modifications or system changes are permitted.
- This phase is for pure discussion and planning activities only.
- Agents should provide detailed explanations and reasoning in this phase.
```

## TODO Phase

```
- The todo file is _TODO-AGENT.md. We make structural changes to it only in TODO phase. It has two main parts:
- First section: ## Description : scope, motivation, research, related work. No checkboxes in this section! Just text and plain lists.
- Second section: ## Tasks : consists of one or more top-level tasks (checkboxes, numbered) with multiple sub-tasks (checkboxes, no numbers).
- See TEMPLATE_TODO-AGENT.md 
- Do research, write down findings, record possibly checked/affected code files.
- Make sure numbers make sense when re-ordering tasks.
```

## 📋 Standard User Commands (German Prompts)

These are user prompts in German - agent also responds in German.

- **"neue todo:"** → create new \_TODO-AGENT.md from template (must be in TODO phase) do research and add content as requested by user
- **"todo:"** → Add something to existing \_TODO-AGENT.md (must be in TODO phase)
- **"was ist noch offen?"** → Check \_TODO-AGENT.md, report remaining tasks briefly
- **"weiter gehts"** → Continue implementing current \_TODO-agent.md
- **"implementier"** → start implementing \_TODO-AGENT.md (TODO must not have checked checkboxes, yet)
- **"mach"** → Choose first available option and do it now
- **"frage:"** → Switch to DISCUSS phase for discussion without changes

## 📝 Pre-commit checklist (MANDATORY)

End your turn with filling out the following checklist. No need to show it to the user, just put it in the commit message when you changed something in the repository.

Rules:

- Mark all completed checkbox items `[x]` and write down why you have marked it (evidence? stats?).
- Replace ALL placeholders [...] with meaningful information, can be just an empty string for YES:choices
- don't show placeholders in your output
- Mark content in the template that is clearly not applicable and state the reason, 
- [evidence?] placeholder means: how did you check that your answer is correct?
- [YES: text] | NO:

In you final message to the user, include The commit ID at the Very end, clearly visible.

**TODO Mode Checklist:**

```
- [ ] We are in TODO phase [evidence?]
    - [ ] Only _TODO-AGENT.md has changes, nothing else ([evidence?])
    - [ ] Progress tracked in _TODO-AGENT.md: [X completed items] / [Y total items]
    - [ ] All tasks done: [yes/no]
    - [ ] Can I continue right away? [YES: what's the next TODO task? | NO: what do you want to ask the user]
    - [ ] I understand that I MUST commit immediately after filling this checklist - NO DELAY! [YES: I will run 'git add _TODO-AGENT.md && git commit' right now | NO: I need help]

- [ ] All mandatory workflow events for [PHASE] called? [N events called] ([evidence?])
- [ ] Everything ready for commit? Will I show the resulting commit ID to the user? [YES: short commit ID plus headline here | NO: reason for not making a commit?]
```

**IMPL Mode Checklist:**

```
- [ ] I know that we are in IMPL phase (evidence?)
    - [ ] I have written tests for new functionality (YES: [N new tests] | NO: [TODO phase/other reason])
    - [ ] I can confirm that tests are green (YES: Number of tests ran: [N tests ran] | NO: Test failures: [N test failures])
    - [ ] I have tracked progress in _TODO-AGENT.md? ([X completed] / [Y total] items | Finished: [yes/no])  
    - [ ] Can I continue right away? (YES: [what's the next TODO task?] | NO: ask user for direction!)
    - [ ] I understand that I MUST commit immediately after filling this checklist - NO DELAY! (YES: I will run 'git add <files> && git commit' right now | NO: I need help)

- [ ] I called all relevant workflow events for phase [PHASE] ([N events called] evidence?)
- [ ] Everything ready for commit? Will I show the resulting commit ID to the user? (YES: [commit details] | NO: [reason])
```

## 🔗 Reference to Development Conventions

Agents must follow all project-wide development conventions as defined in CONVENTIONS.md.\
This includes (but is not limited to):

- **Git**: All commits must follow Conventional Commits (see CONVENTIONS.md → Git).
- **Logging**: Structured logging format must follow CONVENTIONS.md → Logging.
- **Testing**: All tests must follow pytest conventions and aim for ≥80% coverage (see CONVENTIONS.md → Testing).
- **Dependencies**: Use uv for all dependency management (see CONVENTIONS.md → Dependencies).
- **CLI Design**: Generated CLI code must follow CONVENTIONS.md → CLI Design.

In case of conflict between AGENTS.md and CONVENTIONS.md, AGENTS.md takes precedence (agent guardrails).

Last updated: 2025-09-01 by human dev
