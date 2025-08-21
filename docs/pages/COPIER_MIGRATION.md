# Copier Migration Plan

Goal: Make `python-mydevtools-template` (Copier) the single source of truth for all project scaffolding and get rid of `src/mydevtools/configs` (and dependent logic).

## Current Status (duplication and usage)

There are three sources of truth right now:

1) Project root (this repo) – working copies used by CI and development
2) `src/mydevtools/configs/` – package-embedded configs copied by CLI (`mydevtools setup`)
3) `python-mydevtools-template/template/` – Copier template

Active usages of `configs` (package-embedded files):
- CLI (`src/mydevtools/cli.py`):
  - `setup` calls `configs.copy_configs(target_path)` and dry-run reads `configs.get_config_dir()`
- Integration (`src/mydevtools/integration.py`):
  - imports `get_pyproject_config()` from `mydevtools.configs` to build a merge plan
- Tests:
  - `tests/test_configs.py` covers `copy_configs` and `get_config_dir`
  - `tests/test_cli.py` mocks `mydevtools.configs.copy_configs`

Conclusion: `configs` is still used and cannot be removed without code and test changes.

## Decision

Adopt Copier as the single source of truth for file scaffolding and updates. The package-embedded `configs` directory will be deprecated and removed in a major version.

## Step-by-step Migration

1. Ensure template completeness
   - [x] `.pre-commit-config*.yaml.jinja` – already present and updated
   - [x] `dodo.py.jinja` – added (aligned with modern tasks and LOC)
   - [x] `AI-CODING-RULES.md.jinja`, `CONVENTIONS.md.jinja`, `README.md.jinja`, `PRECOMMIT_MIGRATION.md.jinja` – present
   - [ ] Add any missing files that are still only under `src/mydevtools/configs/` (e.g., `.agent.md` if needed by projects)

2. Introduce Copier path in CLI
   - Change `mydevtools setup` to default to Copier-based generation:
     - Detect and load sensible defaults from `pyproject.toml` (e.g., project name, package name)
     - Run Copier non-interactively with those defaults or interactively when requested
     - Fallback: if Copier is not available, print helpful instructions
   - Provide options:
     - `--copier` / `--no-copier`
     - `--interactive` to run Copier prompts
   - Keep legacy `configs.copy_configs` behind a deprecation flag for one minor version

3. Update analyze/integration flow
   - Replace reliance on `get_pyproject_config()` with one of:
     - (Preferred) Recommend running Copier to rewrite files and pyproject tool sections, or
     - Parse `template/pyproject.toml.jinja` and compute suggested tool diffs
   - Adjust messages to point towards Copier-based migration

4. Deprecate `mydevtools.configs`
   - Mark module as deprecated in docstring and log a warning on import
   - Keep thin shims for `copy_configs` and `get_config_dir` for one minor version
   - Remove the module in the next major release

5. Update tests
   - Remove `tests/test_configs.py`
   - Update `tests/test_cli.py` to mock Copier invocation (via subprocess or Python API)
   - Add unit tests for context discovery (project/package names) and flags

6. Remove package-embedded configs
   - Delete `src/mydevtools/configs/`
   - Bump major version

7. Documentation
   - Add a migration guide for users of older versions (how to use Copier to update)
   - README: emphasize Copier-first workflow (init/update)

## Implementation Sketch

- CLI changes (`src/mydevtools/cli.py`):
  - New helper: `run_copier(target_path: Path, *, interactive: bool, context: dict | None) -> int`
    - Implementation via `subprocess.run(["copier", "copy", template_path, str(target_path), ...])`
    - Use `uv run` in docs/CI; library API is optional but subprocess keeps deps minimal
  - Setup flow:
    1. Optionally clean deps
    2. Prefer Copier (unless `--no-copier`)
    3. If Copier missing or fails and legacy not disabled, offer legacy `configs.copy_configs`
  - Analyze flow: remove direct dependency on `get_pyproject_config()`, guide to Copier update

- Dependencies: no hard runtime dependency on Copier; only invoked if available

## Rollout Plan

- vNext minor:
  - Implement Copier path in CLI
  - Deprecation warnings on `mydevtools.configs`
  - Update docs/tests
- Next major:
  - Remove `mydevtools.configs` and its tests
  - Remove legacy paths in CLI/integration

## Risks and Mitigations

- Risk: Users without Copier installed
  - Mitigation: clear guidance; keep legacy for one transition release
- Risk: Merge conflicts in existing repos
  - Mitigation: use `copier update` and provide migration guide
- Risk: Lost project-specific tweaks in configs
  - Mitigation: Copier prompts/answers file; document overrides

## Tasks Checklist

- [x] CLI: add Copier execution path and flags
- [x] Integration: stop using `get_pyproject_config()`
- [x] Deprecate `mydevtools.configs` (warn)
- [x] Tests refactor (remove configs tests, add copier tests)
- [x] Make Copier default in CLI (--copier enabled by default)
- [x] Delete `src/mydevtools/configs/` (major bump)
- [x] Docs: migration guide + README + INTEGRATION.md updates

## Current Status (Updated)

✅ **Completed:**
- Copier-based setup is now the default (`--copier` enabled by default)
- Legacy `configs.py` is deprecated with warnings
- Integration module no longer uses `get_pyproject_config()`
- Migration suggestions recommend Copier-based workflow
- Tests updated to reflect Copier-first approach
- Fallback to legacy configs still available with `--no-copier`

✅ **MIGRATION COMPLETED:**
- All legacy configs removed in v1.0.0
- Copier template contains all functionality
- Breaking change: legacy functions now raise RuntimeError
- Users must use 'mydevtools setup' (Copier-based)