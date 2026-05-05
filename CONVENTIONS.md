# Development Conventions

- Check pyproject.toml if you want to know more about the dependencies and dev tools.

## Code Style

Follow [PEP 8](https://peps.python.org/pep-0008/)

Configuration is in `pyproject.toml`:

- **ruff**: Linting and formatting (88 char line length)
- **mypy**: Strict type checking (Python 3.13+)
- **pytest**: Testing with 90% coverage target

### Code Quality Standards

- **Type hints**: Use modern type annotations (Python 3.9+ style with `list[str]` instead of `List[str]`)
- **Docstrings**: Use NumPy-style docstrings for public APIs
- **Error handling**: Prefer specific exceptions over generic `Exception`
- **Imports**: Use absolute imports, group by standard/third-party/local
- **Constants**: Use UPPER_CASE for module-level constants
- **Private members**: Use single underscore prefix for internal APIs

## Dependencies

- **uv** for package management
- sync dependencies for dev: `uv sync --all-groups --all-extras
- run commands with `uv run` to use the uv virtualenv
- Prefer uv, other that that, [PyPA packaging guidelines](https://packaging.python.org/) apply.

## Version Management

- **Version is managed with uv**: Use `uv version` command to bump versions
- Version is stored in `pyproject.toml` and automatically synced to `uv.lock`
- Common version bump commands:
  - `uv version patch` - for bug fixes (0.3.1 → 0.3.2)
  - `uv version minor` - for new features (0.3.1 → 0.4.0)
  - `uv version major` - for breaking changes (0.3.1 → 1.0.0)

## Project-Specific Patterns

### Important Packages

- **Typer** for CLI
- **Rich** for colored output and progress bars
- **structlog** for structured logging key value logging

### CLI Design (AI- and human-friendly, annotated)

- use `no_args_is_help=True` for all commands
- use modern Annotated option/argument style
- use modern Typer features
- group multiple related commands

#### CLI Best Practices

**Command Structure:**
- Use verb-noun pattern: `stoggertools check file.py`, `stoggertools migrate project/`
- Group related commands in sub-apps: `stoggertools tools review`, `stoggertools tools journal`
- Provide both short and long options: `-v/--verbose`, `-o/--output`

**Help and Documentation:**
- Rich help text with examples and use cases
- Include common usage patterns in command help
- Use emoji sparingly but effectively for visual hierarchy
- Provide `--help` for every command and subcommand
- Examples should be at the top of help text for discoverability

**Output Design:**
- Use Rich for colored, structured output
- Progress bars for long-running operations
- Clear success/error indicators (✅/❌)
- JSON output option for programmatic use (`--json`)

**Error Handling:**
- Meaningful error messages with suggested fixes
- Exit codes: 0 (success), 1 (user error), 2 (system error)
- Use `typer.Exit(code)` for controlled exits
- Log errors before exiting for debugging

**Standard CLI Flags (use consistently):**
- `--help, -h` (provided by Typer)
- `--version` (global option)
- `--verbose, -v` and `--quiet, -q`
- `--dry-run` (preview changes without executing)
- `--force, -f` (skip confirmations/overwrite when safe)
- `--output, -o` and `--input, -i`
- `--json` (structured output for programmatic use)
- `--no-color` (disable colored output)

**Input/Output Standards:**
- Primary results → stdout
- Logs and errors → stderr
- Support `--json` for structured output
- Ensure logs do not mix into JSON output
- Accept `-` for stdin/stdout when applicable

**Options and Arguments:**
```python
from __future__ import annotations
from pathlib import Path
from typing import Annotated
import typer

app = typer.Typer(no_args_is_help=True, add_completion=False)

@app.command()
def process(
    input_file: Annotated[
        Path,
        typer.Option("--input", "-i", help="Input file path", exists=True, readable=True),
    ],
    output_file: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output file (default: stdout)"),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit JSON to stdout"),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Show actions without executing"),
    ] = False,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Skip confirmations/overwrite when safe"),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Verbose output"),
    ] = False,
):
    """Process files with predictable flags.

    Examples:
        mytool process --input data.csv --output results.json
        cat data.csv | mytool process --input - --json
        mytool process --input file.txt --dry-run --verbose
    """
    try:
        if dry_run:
            typer.echo(f"Would process: {input_file}")
            raise typer.Exit(0)

        # ... perform work ...
        results = {"items": 3}

        if json_output:
            import json
            import sys
            json.dump(results, sys.stdout)
            sys.stdout.write("\n")
        else:
            typer.echo(f"✓ Processed {results['items']} items")

    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        typer.echo("Try: mytool process --input /path/to/existing/file", err=True)
        raise typer.Exit(1)
```

### Core Components

- **stogger.core**: Main logging initialization and configuration
- **stoggertools.cli**: Command-line interface with Typer
- **stogger.advanced_assistant**: AST-based code analysis and transformation
- **stoggertools.interactive_transformer**: Interactive code transformation with user prompts
- **stoggertools.linter**: Code quality checking for logging best practices
- **stogger.factory**: Logger factory and configuration management
- **stogger.i18n**: Internationalization support and translation checking

### Testing

- Use pytest conventions for Python tests (unit, functional, integration)
- Mock external dependencies in unit tests (filesystem, subprocess, API requests)
- Test names: `test_component_does_what_when_condition()`
- basic rule: one test module per code module per test style. 
- slow tests should be marked with @pytest.mark.slow

#### Testing Standards

**Test Organization:**
- Unit tests: `tests/test_module.py` for `src/package/module.py`
- Integration tests: `tests/test_integration_*.py`
- CLI tests: `tests/test_cli_*.py` (use subprocess or typer testing)
- Fixtures in `tests/conftest.py` for shared setup

**Test Quality:**
- Aim for 90%+ coverage but focus on critical paths
- Test both happy path and error conditions
- Use descriptive test names that explain the scenario
- Keep tests fast and independent (no shared state)

**Mocking Guidelines:**
```python
# Good: Mock external dependencies
@patch('subprocess.run')
def test_command_execution(mock_run):
    mock_run.return_value = CompletedProcess([], 0)
    result = run_command(['echo', 'test'])
    assert result.success

# Good: Use pytest fixtures for common setup
@pytest.fixture
def temp_project(tmp_path):
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text("[tool.test]")
    return project_dir
```

**Test Markers:**
- `@pytest.mark.slow` for tests taking >1 second
- `@pytest.mark.integration` for integration tests
- `@pytest.mark.cli` for CLI-specific tests

### Logging

- we use structured logging with structlog/stogger. No plain log messages or print statements!
- logging is configured on console to go to stderr.
- always use simple, descriptive event identifiers (max 4 words) in dash-case style

#### Log-Level Usage

- **`log.info()`** — user-facing messages. Always needs `_replace_msg`. No exceptions.
- **`log.debug()`** — developer/bug-report context. Never `_replace_msg`. Aim for 2-3
  key-value pairs, max 5. Marker-style (no key-values) only when truly no context exists.
- **`log.warning()`** — degraded but recoverable state. Not for "not found" (that's DEBUG)
  or "broken" (that's ERROR).
- **`log.error()`** — known failure, handled without exception traceback.
- **`log.exception()`** — only inside `except:` blocks. Stacktrace is automatic, never
  add `(error=str(e))` or similar.

#### Conventions

- **`_replace_msg` is mandatory for INFO**: Every `log.info()` call must have a
  `_replace_msg` with `{placeholder}` syntax for human-readable console output.
- **`_replace_msg` is forbidden for DEBUG**: Debug messages are key-value only,
  meant for developers and bug reports.
- **Consolidate, don't repeat**: If 3+ log calls fire in direct succession sharing the
  same context, merge them into one statement with all keys.

  ```python
  # ❌ BAD — three separate calls with shared context
  log.debug("extracting-docstring", node_type=type(node).__name__)
  log.debug("extracting-type-hint", has_annotation=annotation is not None)
  log.debug("extracting-decorators", decorator_count=len(decorator_list))

  # ✅ GOOD — one statement, all context
  log.debug("extracting-signature-meta",
            node_type=type(node).__name__,
            has_annotation=annotation is not None,
            decorator_count=len(decorator_list))
  ```

- **Use `log.bind()` for repeating context**: When the same keys appear 3+ times
  in a loop or scope, bind them once.

  ```python
  # ❌ BAD — repeating project= on every call
  for project in projects:
      log.info("project-start", project=str(project))
      log.info("project-done", project=str(project))

  # ✅ GOOD — bind once, use everywhere
  for project in projects:
      plog = log.bind(project=str(project))
      plog.info("project-start", _replace_msg="Starting {project}")
      plog.info("project-done", _replace_msg="Finished {project}")
  ```

- **NEVER use f-strings in log calls** — use `{key}` placeholders with separate
  key=value arguments. Placeholders and key=value work TOGETHER: the placeholder
  renders for humans, the key=value keeps data structured and filterable.

  ```python
  # ❌ FALSCH — f-string vergräbt Daten, not filterable
  log.info("fetching-session", _replace_msg=f"Fetching session {sid[:10]}…")

  # ✅ RICHTIG — placeholder + structured data, formatting is the processor's job
  log.info("fetching-session", _replace_msg="Fetching session {sid}…", sid=sid)
  ```

#### Examples

```python
logger.info("scan-finished", _replace_msg="Scan finished in {seconds} seconds", duration=duration, structured_data=value)
logger.debug("cache-hit", operation="scan", name=name, cache_type="redis")
logger.warning("degraded-performance", _replace_msg="Running without cache — slower responses", backend="redis")
logger.error("build-failed", strategy="sphinx", returncode=1)
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

### Git Workflow

**Commit Standards:**
- Use conventional commit format: `type(scope): description`
- Types: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `chore`
- Keep commits atomic (one logical change per commit)
- Write commit messages for future maintainers

**Branch Strategy:**
- `main` branch for stable releases
- Feature branches: `feat/feature-name` or `fix/issue-description`
- Keep branches short-lived and focused
- Rebase before merging to maintain clean history

**Pre-commit Hooks:**
- Automatic formatting with ruff
- Type checking with mypy
- Test execution for changed files
- Conventional commit message validation

## Documentation

**Code Documentation:**
- Use NumPy-style docstrings for public APIs
- Include examples in docstrings for complex functions
- Document type hints for all public interfaces
- Keep README.md up to date with current features

**NumPy Docstring Example:**
```python
def analyze_project(path: Path, verbose: bool = False) -> AnalysisResult:
    """Analyze a project for logging patterns and migration opportunities.
    
    Parameters
    ----------
    path : Path
        Path to the project directory to analyze
    verbose : bool, optional
        Enable verbose output during analysis, by default False
        
    Returns
    -------
    AnalysisResult
        Complete analysis results including patterns, dependencies, and recommendations
        
    Raises
    ------
    FileNotFoundError
        If the specified path does not exist
    ValueError
        If the path is not a valid project directory
        
    Examples
    --------
    >>> result = analyze_project(Path("/path/to/project"))
    >>> print(f"Found {len(result.patterns)} logging patterns")
    """
```

**User Documentation:**
- CLI help should be comprehensive and include examples
- Maintain user guides in `docs/` directory
- Use Sphinx for API documentation generation
- Include migration guides for breaking changes

## 📊 Document Insights and Discoveries

Document valuable findings in `docs/dev/lessons_learned.md`:

- Workflow improvements
- Tool behavior discoveries
- Problem patterns and solutions
- Interesting bugs and how we fixed them

Keep entries short and informal. The goal is to capture insights quickly, not to produce polished documents.

## Performance and Optimization

**Code Performance:**
- Profile before optimizing (use `cProfile` or `py-spy`)
- Optimize hot paths identified by profiling
- Consider async/await for I/O-bound operations
- Use appropriate data structures (sets for membership, dicts for lookups)

**Memory Management:**
- Use generators for large datasets
- Close file handles explicitly or use context managers
- Be mindful of circular references in complex object graphs
- Consider `__slots__` for classes with many instances

**CLI Performance:**
- Lazy import heavy dependencies
- Cache expensive computations when possible
- Provide progress bars for long-running operations
- Allow interruption with Ctrl+C (handle KeyboardInterrupt)

## Security Considerations

**Input Validation:**
- Validate and sanitize all user inputs
- Use Path objects instead of string manipulation for file paths
- Avoid shell injection with subprocess (use lists, not strings)
- Be careful with eval(), exec(), and dynamic imports

**File Operations:**
- Check file permissions before operations
- Use temporary files securely (tempfile module)
- Validate file types and sizes for uploads
- Be mindful of symlink attacks

**Logging Security:**
- Never log passwords, tokens, or sensitive data
- Sanitize user input in log messages
- Use structured logging to avoid injection attacks
- Consider log rotation and retention policies

