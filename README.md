# nicestlog

A sophisticated logging system built on top of [structlog](https://www.structlog.org/) that provides multi-target logging with different renderers for console output, systemd journal, and file logging.

## Features

- **Multi-target logging**: Console, file, and systemd journal simultaneously
- **Optimistic error handling**: Logging failures don't crash your application
- **Rich console formatting**: Colored output with structured data display
- **Structured logging**: Machine-parseable logs for monitoring and analysis
- **Command output logging**: Separate logging for external command output
- **Template-based messages**: Human-readable messages with graceful fallbacks
- **Systemd integration**: Automatic detection and proper journal integration
- **Development-friendly**: Rich debugging information when needed

## Installation

```bash
pip install nicestlog
```

## Quick Start

### Basic Console Logging

```python
import nicestlog
import structlog

# Initialize logging for console output
nicestlog.init_logging(verbose=True, syslog_identifier="myapp")

# Get a logger instance
log = structlog.get_logger()

log.info(
    "application-started",
    _replace_msg="Application {name} started successfully",
    name="myapp",
    version="1.0.0"
)
```

### File + Console Logging

```python
import nicestlog
import structlog
from pathlib import Path

# Setup with file and console logging
nicestlog.init_logging(
    logdir=Path("/var/log/myapp"),
    verbose=True,
    syslog_identifier="myapp"
)

log = structlog.get_logger()
log.info("Starting application", component="main")
```

For more examples and best practices, see the [documentation](docs/best_practices.md).

## CLI Docs Viewer

Use the built-in docs viewer to read project docs with colorized Markdown rendering.

```bash
# Show all docs (prefers local README.md + docs/*.md, falls back to packaged)
uv run nicestlog docs

# Show a specific doc by filename
uv run nicestlog docs README.md

# Use a glob pattern
uv run nicestlog docs 'docs/*.md'

# Disable pager (useful in CI or when piping output)
uv run nicestlog docs --no-pager

# List available docs (no rendering)
uv run nicestlog docs --list

# Filter by text content
uv run nicestlog docs --search "best practice"

# Change code block theme
uv run nicestlog docs --theme github
```

Behavior:
- Prefers local files: ./README.md and ./docs/*.md
- Falls back to packaged docs when installed as a package
- Supports selecting a specific file or glob pattern
- Pager can be disabled via --no-pager
- Uses Rich markdown rendering (with a code theme) for a pleasant reading experience


## i18n check (translation coverage)

Use the built-in CLI to verify that your translation files contain entries for all messages used in your source code.

- Includes .info events even when no `_replace_msg` is present
- Ignores `.debug` events for coverage; warns if `.debug` uses `_replace_msg`

Examples:

```bash
# Full report for English, using translations/en.toml
nicestlog i18n check . --translation-dir translations -l en

# Only print missing keys (one per line), good for CI scripting
nicestlog i18n check src --translation-dir translations -l en --list-missing

# Fail the check if missing keys exist
nicestlog i18n check . --translation-dir translations -l en --strict

# Also fail if extra (unused) keys exist in the translation file
nicestlog i18n check . --translation-dir translations -l en --fail-on-extra

# Combine list mode with strict/extra failure (machine-friendly + failing status)
nicestlog i18n check src --translation-dir translations -l en --list-missing --strict --fail-on-extra
```

CI example (GitHub Actions):

```yaml
name: i18n-check
on: [push, pull_request]
jobs:
  i18n:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync --locked
      - run: uv run nicestlog i18n check . --translation-dir translations -l en --list-missing --strict --fail-on-extra
```


## 🚀 Advanced AST Assistant

nicestlog now includes a revolutionary **Advanced AST Assistant** for sophisticated code analysis and transformation:

```bash
# Analyze Python code structure and patterns
nicestlog ast analyze my_script.py --verbose

# Transform code with comprehensive logging
nicestlog ast transform src/ --dry-run --pattern "*.py"

# List available transformation patterns
nicestlog ast patterns --list --details
```

**Key Features:**
- 🔍 **Deep AST Analysis** - Comprehensive code structure analysis
- 🔄 **Pattern-Based Transformations** - Convert print() to structured logging
- 📊 **Performance Metrics** - Detailed timing and analysis data
- 🛡️ **Safety Features** - Dry-run mode, backups, rollback capabilities
- 📝 **Extensive Logging** - Every operation logged with structured data

See [Advanced Assistant Documentation](docs/advanced_assistant.md) for complete details.

## License

MIT License
