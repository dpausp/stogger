# workspace-split

## Context

nicestlog is a single-package structured logging library (24 .py files, ~13k lines in `src/`) with a monolithic `__init__.py` exporting 36 public symbols. The package mixes core logging, CLI tooling, web dashboards, and system integrations in one namespace. The brand "nicestlog" is being retired. The restructuring splits the monolith into a uv workspace with 5 focused packages under `packages/`, each with its own dependencies and public API.

## Decisions

### workspace-structure

- Context: Single `pyproject.toml` at repo root currently defines the `nicestlog` package, all optional deps, dev tools, and build config. The workspace root must not conflict with member packages.
- Decision: Root `pyproject.toml` has NO `[project]` section. It declares `[tool.uv.workspace]` with `members = ["packages/*"]`. All dev dependency groups (lint, test, docs, dev) and tool configs (ruff, pytest, tox, coverage, vulture, ty, radon) remain at root level.
- Consequences: `uv sync` resolves the entire workspace. Member packages define their own `[project]` sections with independent versioning. Root-level tool configs apply to all workspace members.

### package-stogger

- Context: Core logging functionality is the foundation all other packages depend on. Files `_regexes.py`, `config.py`, `core.py`, `factory.py`, `pii_scrubber.py`, `gitignore_utils.py`, `i18n.py`, `i18n_check.py` form the core. The only required external dependency is `structlog`.
- Decision: Package `stogger` at `packages/stogger/` with `src/` layout. External deps: `structlog>=25.4.0`. No optional deps. Starting version: `1.0.0`. No entry point (library only).
- Consequences: All other packages depend on `stogger`. It is the single source of truth for logging configuration, factories, PII scrubbing, and i18n.

### package-stogger-systemd

- Context: `systemd_integration.py` and `journal_viewer.py` provide systemd journal integration. Both duplicate color constants currently defined inline in `core.py` and locally in each file.
- Decision: Package `stogger-systemd` at `packages/stogger-systemd/` with `src/` layout. External deps: `structlog>=25.4.0` (systemd bindings are optional via try/except). Internal dep: `stogger`. Starting version: `1.0.0`.
- Consequences: Color duplication eliminated by importing from `stogger._colors` (see `color-constants-extraction`). The systemd C extension is imported with try/except so the package works without `python-systemd` installed.

### package-stogger-eliot

- Context: `eliot_integration.py` integrates Eliot logging. It duplicates the same color constants as the systemd package.
- Decision: Package `stogger-eliot` at `packages/stogger-eliot/` with `src/` layout. External deps: `structlog>=25.4.0`, `eliot>=1.17.5`. Internal dep: `stogger`. Starting version: `1.0.0`.
- Consequences: Color duplication eliminated by importing from `stogger._colors`. Eliot is a declared dependency. Try/except import guard provides graceful degradation at runtime.

### package-stogger-web

- Context: `web_dashboard.py` provides a Flask-based log viewing dashboard. No dependency on other nicestlog submodules beyond structlog.
- Decision: Package `stogger-web` at `packages/stogger-web/` with `src/` layout. External deps: `structlog>=25.4.0`, `flask>=3.1.3`. No internal deps on other workspace packages. Starting version: `1.0.0`.
- Consequences: Self-contained web package. Flask is a declared dependency. Try/except import guard provides graceful degradation at runtime if Flask is somehow missing.

### package-stoggertools

- Context: CLI tooling (`cli.py`, `assistant.py`, `advanced_assistant.py`, `interactive_transformer.py`, `live_editor.py`, `linter.py`, `log_statement_analyzer.py`, `log_reviewer.py`, `project_analyzer.py`, `cli_output_transformer.py`) plus `__init__.py` and `__main__.py` form the user-facing command-line tool. Users importing from the CLI package currently get the full convenience API.
- Decision: Package `stoggertools` at `packages/stoggertools/` with `src/` layout. External deps: `structlog>=25.4.0`, `typer>=0.16.1`, `rich>=14.3.3`, `toml>=0.10.2`. Internal dep: `stogger`. Entry point: `stoggertools = "stoggertools:main"`. Starting version: `1.0.0`.
- Consequences: Re-exports stogger's core API from `stoggertools.__init__` for convenience. Users who `import stoggertools` get access to `init_logging`, `NicestLogConfig`, `t`, etc. The removed deps `click` and `colorama` are no longer required (typer bundles click; colorama is handled via rich).

### color-constants-extraction

- Context: `core.py` defines color constants (`RESET_ALL`, `BRIGHT`, `DIM`, `RED`, `BACKRED`, `BLUE`, `CYAN`, `MAGENTA`, `YELLOW`, `GREEN`) using colorama when available, falling back to empty strings. `journal_viewer.py` and `eliot_integration.py` duplicate these constants with identical try/except patterns. After the split, these files live in separate packages that cannot import from `core.py` directly.
- Decision: Extract color constants into `stogger._colors` module. The module defines all constants with the same colorama-with-fallback pattern. `core.py`, `journal_viewer.py` (now in stogger-systemd), and `eliot_integration.py` (now in stogger-eliot) import from `stogger._colors`.
- Consequences: Single source of truth for terminal colors. The `_colors` module is private (underscore prefix) but intentionally importable by workspace sibling packages. Eliminates triple duplication.

### re-export-pattern

- Context: Current `nicestlog.__init__` re-exports 36 symbols from all submodules, providing a flat convenience API. Users do `from nicestlog import init_logging`. After the split, core API lives in `stogger` while CLI tooling lives in `stoggertools`.
- Decision: `stoggertools.__init__` re-exports stogger's core public symbols (`init_logging`, `init_early_logging`, `init_command_logging`, `drop_cmd_output_logfile`, `logging_initialized`, `JournalLogger`, `JournalLoggerFactory`, `MultiOptimisticLogger`, `MultiOptimisticLoggerFactory`, `SystemdJournalRenderer`, `NicestLogConfig`, `create_pii_processor`, `demo_pii_scrubbing`, `init_i18n`, `get_translator`, `t`, `arsch`, `leiwand`, `oida`). `stogger.__init__` only exports its own symbols.
- Consequences: `stoggertools` is the drop-in convenience entry point. `stogger` is the clean library without CLI baggage. Users who need only the library import from `stogger`; CLI users import from `stoggertools` and get everything.

### import-path-migration

- Context: All 24 .py files use `from nicestlog.X import Y` or relative imports internally. After splitting into 5 packages, every internal import must change.
- Decision: All imports are updated to new package names: `stogger.X`, `stogger-systemd.X` (as `stogger_systemd`), `stogger-eliot.X` (as `stogger_systemd`), `stogger-web.X` (as `stogger_web`), `stoggertools.X`. Cross-package references use the distribution name as import target (PEP 503 normalized: hyphens become underscores).
- Consequences: Every `.py` file that moves gets its imports rewritten. Tests in `/tests/` also update all `nicestlog` references to the appropriate new package name.

### test-organization

- Context: Tests currently live in `/tests/` at repo root and import from `nicestlog`.
- Decision: Tests remain at `/tests/`. All imports updated from `nicestlog` to the appropriate new package name (`stogger`, `stogger_systemd`, `stogger_eliot`, `stogger_web`, `stoggertools`). Coverage config in root `pyproject.toml` updated to cover all workspace packages.
- Consequences: No test directory restructuring. Single pytest invocation from root covers all packages. Coverage reports aggregate across workspace.

### optional-deps-pattern

- Context: `systemd_integration.py`, `eliot_integration.py`, and `web_dashboard.py` use try/except around optional imports (`systemd`, `eliot`, `flask`) to allow installation without heavy dependencies.
- Decision: `eliot` and `flask` are declared as package dependencies in `stogger-eliot` and `stogger-web` respectively. `python-systemd` is NOT declared (stdlib-adjacent, platform-specific). All three retain try/except import guards for graceful runtime degradation if a dep is somehow missing.
- Consequences: `pip install stogger-eliot` pulls eliot. `pip install stogger-web` pulls flask. `pip install stogger-systemd` does NOT pull python-systemd (must be installed separately). Try/except guards provide defense-in-depth.

### versioning-break

- Context: nicestlog is at version `0.3.5`. The workspace split is a complete restructuring with new package names, new import paths, and removed backward compatibility.
- Decision: All 5 packages start at version `1.0.0`. This is a breaking change by design. No compatibility shims, no migration aliases.
- Consequences: Clear signal that this is not a drop-in upgrade. Users must change their imports and dependency declarations.

### old-package-removal

- Context: The `src/nicestlog/` directory contains the old monolith. After migration it must not coexist with the new workspace packages.
- Decision: The entire `src/nicestlog/` directory and the `src/` parent directory are deleted after all files are distributed to their new package locations. The `[tool.hatch.build.targets.wheel]` config referencing `src/nicestlog` is removed from root `pyproject.toml`.
- Consequences: No stale code. No import confusion. Clean workspace with only `packages/` and `tests/`.

## Requirements

### File Distribution

| Source file (in `src/nicestlog/`) | Target package | Target path |
|---|---|---|
| `_regexes.py` | stogger | `packages/stogger/src/stogger/` |
| `config.py` | stogger | `packages/stogger/src/stogger/` |
| `core.py` | stogger | `packages/stogger/src/stogger/` |
| `factory.py` | stogger | `packages/stogger/src/stogger/` |
| `pii_scrubber.py` | stogger | `packages/stogger/src/stogger/` |
| `gitignore_utils.py` | stogger | `packages/stogger/src/stogger/` |
| `i18n.py` | stogger | `packages/stogger/src/stogger/` |
| `i18n_check.py` | stogger | `packages/stogger/src/stogger/` |
| `_colors.py` (new) | stogger | `packages/stogger/src/stogger/` |
| `systemd_integration.py` | stogger-systemd | `packages/stogger-systemd/src/stogger_systemd/` |
| `journal_viewer.py` | stogger-systemd | `packages/stogger-systemd/src/stogger_systemd/` |
| `eliot_integration.py` | stogger-eliot | `packages/stogger-eliot/src/stogger_eliot/` |
| `web_dashboard.py` | stogger-web | `packages/stogger-web/src/stogger_web/` |
| `__init__.py` | stoggertools | `packages/stoggertools/src/stoggertools/` (rewritten) |
| `__main__.py` | stoggertools | `packages/stoggertools/src/stoggertools/` |
| `cli.py` | stoggertools | `packages/stoggertools/src/stoggertools/` |
| `assistant.py` | stoggertools | `packages/stoggertools/src/stoggertools/` |
| `advanced_assistant.py` | stoggertools | `packages/stoggertools/src/stoggertools/` |
| `interactive_transformer.py` | stoggertools | `packages/stoggertools/src/stoggertools/` |
| `live_editor.py` | stoggertools | `packages/stoggertools/src/stoggertools/` |
| `linter.py` | stoggertools | `packages/stoggertools/src/stoggertools/` |
| `log_statement_analyzer.py` | stoggertools | `packages/stoggertools/src/stoggertools/` |
| `log_reviewer.py` | stoggertools | `packages/stoggertools/src/stoggertools/` |
| `project_analyzer.py` | stoggertools | `packages/stoggertools/src/stoggertools/` |
| `cli_output_transformer.py` | stoggertools | `packages/stoggertools/src/stoggertools/` |

### Public API per Package

**stogger**: `init_logging`, `init_early_logging`, `init_command_logging`, `drop_cmd_output_logfile`, `logging_initialized`, `JournalLogger`, `JournalLoggerFactory`, `MultiOptimisticLogger`, `MultiOptimisticLoggerFactory`, `SystemdJournalRenderer`, `NicestLogConfig`, `create_pii_processor`, `demo_pii_scrubbing`, `init_i18n`, `get_translator`, `t`, `arsch`, `leiwand`, `oida`

**stogger-systemd**: `setup_systemd_logging`, `create_systemd_service_file`, `demo_systemd_integration`

**stogger-eliot**: `setup_eliot_logging`

**stogger-web**: `setup_web_logging`, `run_dashboard`, `get_log_stats`

**stoggertools**: All stogger public API (re-exported) plus `main`, `migrate_directory`, `analyze_python_file`, `create_advanced_assistant`, `transform_python_file`, `create_interactive_transformer`, `transform_directory_interactive`, `transform_file_interactive`, `create_live_editor`, `edit_code_live`

### Package pyproject.toml Skeletons

**Root** (no `[project]`):
```toml
[tool.uv.workspace]
members = ["packages/*"]
```

**stogger**:
```toml
[project]
name = "stogger"
version = "1.0.0"
requires-python = ">=3.13"
dependencies = ["structlog>=25.4.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/stogger"]
```

**stogger-systemd**:
```toml
[project]
name = "stogger-systemd"
version = "1.0.0"
requires-python = ">=3.13"
dependencies = ["structlog>=25.4.0", "stogger"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/stogger_systemd"]
```

**stogger-eliot**:
```toml
[project]
name = "stogger-eliot"
version = "1.0.0"
requires-python = ">=3.13"
dependencies = ["structlog>=25.4.0", "stogger", "eliot>=1.17.5"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/stogger_eliot"]
```

**stogger-web**:
```toml
[project]
name = "stogger-web"
version = "1.0.0"
requires-python = ">=3.13"
dependencies = ["structlog>=25.4.0", "flask>=3.1.3"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/stogger_web"]
```

**stoggertools**:
```toml
[project]
name = "stoggertools"
version = "1.0.0"
requires-python = ">=3.13"
dependencies = ["structlog>=25.4.0", "typer>=0.16.1", "rich>=14.3.3", "toml>=0.10.2", "stogger"]

[project.scripts]
stoggertools = "stoggertools:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/stoggertools"]
```

### Import Name Mapping

Distribution package names contain hyphens (PEP 503), but Python import names use underscores:

| Distribution name | Import name |
|---|---|
| `stogger` | `stogger` |
| `stogger-systemd` | `stogger_systemd` |
| `stogger-eliot` | `stogger_eliot` |
| `stogger-web` | `stogger_web` |
| `stoggertools` | `stoggertools` |

### New Module: stogger._colors

Extracted from `core.py` lines 38-50. Defines: `RESET_ALL`, `BRIGHT`, `DIM`, `RED`, `BACKRED`, `BLUE`, `CYAN`, `MAGENTA`, `YELLOW`, `GREEN`. Uses `colorama` when available, falls back to empty strings.

### Deletions After Migration

- `src/nicestlog/` (entire directory)
- `src/` (parent directory, now empty)
- Entire `[project]` section from root `pyproject.toml` (name, version, description, readme, requires-python, dependencies)
- `[project.optional-dependencies]` from root `pyproject.toml` (cli, web, http, eliot groups)
- `[project.scripts]` from root `pyproject.toml` (`nicestlog = "nicestlog:main"`)
- `[build-system]` from root `pyproject.toml` (hatchling config)
- `[tool.uv.sources.nicestlog]` from root `pyproject.toml`
- `[tool.nicestlog]` section from root `pyproject.toml`
- `[tool.hatch.build.targets.wheel]` and `[tool.hatch.build.targets.wheel.force-include]` from root `pyproject.toml`
- `[tool.hatch.build.targets.sdist]` from root `pyproject.toml`
- `nicestlog` reference in `[dependency-groups] dev` (`"nicestlog[cli]"`)

## References

- [uv workspaces](https://docs.astral.sh/uv/concepts/workspaces/)
- [PEP 503 package normalization](https://peps.python.org/pep-0503/#normalized-names)
