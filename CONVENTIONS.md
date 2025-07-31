# Development Conventions

## Code Style

Follow [PEP 8](https://peps.python.org/pep-0008/) and [PyPA packaging guidelines](https://packaging.python.org/).

Configuration is in `pyproject.toml`:

- **ruff**: Linting and formatting (88 char line length)
- **mypy**: Strict type checking (Python 3.13+)
- **pytest**: Testing with 90% coverage target

## Dependencies

- **uv** for package management
- sync dependencies for dev: `uv sync --all-groups --all-extras`

## Project-Specific Patterns

### CLI Architecture

- **Typer** for CLI with `no_args_is_help=True` on all commands, modern Annotated option/argument style
- **Rich** for colored output and progress bars
- **Structured logging** with `structlog` (use event identifiers, not plain messages)

### Core Components

- **`core/`**: Business logic (scanner, registry, walker, cache)
- **`models/`**: Pydantic models for config and data validation
- **`utils/`**: Shared utilities (patterns, logging, archives)

### Testing

- Use pytest conventions for Python tests (unit, functional, integration)
- Use `timeout 60 uv run` for commands (never run without timeout)
- Mock external dependencies in unit tests (filesystem, subprocess)
- Test names: `test_component_does_what_when_condition()`

### Logging

- logging is configured on console to go to stderr.

```python
logger.info("userscan-finished", _replace_msg="Scan finished in {seconds} seconds", duration=duration, structured_data=value)
logger.debug("cache-hit", operation="scan", name=name)
logger.warn("missing-config-value", _replace_msg="Config: no value for {key}", key=key)
```

### Error Handling

- Log timing for long operations
- Log exceptions: `logger.error("cmd-call-error", username="bl", exc_info=True)`
- Use `typer.Exit(1)` for CLI errors
- Structured error context in logs

## Git

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(scanner): add ZIP archive support
fix(cli): handle missing config gracefully
test: boost coverage to 90%
```

- concise Git messages explaining the reason for the change and essential technical decisions.

