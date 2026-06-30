# legacy-elimination

## Context

Stogger's codebase carries 30+ legacy artifacts from its evolution: dead code from absorbed packages, backwards-compatibility keys from fc-agent inheritance, defensive exception handling that violates fail-loudly principles, stale documentation referencing non-existent modules, and spec test lifecycle debt. CODEX Article 4 mandates: BREAK EVERYTHING NOW — no migration paths, no deprecation periods, no fallbacks.

## Decisions

### dead-code-removal

#### Context

Dead code from absorbed packages and abandoned features litters the codebase. `JournalLoggerFactory` stub in core.py was superseded when stogger-systemd was absorbed as `src/stogger/systemd.py`. `_regexes.py` has no production consumer — only tests verify its existence. Dead fields `show_logger_brackets` and `show_pid` in `ConsoleFileRenderer` were explicitly documented as dead by ADR `format-config-extension`. A bare `sys.stdout.isatty()` call in `ConsoleFileRenderer.__init__` discards its result.

#### Decision

Remove all dead code:
- Delete `_regexes.py` module entirely
- Delete `JournalLoggerFactory` stub class from core.py
- Delete `show_logger_brackets` and `show_pid` dead fields from `ConsoleFileRenderer.__init__`
- Delete bare `sys.stdout.isatty()` call from `ConsoleFileRenderer.__init__`
- Remove `JournalLoggerFactory` export from `__init__.py`
- Update any tests that verify dead code existence

#### Alternatives

a. Keep dead code "just in case" — violates Article 4, accumulates maintenance burden
b. Move to archive branch — code archeology is git's job, not the codebase's

#### Consequences

~120 lines removed from production code. Any external consumer of `JournalLoggerFactory` (unlikely — it returns None) gets an ImportError, which is correct behavior.

### broad-exception-cleanup

#### Context

Five catch-all `except Exception` blocks silently suppress failures. `init_early_logging` swallows all startup errors as debug messages. `MultiRenderer.__call__` and `MultiOptimisticLogger.msg` catch all renderer failures silently. `_load_pyproject_config` has a redundant `(tomllib.TOMLDecodeError, Exception)` tuple. `_check_test_dependencies` defers warnings to process exit via `atexit`.

#### Decision

Replace broad exception handling with let-it-crash or targeted catches:
- `init_early_logging`: remove the try/except entirely — let startup failures propagate
- `MultiRenderer.__call__`: keep try/except but re-raise as `RuntimeError` with context — renderer failures must be visible
- `MultiOptimisticLogger.msg`: same as MultiRenderer — re-raise with context
- `_load_pyproject_config`: catch only `FileNotFoundError` and `tomllib.TOMLDecodeError` — remove bare `Exception`
- `_check_test_dependencies` / `_PENDING_WARNINGS` / `atexit`: remove deferred warning system entirely — emit warnings immediately or remove the feature

#### Alternatives

a. Keep silent catches for "logging must not crash the app" — violates Article 5, hides real bugs
b. Log at error level instead of debug — better but still hides the failure from the caller

#### Consequences

Failures surface immediately at the call site. Any code depending on silent error suppression will break, which is the intended outcome. Renderer errors become visible in CI and production logs.

### backwards-compat-purge

#### Context

The bare `"output"` key in `KEYS_TO_SKIP_IN_JOURNAL_MESSAGE` is documented as retained "for backward compatibility" — it's a bug from "original fc-agent code" with the actual key being `"_output"`. The `log_to_stdlib` processor exists solely for "Legacy code that reads from stdlib logging handlers." Two version management systems coexist in pyproject.toml: `hatch-vcs` (active) and `bumpversion` (redundant). `scripts/release.py` references `stogger-systemd` (absorbed into main package) and `pytest-stogger` (not in workspace).

#### Decision

Remove all backwards-compatibility artifacts:
- Remove bare `"output"` from `KEYS_TO_SKIP_IN_JOURNAL_MESSAGE`
- Remove `log_to_stdlib` processor function entirely
- Remove `[tool.bumpversion]` section and `[[tool.bumpversion.files]]` from pyproject.toml
- Remove `stogger-systemd` and `pytest-stogger` from `scripts/release.py` PROJECTS dict
- Remove `scripts/release.py` docstring references to these projects

#### Alternatives

a. Keep `"output"` key "just in case" — perpetuates a known bug
b. Keep `log_to_stdlib` for gradual migration — violates Article 4
c. Keep bumpversion alongside hatch-vcs — redundant configuration is confusing

#### Consequences

Breaking changes for any consumer using bare `"output"` key or `log_to_stdlib` processor. Both are documented as legacy/deprecated already. Version management consolidated to hatch-vcs only. Release script only references workspace members.

### vulture-whitelist-cleanup

#### Context

`.vulture_whitelist.py` has 168 lines, ~140 of which reference code that no longer exists: eliot integration, CLI commands (`tools_generate_service`, `tools_review`, etc.), i18n functions, interactive transformer, web dashboard, 18 PyDoit task functions, ~30 Sphinx config variables. The file header lists categories that are stale.

#### Decision

Remove all whitelist entries for non-existent code. Keep only entries that reference actual symbols in the current codebase. Rewrite the module docstring to reflect current categories. If no legitimate entries remain, delete the file entirely and remove the vulture config from pyproject.toml.

#### Alternatives

a. Keep stale entries as "documentation" — vulture whitelists are not documentation
b. Partial cleanup — leaves misleading entries that suggest features exist

#### Consequences

Clean whitelist that accurately reflects the codebase. Vulture continues to catch dead code without false positives from ghost entries.

### stale-documentation-fix

#### Context

`CONVENTIONS.md` references mypy (project uses ty), and lists non-existent components (`stoggertools.cli`, `stogger.advanced_assistant`, `stogger.i18n`). `docs/dev/type_checking_guide.md` shows wrong import path (`stogger_systemd` instead of `stogger.systemd`). All 4 ADRs have a placeholder HTML comment about pending tests in `## Verified By`. pyproject.toml has a commented-out `infrastructure_files` line that should have been deleted per ADR `stogger-self-logging`.

#### Decision

Fix all stale documentation:
- `CONVENTIONS.md`: replace mypy reference with ty, remove references to non-existent components
- `docs/dev/type_checking_guide.md`: fix import path from `stogger_systemd` to `stogger.systemd`
- All ADRs: remove the pending-tests placeholder comments from `## Verified By` sections
- `pyproject.toml`: remove commented-out `infrastructure_files` line

#### Alternatives

a. Leave documentation stale — misleading for contributors and users
b. Only fix ADRs — leaves CONVENTIONS.md and type_checking_guide wrong

#### Consequences

Documentation matches reality. ADR `Verified By` sections are empty (honest) instead of containing placeholder promises.

### spec-test-lifecycle-cleanup

#### Context

Three impl_spec test files totaling 843 lines should have been garbage-collected after passing. `tests/impl_spec/test_logging_decorators_docs.py` (143 lines) — impl spec `logging-decorators-docs` is fully verified. `tests/impl_spec/test_format_config_extension.py` (373 lines) — ADR `format-config-extension` is implemented. `tests/impl_spec/test_postgres_target.py` (327 lines) — ADR `postgres-target` is implemented. These tests pass without xfail markers but remain in the tree.

#### Decision

Delete all three impl_spec test files. Their purpose (spec validation before implementation) is complete. Permanent tests in `tests/test_core.py`, `tests/test_config.py`, and `tests/test_decorators.py` cover the functionality.

#### Alternatives

a. Keep as "extra coverage" — redundant, confuses test purpose, 843 lines of maintenance burden
b. Move to permanent test files — tests already exist in natural locations

#### Consequences

843 lines of temporary test code removed. Test tree clean — only permanent tests remain.

### colorama-availability-check

#### Context

`_colors.py` has a runtime check for colorama availability (`if sys.stdout.isatty() and colorama`), falling back to empty strings when colorama is missing. But colorama is a hard dependency in pyproject.toml (`colorama>=0.4.6`). The fallback branch is unreachable in a properly installed environment.

#### Decision

Remove the colorama availability check. Import colorama directly without fallback. The empty-string fallback is dead code.

#### Alternatives

a. Keep the check for "flexibility" — colorama is a hard dependency, flexibility is misleading
b. Make colorama optional — contradicts project's design decision

#### Consequences

Simpler code. If colorama is somehow missing, the ImportError is immediate and clear rather than silently producing colorless output.

### optional-import-simplification

#### Context

The systemd dynamic import in `core.py` catches ImportError for `stogger.systemd`, but `stogger.systemd` is now a built-in module (not an external package). The ImportError path cannot fire in the current codebase. The postgres dynamic import catches ImportError legitimately (optional dependency) but uses `import_error=True` which is a misleading key-value.

#### Decision

- Systemd import: replace dynamic import with direct `from stogger.systemd import get_journal_logger_factory` — remove the try/except ImportError entirely
- Postgres import: keep the try/except (legitimate optional dependency) but fix `import_error=True` to a more meaningful debug message

#### Alternatives

a. Keep both dynamic imports "for consistency" — the systemd one masks a design change that already happened
b. Remove postgres ImportError handling too — breaks users without stogger-postgres installed

#### Consequences

Systemd import is direct and fails at module level if broken (correct behavior). Postgres import remains defensive but with honest debug output.

## Verified By
