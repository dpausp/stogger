# Development Conventions

- Check pyproject.toml if you want to know more about the dependencies and dev tools.

## Code Style

Follow [PEP 8](https://peps.python.org/pep-0008/)

Configuration is in `pyproject.toml`:

- **ruff**: Linting and formatting (88 char line length)
- **mypy**: Strict type checking (Python 3.13+)
- **pytest**: Testing with 90% coverage target

## Dependencies

- **uv** for package management
- sync dependencies for dev: `uv sync --all-groups --all-extras
- run commands with `uv run` to use the uv virtualenv
- Prefer uv, other that that, [PyPA packaging guidelines](https://packaging.python.org/) apply.

## Project-Specific Patterns

### Important Packages

- **Typer** for CLI
- **Rich** for colored output and progress bars
- **structlog** for structured logging key value logging

### CLI

- use `no_args_is_help=True` for all commands
- use modern Annotated option/argument style
- use modern Typer features
- group multiple related commands

### Core Components

- **nicestlog.core**: Main logging initialization and configuration
- **nicestlog.cli**: Command-line interface with Typer
- **nicestlog.advanced_assistant**: AST-based code analysis and transformation
- **nicestlog.interactive_transformer**: Interactive code transformation with user prompts
- **nicestlog.linter**: Code quality checking for logging best practices
- **nicestlog.factory**: Logger factory and configuration management
- **nicestlog.i18n**: Internationalization support and translation checking

### Testing

- Use pytest conventions for Python tests (unit, functional, integration)
- Mock external dependencies in unit tests (filesystem, subprocess, API requests)
- Test names: `test_component_does_what_when_condition()`
- basic rule: one test module per code module per test style. 
- slow tests should be marked with @pytest.mark.slow

### Logging

- we use structured logging with structlog/nicestlog. No plain log messages or print statements!
- logging is configured on console to go to stderr.
- always use simple, descriptive event identifiers (max 4 words) in dash-case style
- log.info needs a _replace_msg meant for user-focused output relevant to all users
- log.debug must not have a _replace_msg, just key value info. It's meant for developers and users that want to report issues.
- use log.bind(key=val) to avoid common repeating keys 3 times or more
- use log.exception() to log exceptions. Exceptions are handled automatically
  by the logging library, don't add (error=str(e)) or something like that on
  your own.

```python
logger.info("scan-finished", _replace_msg="Scan finished in {seconds} seconds", duration=duration, structured_data=value)
logger.debug("cache-hit", operation="scan", name=name, cache_type="redis")
logger.warn("missing-config-value", _replace_msg="Config: no value for {key}", key=key)
logger.exception("subprocess-failed", cmd=cmd)
```

### Error Handling

- Log timing for long operations
- Log exceptions: `logger.exception("cmd-call-error", action="commit", cmd=cmd, username=username)`
- Use `typer.Exit(1)` for top-level CLI errors only

## Git

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(scanner): add ZIP archive support
fix(cli): handle missing config gracefully
test: boost coverage to 90%
```

- concise Git messages explaining the reason for the change and essential technical decisions. Markdown formatting is allowed.

