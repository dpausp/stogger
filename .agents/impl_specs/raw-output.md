---
lifecycle:
  requirements:
    completed_at: "2026-05-05T19:00:00Z"
    git_rev: c17bb39
  design:
    completed_at: "2026-05-05T19:30:00Z"
    git_rev: c17bb39
  plan:
    completed_at: "2026-05-15T12:00:00Z"
    git_rev: e32969d
---

# raw-output

## Context

`_render_output_sections` has no output key that preserves ANSI colors. Tool output from `ty check --color always` or `pytest --color yes` loses color meaning. The existing `write()` closure in `ConsoleFileRenderer.__call__` already splits correctly: console gets raw ANSI, file gets stripped. No new flag needed.

## Decisions

### raw-output-rendering

#### Context

`_render_output_sections` handles 6 output keys (`cmd_output_line`, `_output`, `stdout`, `stderr`, `stack`, `exception_traceback`). All strip ANSI via DIM wrapping or the `write()` closure. The `write()` closure writes raw to `console_io` then strips 10 colorama constants for `log_io` — this split already provides the desired console-preserve/file-strip behavior.

#### Decision

Add `_raw_output` and optional `_raw_output_prefix` to `_render_output_sections`. Render after `_output`, before `stdout`. No DIM, no RESET_ALL wrapping — just pass content through `write_fn()` directly. The existing `write()` closure handles ANSI preservation in console and stripping in file. When `_raw_output_prefix` is set, wrap with `prefix(prefix_str, content)` before passing to `write_fn()`.

#### Alternatives

a. `raw=True` flag on `write()` — unnecessary because `write()` already splits console/file correctly. The flag would be a no-op in both branches.
b. Direct `console_io.write()` bypass — duplicates stripping logic.
c. Tuple value `_raw_output=("prefix", content)` — breaks string-only convention of all output keys.

#### Consequences

Two new keys in output rendering pipeline. No changes to `write()` closure or its 17 existing call sites. Callers use `log.warning("type-errors", _raw_output=result.output.strip())`.

### skip-list-cleanup

#### Context

`KEYS_TO_SKIP_IN_JOURNAL_MESSAGE` has `"output"` (without underscore) but the actual key is `"_output"`. Bug inherited from original fc-agent code. `stdout` and `stderr` are missing entirely. The journal renderer uses this list to exclude keys from the message string.

#### Decision

Fix list: add `"_output"`, `"_raw_output"`, `"_raw_output_prefix"`, `"stderr"`, `"stdout"`. Keep `"output"` for backward compatibility. Sort alphabetically.

#### Alternatives

a. Only add new keys — perpetuates inherited bugs.
b. Remove `"output"` — risk breaking external consumers.

#### Consequences

All output-rendering keys correctly excluded from journal message string. Structured journal fields still contain the raw key-value data (journal renderer uppercases all remaining event_dict keys).

### test-strategy

#### Context

`TestRenderOutputSections` has one test (`test_render_output_sections_all_types`) that passes all 6 keys through a StringIO buffer and checks string presence. `test_console_renderer_output` exercises the full `ConsoleFileRenderer.__call__` and asserts `"\x1b" not in result["file"]` for ANSI stripping.

#### Decision

Extend both existing tests. Add `_raw_output` and `_raw_output_prefix` to `test_render_output_sections_all_types`. Add a new test method that passes ANSI-containing content through `_raw_output` via the full `__call__` path and asserts ANSI present in `result["console"]` and absent in `result["file"]`. Tests live in `tests/test_core.py` alongside existing output rendering tests.

#### Alternatives

a. Only extend existing all_types test — misses ANSI split verification.
b. New test class — overkill, existing class is the natural home.

#### Consequences

Two test changes: extend existing + one new method. Coverage for ANSI passthrough in console and stripping in file.

## Requirements

### Interface Contracts

Usage:
```python
log.warning(
    "component-type-errors",
    _replace_msg="{component}: {count} type error(s)",
    component=component_name,
    count=result.output.count("error:"),
    _raw_output_prefix="ty",
    _raw_output=result.output.strip(),
)
```

Discovery: `docs/user/logging_patterns.md` — new "Output Rendering" section with table of all 8 output keys. `docs/user/cheatsheet.md` — output blocks subsection.

### Documentation

New section "Output Rendering" in `docs/user/logging_patterns.md` covering all 8 keys: `cmd_output_line`, `_output`, `_raw_output`, `_raw_output_prefix`, `stdout`, `stderr`, `stack`, `exception_traceback`. Table with key, prefix behavior, DIM wrapping, ANSI behavior.

Update `docs/user/cheatsheet.md` with output keys reference.

### Files to Modify

| File | Change |
|------|--------|
| `src/stogger/core.py` `_render_output_sections` | Add `_raw_output` and `_raw_output_prefix` pop and render |
| `src/stogger/core.py` `KEYS_TO_SKIP_IN_JOURNAL_MESSAGE` | Fix and extend |
| `tests/test_core.py` `TestRenderOutputSections` | Extend all_types + new ANSI test |
| `tests/test_core.py` `TestConsoleFileRenderer` | Extend for _raw_output |
| `docs/user/logging_patterns.md` | New "Output Rendering" section |
| `docs/user/cheatsheet.md` | Add output keys reference |

## Appendix

```yaml
# implementation_plan
id: raw-output
description: "Add _raw_output and _raw_output_prefix keys to output rendering pipeline for ANSI-preserving tool output display"
git_rev: e32969d
created_at: "2026-05-15T12:00:00Z"
target_tests:
  - file: tests/impl_spec/test_raw_output.py
    tests:
      - TestRawOutputRendering::test_raw_output_popped_from_event_dict
      - TestRawOutputRendering::test_raw_output_no_dim_wrapping
      - TestRawOutputRendering::test_raw_output_with_prefix
      - TestRawOutputRendering::test_raw_output_without_prefix
      - TestRawOutputRendering::test_raw_output_rendered_after_output_before_stdout
      - TestRawOutputRendering::test_raw_output_none_skipped
      - TestSkipListCleanup::test_required_keys_present
      - TestSkipListCleanup::test_skip_list_sorted_alphabetically
      - TestRawOutputAnsiPassthrough::test_ansi_preserved_in_console_stripped_from_file
      - TestRawOutputAnsiPassthrough::test_raw_output_content_preserved_in_both
      - TestRawOutputAnsiPassthrough::test_raw_output_with_prefix_through_full_call
```

