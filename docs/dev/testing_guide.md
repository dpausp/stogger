# Testing Guide

How tests are structured, what fixtures exist, and what patterns to follow when writing tests for stogger.

## Test Structure

```
tests/
├── conftest.py                    # Shared autouse fixture
├── test_core.py                   # Core rendering and pipeline tests
├── test_config.py                 # StoggerConfig and project detection
├── test_factory.py                # Factory and stdlib integration
├── test_decorators.py             # log_call, log_result, log_operation, log_scope
├── test_integration.py            # Cross-module pipeline tests
├── test_architecture.py           # pytest-archon layer boundary rules
├── test_exception_logging.py      # AST-based except-block convention checks
├── test_e2e_single_module_app.py  # Full pipeline, no mocks
├── test_systemd_integration.py    # Systemd renderer (mocked)
├── test_systemd_integration_real.py # Requires stogger-systemd package
├── test_postgres_integration.py   # Postgres renderer (mocked)
├── test_postgres_integration_real.py # Requires stogger-postgres package
```

## Markers

Defined in `pyproject.toml [tool.pytest.ini_options]`:

- `@pytest.mark.integration` — Tests real module interactions (most tests)
- `@pytest.mark.e2e` — Full pipeline exercises with no mocks
- `@pytest.mark.slow` — Tests taking more than 1 second

Run fast tests only: `uv run pytest -m "not slow"`

## Key Fixtures

### `conftest.py` — autouse structlog reset

```python
@pytest.fixture(autouse=True)
def _reset_structlog():
    """Reset structlog configuration after each test to avoid state leakage."""
    yield
    structlog.reset_defaults()
```

Every test file gets this automatically. Tests that configure structlog themselves (e.g., `test_integration.py`) also include a cleanup fixture that closes file handles from `MultiOptimisticLoggerFactory`.

### `captured_events` (test_decorators.py)

Configures structlog with a capturing processor that appends every event dict to a list. Used to assert on decorator output:

```python
@pytest.fixture
def captured_events():
    events: list[dict] = []
    structlog.configure(
        processors=[lambda _, __, ed: (events.append(dict(ed)), str(ed))[1]],
        wrapper_class=structlog.BoundLogger,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )
    return events
```

### `create_pyproject_toml` (test_config.py)

Creates a temporary `pyproject.toml` with `[tool.stogger]` settings and patches `Path.cwd()`:

```python
@pytest.fixture
def create_pyproject_toml():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)
        pyproject_path = config_dir / "pyproject.toml"
        with open(pyproject_path, "w") as f:
            f.write('[tool.stogger]\nverbose = true\n...')
        with patch("pathlib.Path.cwd", return_value=config_dir, autospec=True):
            yield
```

### `source_files` and `stogger_config` (test_exception_logging.py)

Provided by pytest-stogger. Returns source file paths and `[tool.pytest-stogger]` config for AST-based convention checking.

## Testing Patterns

### Configuring structlog in tests

Always set `cache_logger_on_first_use=False` so the autouse reset fixture can reconfigure:

```python
structlog.configure(
    processors=[...],
    wrapper_class=structlog.BoundLogger,
    logger_factory=...,
    cache_logger_on_first_use=False,
)
```

### Testing renderers

Call the renderer directly with the structlog processor signature `(logger, method_name, event_dict)`:

```python
renderer = ConsoleFileRenderer(format_config=FormatConfig())
result = renderer(None, "info", {
    "event": "test-event",
    "timestamp": "2024-01-01T00:00:00Z",
    "level": "info",
})
assert "test-event" in result["console"]
```

### Testing decorator output

Use `captured_events` fixture, then assert on the event dict:

```python
def test_log_call_captures_args(captured_events):
    @log_call
    def greet(name: str):
        return f"hello {name}"

    greet("world")
    evt = captured_events[0]
    assert evt["event"] == "called"
    assert evt["args"] == {"name": "world"}
```

### Architecture enforcement

`test_architecture.py` uses pytest-archon to enforce the dependency graph:

```
config.py ← (no internal deps)
_types.py ← (no internal deps)
_colors.py ← (no internal deps)
_regexes.py ← (no internal deps)
processors.py ← config.py
core.py ← config.py, _types.py, processors.py, _colors.py
factory.py ← config.py, core.py, processors.py
```

### AST convention checks

`test_exception_logging.py` runs pytest-stogger rules against the source. The `[tool.pytest-stogger]` section in `pyproject.toml` configures which files to scan and per-file rule exemptions.

## Coverage

Configured in `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["src"]
branch = true
omit = ["tests/*", ".venv/*"]

[tool.coverage.report]
show_missing = true
precision = 2
```

Run with: `uv run pytest --cov=stogger --cov-report=term-missing`

## Commands

| Command | Purpose |
|---------|---------|
| `uv run pytest` | Run all tests |
| `uv run pytest -m "not slow"` | Fast tests only |
| `uv run pytest -m integration` | Integration tests |
| `uv run pytest -m e2e` | End-to-end tests |
| `uv run pytest --cov=stogger` | Tests with coverage |
| `CI=1 uv run tox -p` | Full CI pipeline (lint, test, docs, build) |
