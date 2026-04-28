# pytest-stogger

Automatic AST-based logging convention checking for pytest.

Install the plugin, run `pytest`, all rules execute against every `.py` file under `src/`. Zero config required.

## Installation

    uv add --dev pytest-stogger

## Quick Start

Just run pytest:

    uv run pytest

The plugin creates one test item per source file plus a cross-file logging-coverage check. No test files to write.

Example output:

    src/mypackage/__init__.py::stogger PASSED
    src/mypackage/core.py::stogger PASSED
    stogger::logging-coverage PASSED

## Configuration

Optional in `pyproject.toml`:

```toml
[tool.pytest-stogger]
source = "src/mypackage"    # default: "src"
test_dir = "tests"          # default: "tests"
exclude = ["vendor"]
disable_rules = []
info_allowed_layers = []    # empty = layer rule skipped
exempt_event_ids = []
infrastructure_files = []
```

CLI overrides:

    pytest --stogger-source=src/mypackage --stogger-exclude vendor generated

## Built-in Rules

12 file-level rules run per source file, plus 1 cross-file coverage check.

- **log-kebab-case-event-id** — event IDs must use `kebab-case`
- **log-context-required** — log calls must include keyword arguments
- **log-no-fstring** — no f-strings in log messages
- **log-requires-replace-msg** — `log.info()` must use `replace_msg`
- **log-debug-no-replace-msg** — `log.debug()` must not use `replace_msg`
- **log-exception-no-error-keyword** — no duplicate `error` in exception logging
- **no-log-info-in-except** — no `log.info()` in except blocks
- **except-must-log** — except blocks must contain a log call (excludes `infrastructure_files`)
- **log-use-bind-for-repeating-keys** — repeating structured keys must use `bind()`
- **private-no-log-info** — private functions must not use `log.info()`
- **complexity-needs-log** — complex functions must contain log calls (excludes `infrastructure_files`)
- **log-info-layer-restriction** — `log.info()` only in allowed layers (requires `info_allowed_layers`)
- **logging-coverage** — every non-debug log event ID must have a corresponding test assertion

Disable specific rules:

```toml
[tool.pytest-stogger]
disable_rules = ["log-info-layer-restriction", "logging-coverage"]
```

## Fixtures

For custom checks, session-scoped fixtures are available:

- **`source_files`** — `list[tuple[Path, ast.Module]]` — all parsed Python files
- **`stogger_source`** — `Path` — resolved source directory
- **`stogger_exclude`** — `frozenset[str]` — excluded directory names
- **`stogger_config`** — `dict[str, Any]` — raw config from `pyproject.toml`

## Provided Helpers

### `is_method_call(node, obj, methods)`

Match `obj.method()` AST patterns. Returns `(method_name, call_node)` or `None`.

### `walk_python_files(source, exclude=...)`

Yield `(path, tree)` for every parseable `.py` file.

### `format_violations(violations)`

Format a `{rule_name: [messages]}` dict into a readable string.
