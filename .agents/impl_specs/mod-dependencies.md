# mod-dependencies

## Context

Patch-level dependency updates across all dependency groups. No security vulnerabilities found (uv audit clean). All updates are minor/patch with no known breaking changes.

## Decisions

### patch-updates

#### Context

Four packages are behind their latest versions. All are patch-level updates with no API changes.

#### Decision

Update all four packages to latest patch versions in one batch:

| Package | Current | Target | Group |
|---|---|---|---|
| ty | 0.0.39 | 0.0.42 | lint |
| pytest-stogger | 2026.5.21 | 2026.6.2 | test |
| ruff | 0.15.14 | 0.15.15 | lint |
| typer | 0.26.1 | 0.26.6 | (transitive) |

Update strategy: `uv lock --upgrade-package <name>` for each, then `uv sync --all-groups --all-extras`.

#### Alternatives

a. `uv lock --upgrade` (all packages) — broader than needed, risks pulling unrelated changes
b. Manual version pins in pyproject.toml — unnecessary for patch updates, version ranges already allow these

#### Consequences

Minimal risk. Patch updates are backward-compatible by definition. Tests must pass unchanged.

## Constraints

- Run `CI=1 uv run tox -p` after updates to verify all quality gates pass
- Do NOT modify pyproject.toml version ranges — they already allow these versions
- Do NOT modify any test files
- If any test fails after update, STOP and report
