# Embedded Documentation for Agent Discovery

## Context

LLM Agents in external projects that depend on `stogger` have no way to discover how to use it correctly. They see a package name in `pyproject.toml`, get told "write stogger log messages", and produce wrong output — missing `_replace_msg`, using f-strings, wrong log levels.

There was an attempt to solve this in `3eb52e5` (Apr 14, 2026): Sphinx build output (`_sources/`, `llms.txt`, `llms-full.txt`) was copied into the installed package via `scripts/build_docs_for_package.py`. An agent could then discover docs via `importlib.resources.files('stogger')`.

This was reverted in `6b2b0f0` (Apr 16, 2026) — the embedded docs were gitignored as "build artefacts". Combined with the "big cleanup" in `ff06aab` (Apr 25, 2026) that removed most packages and docs, the agent discovery path is completely broken. No `llms.txt`, no `_sources/`, nothing discoverable from an installed package.

Today, Sphinx + `sphinx-llms-txt` still generate `llms.txt` (33 lines, table of contents) and `_sources/` (27 files, ~3.5K lines total) in `docs/_build/html/`. These never reach the package.

## Decision

Embed Sphinx-generated documentation in the installed stogger package so LLM agents can discover stogger's conventions without repo access or internet.

### packaging

#### Decision

Copy `_sources/` and `llms.txt` from `docs/_build/html/` into `src/stogger/_docs/` during the build process. The `_docs/` directory is included in the wheel via hatch's `include_package_data`.

#### Alternatives

a. Copy directly into `src/stogger/_sources/` — risks name collision with Python modules, confusing import paths. Rejected.
b. Embed as a single `_docs.md` file — loses navigability. Rejected.
c. Publish `llms.txt` on a web endpoint — requires internet access, defeats the purpose. Rejected.

#### Consequences

The installed package grows by ~3.5K lines of documentation (negligible for a wheel). An agent reads `importlib.resources.files('stogger') / '_docs' / 'llms.txt'` and follows links to `_docs/_sources/user/cheatsheet.md.txt` etc.

### llms-full-txt

#### Decision

Disable `llms_txt_full_build` in `conf.py`. The full text dump (3.572 lines of all pages concatenated) is redundant when `_sources/` is available — the agent reads targeted files, not a wall of text.

#### Alternatives

a. Keep `llms-full.txt` — wastes space, Sphinx directives (`{toctree}`, `{image}`) make it less readable than individual files. Rejected.
b. Generate a custom `llms-full.txt` without Sphinx directives — extra tooling for no gain. Rejected.

#### Consequences

`llms.txt` (33 lines) is the entry point. Individual files in `_sources/` are the content. No concatenated dump.

### build-script

#### Decision

Create `scripts/build_docs_for_package.py` that runs after Sphinx. It copies `_sources/` and `llms.txt` from `docs/_build/html/` into `src/stogger/_docs/`, fixing paths in `llms.txt` (`/_sources/` → `_docs/_sources/`).

The tox `build` environment depends on `docs`, runs the script, then runs `uv build`.

#### Alternatives

a. Sphinx post-build hook in `conf.py` — couples Sphinx config to package layout. Rejected.
b. Hatch build hook — possible, but tox already orchestrates the build pipeline. Rejected.

#### Consequences

Build pipeline: `fix` → `docs` (Sphinx) → `build` (copy + wheel). The script is idempotent — it removes old `_docs/` before copying.

### agent-skill

#### Decision

Copy `.agents/skills/stogger-logging.md` into `_docs/agent_skill.md` during the build. This 437-line file is the most agent-relevant content — it contains the complete logging convention rules, patterns, heuristics, and common mistakes. Add it to `llms.txt` as the primary entry point for agents.

#### Alternatives

a. Don't embed the skill — agents only get Sphinx docs. Rejected: the skill is better written for agents than Sphinx docs.
b. Generate the skill from Sphinx — no, it's a separate artifact with its own structure. Rejected.

#### Consequences

`llms.txt` lists `_docs/agent_skill.md` first. An agent reads the skill, then follows links to `_sources/` for deeper context.

### autoapi

#### Decision

Keep autoapi. The 7 generated RST files (config, core, decorators, factory, processors, systemd, index) contain docstring-derived API documentation. They're useful for agents and the Sphinx build already handles them.

#### Alternatives

a. Remove autoapi — agents lose API reference. Rejected.
b. Keep autoapi but exclude from `_sources/` — possible, but API docs are part of the package's documentation surface. Rejected.

#### Consequences

Autoapi RST files are included in `_sources/api/`. Minor Sphinx warnings (indentation in config RST) don't affect functionality.

### discovery-test

#### Decision

Write a test that verifies doc discovery from an installed package: `importlib.resources.files('stogger') / '_docs' / 'llms.txt'` must exist and be readable. Parse `llms.txt` to verify links reference valid files in `_sources/`.

#### Alternatives

a. No test — docs could silently stop embedding. Rejected.
b. Integration test only — slower, harder to debug. Rejected.

#### Consequences

One unit test in `tests/` that runs against the editable install. Catches if the build pipeline breaks.

## Verified By
