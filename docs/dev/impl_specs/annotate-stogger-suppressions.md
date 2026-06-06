# Annotate Stogger Logging Suppressions

## Context

`STOGGER_TECH_DEBT.md` lists 29 suppressed logging violations across
the stogger codebase. After investigation, the majority of these are
**architecturally intentional** — they live in the logging pipeline itself
(structlog processors, formatters, dispatchers) where adding a log call
would cause recursion or corrupt the visible output.

The suppressions are correct. The problem is they are **silent**: every
`# stogger: ignore` in the code is undocumented, and the
`[tool.pytest-stogger.per-file-ignores]` entries in `pyproject.toml` carry
no rationale. This makes the tech-debt report noisy and obscures any
genuine future violations.

## Decision

**Do NOT add log calls to pipeline-internal code.** Instead, annotate
every suppression with a one-line rationale so the next reader (human or
agent) knows why the suppression exists. Tighten the per-file-ignores
config to be rule-specific rather than blanket where possible.

This is a documentation/justification pass, not a behavioral change.
`STOGGER_TECH_DEBT.md` should regenerate smaller (or empty) after the
annotations are in place.

## Files in Scope

- `src/stogger/core.py` — 22 inline ignores
- `src/stogger/decorators.py:31` — 1 inline ignore
- `src/stogger/__init__.py` — per-file-ignore
- `src/stogger/_colors.py` — per-file-ignore
- `src/stogger/systemd.py` — per-file-ignore
- `pyproject.toml` — per-file-ignores config
- `STOGGER_TECH_DEBT.md` — regenerate after changes

## Per-Suppression Policy

### Category A: Pipeline internals (keep, annotate)

Any function with one of these signatures or purposes MUST keep its
suppression. Annotation template:

```python
# stogger: ignore — <reason>
```

Valid reasons (pick the most specific):

- `structlog processor — logging here would recurse`
- `structlog formatter — output pipeline, must not log`
- `json fallback / serialization — output pipeline, must not log`
- `ANSI escape helper — output pipeline, must not log`
- `translation lookup — recurses through logger pipeline`

Applies to:

| File:Line | Function | Why |
|---|---|---|
| core.py:73 | `_TranslationProcessor.__call__` | processor |
| core.py:98 | `prefix()` | formatter helper |
| core.py:124 | `ConsoleRenderer.__init__` | renderer construction |
| core.py:172 | `_resolve_level_name` | processor helper |
| core.py:181 | `_should_drop_by_level` | processor helper |
| core.py:190 | `_strip_internal_fields` | processor helper |
| core.py:203 | `_format_timestamp` | formatter |
| core.py:214 | `_render_output_sections` | formatter |
| core.py:251 | `_format_replace_msg` | formatter |
| core.py:262 | `_create_write_helper` | renderer helper |
| core.py:285 | `_format_header` | formatter |
| core.py:301 | `_format_body` | formatter |
| core.py:314 | `ConsoleRenderer.__call__` | processor |
| core.py:343 | `ConsoleRenderer.__call__` (overload) | processor |
| core.py:371 | `_inject_exc_info_for_exception` | processor helper |
| core.py:392 | `process_exc_info` | formatter |
| core.py:405 | `format_exc_info` | formatter |
| core.py:448 | `EtherRenderer.__call__` | processor |
| core.py:827 | `MultiRenderer.__call__` | processor |
| core.py:868 | `handle_json_fallback` | json fallback |
| core.py:877 | `dump_for_journal` | json fallback |
| core.py:898 | `EtherJSONRenderer.__call__` | processor |
| core.py:918 | `_DropEventProcessor.__call__` | processor |

### Category B: External boundary (keep, annotate)

| File:Line | Function | Why |
|---|---|---|
| decorators.py:31 | (function at line 31) | decorator construction — runs at import time, no logger available |

(Developer: read `decorators.py:31` and choose the most accurate reason
from: "decorator — runs at import time", "decorator — passthrough
wrapper", or similar. If the function actually COULD log safely, then
fix it instead of suppressing.)

### Category C: Per-file ignores in pyproject.toml

These are file-level suppressions. Add an inline comment above each
entry in `pyproject.toml`:

```toml
[tool.pytest-stogger.per-file-ignores]
# Low-level ANSI helpers — logging would corrupt colorized output.
"_colors.py" = ["except-must-log", "complexity-needs-log"]
# Package init — runs before logger is configured.
"__init__.py" = ["except-must-log"]
# systemd journal bridge — uses journald native logging, not stogger.
"systemd.py" = ["except-must-log", "complexity-needs-log"]
```

(Developer: verify the systemd.py rationale by reading the file — if
it's genuinely a journald bridge, the comment is correct; if not,
adjust to match reality.)

## What NOT to Do

- Do **not** add `log.exception()` or `log.info()` calls to any function
  listed in Category A. The recursion / output-corruption risk is real.
- Do **not** remove any suppression. The goal is annotation, not
  removal.
- Do **not** change the behavior of any function.
- Do **not** refactor unrelated code.
- Do **not** change the `[tool.pytest-stogger]` config structure
  (rule list, source path, etc.).

## Acceptance Criteria

1. Every `# stogger: ignore` comment in `src/stogger/*.py` has a
   rationale suffix (e.g. `# stogger: ignore — processor`) OR has a
   preceding comment line explaining why.
2. Every entry in `[tool.pytest-stogger.per-file-ignores]` has an
   explanatory comment line above it.
3. `CI=1 uv run tox -p` is green (all envs: fix, cov, docs, build, 3.13,
   integrations).
4. `STOGGER_TECH_DEBT.md` is regenerated by the next test run. It should
   ideally be empty (all 29 suppressions now annotated). If
   pytest-stogger still flags annotated suppressions, that's a
   pytest-stogger feature gap — note it and proceed.
5. Single commit, message:

   ```
   Annotate stogger logging suppressions with rationale

   All 29 suppressions listed in STOGGER_TECH_DEBT.md were architectural
   (structlog pipeline, formatter helpers, ANSI utilities, systemd
   bridge) — keeping them was correct, but they were silent. Each
   `# stogger: ignore` now carries a one-line reason; each per-file-
   ignores entry in pyproject.toml has an explanatory comment.

   No behavioral change.
   ```

## Verification

- `cd /stogger && CI=1 uv run tox -p` — must exit 0
- `grep -n "stogger: ignore$" src/stogger/*.py` — must be empty (every
  ignore has a rationale suffix now)
- After tox run, check `STOGGER_TECH_DEBT.md` state
