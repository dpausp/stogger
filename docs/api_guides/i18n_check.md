# i18n Check Module

:::{admonition} Test Coverage: 54.9%
:class: warning

This module has moderate test coverage. Some features may not work as expected.
:::

The `stogger.i18n_check` module checks completeness of stogger i18n translation files by scanning Python source files for translation key usage and verifying coverage.

## Basic Usage

```python
from pathlib import Path
from stogger.i18n_check import check_translations, format_report

# Check translation coverage
report = check_translations(
    source_paths=[Path("src/")],
    translation_dir=Path("translations"),
    language="at",
)

# Pretty-print the report
print(format_report(report))
```

## CLI Usage

```bash
stoggertools tools i18n check
```

## Functions

### scan_translation_keys

Scan Python files for all translation-related keys in a single pass.

```python
from stogger.i18n_check import scan_translation_keys

event_keys, msg_keys, debug_events = scan_translation_keys([Path("src/")])
```

Returns a tuple of `(event_keys, msg_keys, debug_events)`.

### find_required_translation_keys

Scan for keys required by the TranslationProcessor.

```python
from stogger.i18n_check import find_required_translation_keys

event_keys, msg_keys = find_required_translation_keys([Path("src/")])
```

### load_translation_keys

Load top-level keys from a TOML translation file.

```python
from stogger.i18n_check import load_translation_keys

keys = load_translation_keys(Path("translations/en.toml"))
```

### check_translations

Full translation coverage check returning a report dict.

```python
from stogger.i18n_check import check_translations

report = check_translations(
    source_paths=[Path("src/")],
    translation_dir=Path("translations"),
    language="en",
)

# Report keys:
# - required_keys: set[str]
# - translation_keys: set[str]
# - missing_keys: list[str]
# - missing_by_level: dict[str, list[str]]
# - extra_keys: list[str]
# - translation_file: str
# - msg_keys_found: set[str]
# - debug_with_replace_events: set[str]
```

### format_report

Format the report as a human-readable string.

```python
from stogger.i18n_check import format_report

print(format_report(report, include_debug=True))
```

### run_i18n_check_cli

Run the i18n check and print a report. Returns an exit code.

```python
from stogger.i18n_check import run_i18n_check_cli

exit_code = run_i18n_check_cli(
    path=".",
    translation_dir="translations",
    language="at",
    strict=True,
)
```

## Key Detection

The scanner detects translation keys from:
- Event names with `_replace_msg` in the same log call
- `.info("event")` calls
- Explicit `_msg_key` assignments
- Debug events using `_replace_msg` (excluded from required coverage)

## API Reference

```{autoapi} stogger.i18n_check
:members:
```
