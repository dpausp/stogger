---
lifecycle:
  requirements:
    completed_at: "2026-05-04T14:00:00Z"
    git_rev: "be50a11"
  design:
    completed_at: "2026-05-15T00:00:00Z"
    git_rev: "e32969d"
  plan:
    completed_at: "2026-05-15T12:00:00Z"
    git_rev: "69aa1d3"
  workflow:
    completed_at: "2026-05-16T00:00:00Z"
    git_rev: "a40967b"
---

# logging-decorators-docs

## Context

The logging decorators (`log_call`, `log_result`, `log_operation`, `log_scope`) are implemented and functional (commit be50a11) but documentation-invisible. Autoapi skips `_decorators.py` due to the underscore prefix, leaving zero decorator entries in generated API docs. The `LogScope` class docstring has a truncated event schema example. No dedicated user-facing decorator documentation exists.

## Decisions

### docstring-quality

#### Context

All 5 public decorator docstrings (`log_call`, `log_result`, `log_operation`, `log_scope`, `LogScope`) already have Google-style Args, Returns, Raises, and Examples sections at the same quality level as `init_logging`. The only gap is the `LogScope` class docstring which has a truncated/incomplete event schema example.

#### Decision

Fix only the `LogScope` event schema example. The other 4 docstrings are already at benchmark quality.

#### Alternatives

a. Re-enrich all 5 docstrings against init_logging benchmark — unnecessary churn, the docstrings are already at target quality
b. Minimal docstrings + separate docs — forces users to look in two places

#### Consequences

Minimal diff, focused fix. `help()` and API docs already show complete usage information for all decorators.

### api-docs-visibility

#### Context

Autoapi skips `_decorators.py` because the `autoapi_skip_member` hook in `conf.py` rejects names starting with `_`. The re-exports in `core.py` are bare imports (`# noqa: F401`) so autoapi doesn't document them either. Generated `docs/api/stogger/core/index.rst` has zero decorator entries. The decorators live in `src/stogger/_decorators.py`.

#### Decision

Rename `_decorators.py` to `decorators.py` (remove underscore prefix). This makes autoapi generate the module documentation automatically. All imports must be updated: `core.py`, `__init__.py`, `tests/test_decorators.py`. The `tests/impl_spec/test_logging_decorators.py` file is deleted first per decision `spec-test-cleanup`, reducing the rename scope. Private helpers (`_extract_args`, `_filter_args`, `_make_func_name`) keep their underscore prefix so autoapi's existing skip logic still hides them.

#### Alternatives

a. Manual Sphinx directives in core/index.rst — fragile, requires maintenance when decorators change, manual sync with source
b. Modify autoapi_skip_member to allow `_decorators` — exposes private helper functions (_extract_args, _filter_args, _make_func_name) that shouldn't be in public docs

#### Consequences

Autoapi generates correct documentation automatically. Module is now publicly discoverable. Private helpers stay hidden via their underscore names. Import chain must be updated in 4+ files. The `impl_spec` test file should be deleted first (see decision `spec-test-cleanup`) to reduce rename scope.

### user-guide-integration

#### Context

`docs/user/logging_patterns.md` has manual "Function Tracing" and "Timing Operations" patterns that are exactly what the decorators automate. There are one-liner cross-references at lines 75 and 96 ("Or use the @log_call decorator instead") but no dedicated decorator section exists.

#### Decision

Add a new "Decorators" section to `logging_patterns.md` after the "Common Patterns" section. Cover all 4 features (`@log_call`, `@log_result`, `@log_operation`, `log_scope()`) with practical examples. Cross-reference from the existing "Function Tracing" and "Timing Operations" subsections.

#### Alternatives

a. New standalone page `docs/user/decorators.md` — fragments the logging patterns narrative
b. No user guide, rely on API docs only — poor discoverability for new users

#### Consequences

Users reading logging patterns naturally discover decorators. Single coherent page covers manual and automated approaches.

### spec-test-cleanup

#### Context

`tests/impl_spec/test_logging_decorators.py` (487 lines, 24 tests) is a leftover from the original implementation spec. The file header says "all tests are marked xfail because the feature doesn't exist yet" but they run green with no `@pytest.mark.xfail`. The permanent test file `tests/test_decorators.py` (235 lines, 15 tests) covers all decorator functionality comprehensively.

#### Decision

Delete `tests/impl_spec/test_logging_decorators.py` entirely. The implementation is complete and permanently tested.

#### Alternatives

a. Keep spec tests as extra coverage — redundant, creates confusion about test purpose, 487 lines of maintenance burden for no additional coverage

#### Consequences

Cleaner test tree. The permanent tests in `test_decorators.py` provide full coverage. Must be deleted before the module rename (decision `api-docs-visibility`) to reduce the number of files requiring import updates.

### test-strategy

#### Context

This is a documentation-only change (docstrings, module rename, user guide). Existing decorator tests (38 tests in 2 files, pytest + pytest-structlog) provide comprehensive functional coverage.

#### Decision

No new automated tests needed for this work. Documentation changes (docstrings, RST, user guide prose) are verified by the docs build (`tox` env `docs`).

#### Alternatives

a. Docstring smoke tests checking `help(log_call)` for expected sections — over-engineering for documentation work, docs build already validates docstring rendering

#### Consequences

Lower implementation effort. Docs build (`CI=1 uv run tox -p`) validates that docstrings render correctly in generated HTML.

## Requirements

### Files to Change

- **Rename**: `src/stogger/_decorators.py` → `src/stogger/decorators.py` — remove underscore prefix
- **Modify**: `src/stogger/core.py` — update import from `._decorators` to `.decorators`, fix LogScope truncated event schema
- **Modify**: `src/stogger/__init__.py` — import chain unchanged (imports from `core`)
- **Modify**: `docs/user/logging_patterns.md` — add "Decorators" section with examples for all 4 features
- **Delete**: `tests/impl_spec/test_logging_decorators.py` — obsolete spec validation tests
- **Modify**: `tests/test_decorators.py` — update any `_decorators` references to `decorators`

### Execution Order

1. Delete `tests/impl_spec/test_logging_decorators.py` first
2. Rename `src/stogger/_decorators.py` → `src/stogger/decorators.py`
3. Update all imports (`core.py`, `__init__.py`, `test_decorators.py`)
4. Fix LogScope truncated event schema in `decorators.py`
5. Add decorator section to `docs/user/logging_patterns.md`
6. Run `CI=1 uv run tox -p` to verify (includes docs build which regenerates autoapi)

### User Guide Requirements

New section must show: basic usage of all 4 features, arg filtering example, exception handling example, async usage. Each example must be self-contained and runnable.

## References

- `.agents/impl_specs/logging-decorators.md` — original implementation spec with event schemas and interface contracts

## Appendix

```yaml implementation_plan
description: "Make logging decorators documentation-visible: rename _decorators.py to decorators.py, fix LogScope docstring, add user guide section, delete obsolete spec tests"
specs:
  - .agents/impl_specs/logging-decorators-docs.md
target_tests:
  - file: tests/impl_spec/test_logging_decorators_docs.py
    tests:
      - test_decorators_module_importable
      - test_old_decorators_module_gone
      - test_decorators_module_exports_all_symbols
      - test_top_level_re_exports_sourced_from_decorators
      - test_old_spec_test_file_removed
      - test_logscope_docstring_has_complete_event_schema
      - test_logscope_docstring_no_truncated_json
      - test_log_call_module_is_decorators
      - test_log_scope_module_is_decorators
      - test_log_result_module_is_decorators
      - test_log_operation_module_is_decorators
      - test_logscope_class_module_is_decorators
id: logging-decorators-docs
created_at: "2026-05-15T12:00:00Z"
git_rev: "69aa1d3"
```
