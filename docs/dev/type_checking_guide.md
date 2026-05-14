# Type Checking Guide

Stogger uses **ty** (Astral's type checker, configured in `[tool.ty.src]`) for static type analysis. This guide covers the type patterns specific to this codebase.

## Project Type Configuration

```toml
# pyproject.toml
[tool.ty.src]
exclude = ["tests", "docs"]

requires-python = ">=3.13"
```

Type checking runs as part of `tox`:

```bash
# Via tox (recommended — runs with correct dependencies)
CI=1 uv run tox -p

# Direct (if needed)
uv run ty check src/
```

## Modern Type Syntax

Stogger targets Python 3.13+. Use modern syntax everywhere — no `typing` module imports for standard containers:

```python
# ✅ Correct — modern syntax
def process(data: dict[str, Any]) -> list[str] | None:
    ...

items: list[str] = []
config: dict[str, Any] = {}
result: str | None = None

# ❌ Wrong — legacy typing
from typing import List, Dict, Optional
def process(data: Dict[str, Any]) -> Optional[List[str]]:
    ...
```

## Common Patterns in Stogger

### attrs classes with type annotations

`StoggerConfig` and `FormatConfig` use `attrs.define`. Type annotations go directly on attributes:

```python
import attrs

@attrs.define(slots=False)
class FormatConfig:
    timestamp_precision: str = "iso_seconds"
    min_level: str = "info"
    show_code_info: bool = False
    pad_event_width: int = 30

@attrs.define
class StoggerConfig:
    verbose: bool = False
    logdir: Path | None = None
    systemd_facility: str | None = None
    ast_enabled_patterns: list | None = None
```

### Processor type signature

All structlog processors follow the `StructlogProcessor` protocol defined in `_types.py`:

```python
type EventDict = MutableMapping[str, Any]

class StructlogProcessor(Protocol):
    def __call__(
        self,
        logger: object,
        method_name: str,
        event_dict: EventDict,
    ) -> EventDict | None: ...
```

Use `EventDict` from `stogger._types` for processor signatures:

```python
from stogger._types import EventDict

def my_processor(_logger: object, _method_name: str, event_dict: EventDict) -> EventDict:
    event_dict["custom_field"] = "value"
    return event_dict
```

### `ty: ignore` directives

Stogger uses `ty: ignore` (not `type: ignore`) for the Astral type checker. Always include the specific error code:

```python
# ty: ignore[unresolved-import] — dynamic import of optional package
from stogger_systemd import get_journal_logger_factory  # ty: ignore[unresolved-import]

# ty: ignore[unresolved-attribute] — accessing private structlog API
structlog._frames._find_first_app_frame_and_name(...)  # ty: ignore[unresolved-attribute]

# ty: ignore[invalid-argument-type] — structlog processor chain typing gaps
structlog.configure(processors=processors)  # ty: ignore[invalid-argument-type]
```

### Dynamic imports for optional packages

Systemd and PostgreSQL support are optional. Use try/except with `ty: ignore`:

```python
if cfg.enable_postgres:
    try:
        from stogger_postgres import get_postgres_logger_factory  # ty: ignore[unresolved-import]
        factory = get_postgres_logger_factory(dsn=cfg.postgres_dsn, table=cfg.postgres_table)
        loggers["postgres"] = factory
    except ImportError:
        pass  # Optional package not installed
```

### `noqa` comments

Stogger uses Ruff with specific rule codes. Common suppressions:

```python
# noqa: SLF001 — accessing private attributes (e.g., _file, __attrs_init__)
# noqa: PLC0415 — late import inside function body (intentional for optional deps)
# noqa: T201 — print() statements (used for early stderr warnings)
# noqa: S603, S607 — subprocess without shell=False
```

## Troubleshooting

### `unresolved-import` for optional packages

The `stogger-systemd` and `stogger-postgres` packages are workspace members. They're imported dynamically and need `ty: ignore[unresolved-import]`.

### `invalid-argument-type` in processor chains

Structlog's processor chain typing doesn't perfectly match all stogger processor signatures. Use `ty: ignore[invalid-argument-type]` where the runtime behavior is correct but the type system can't verify it.

### attrs `__attrs_init__` access

`StoggerConfig.__init__` merges TOML config with kwargs and calls `self.__attrs_init__(...)`. This requires `ty: ignore[unresolved-attribute]` because attrs generates this method at class creation time.
