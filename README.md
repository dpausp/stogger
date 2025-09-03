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

### 🔄 Migration from Existing Logging

Already have a project with print statements or standard logging? Nicestlog can migrate it automatically:

```bash
# Analyze your project (safe, no changes)
nicestlog migrate /path/to/your/project

# Apply migration with backup
nicestlog migrate /path/to/your/project --do-migrate --backup

# Validate results
nicestlog check /path/to/your/project
```

**Supported migrations:**
- ✅ `print()` statements → structured logging
- ✅ Standard `logging` module → structlog  
- ✅ Eliot integration (already compatible!)
- ✅ Loguru, Sentry, and other libraries

📚 See [Migration Examples](docs/user_guide/migration_examples.md) for concrete before/after code examples.

### 🌱 New Project Setup

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

For more examples and best practices, see the [documentation](docs/user_guide/best_practices.md).

For internationalization and translation coverage checking, see [i18n documentation](docs/features/i18n.md).

## Quick Command Reference

```bash
# Project analysis and migration
nicestlog migrate .                    # Analyze project (safe, default)
nicestlog migrate . --json            # JSON output for agents
nicestlog migrate . --do-migrate      # Apply migration changes

# Code quality and fixes
nicestlog check .                      # Check logging best practices
nicestlog check . --fix                # Fix issues automatically
nicestlog check . --interactive        # Fix issues interactively

# Internationalization
nicestlog i18n check .                 # Check translation coverage
nicestlog i18n check . --strict        # Fail on missing translations

# Setup and utilities
nicestlog init                         # Initialize configuration
nicestlog docs                         # Browse documentation
nicestlog docs --pager                 # Browse documentation with pager
nicestlog tools demo                   # Run interactive demos
```

## CLI Docs Viewer

Use the built-in docs viewer to read project docs with colorized Markdown rendering.

```bash
# Show all docs (prefers local README.md + docs/*.md, falls back to packaged)
uv run nicestlog docs

# Show a specific doc by filename
uv run nicestlog docs README.md

# Use a glob pattern
uv run nicestlog docs 'docs/*.md'

# Use pager for displaying docs (uses glow, bat, or less/more)
uv run nicestlog docs --pager
```

Behavior:
- Prefers local files: ./README.md and ./docs/*.md
- Falls back to packaged docs when installed as a package
- Supports selecting a specific file or glob pattern
- Uses Rich markdown rendering (with a code theme) for a pleasant reading experience
- With --pager flag, uses glow (if installed), bat (if installed), or falls back to less/more


## 🚀 Project Migration & Code Analysis

nicestlog includes powerful tools for analyzing existing projects and migrating them to use structured logging:

```bash
# Analyze project for migration opportunities (safe, fast)
nicestlog migrate .

# Get JSON output for automated processing
nicestlog migrate . --json

# Actually apply migration changes
nicestlog migrate . --do-migrate

# Interactive migration with user confirmation
nicestlog migrate . --do-migrate --interactive

# Specific migration type
nicestlog migrate . --do-migrate --type logging-to-structlog
```

**Key Features:**
- 🔍 **Project Analysis** - Comprehensive assessment of logging patterns
- 🔄 **Safe Migration** - Analyze first, migrate only with explicit flag
- 🎯 **Interactive Mode** - User confirmation for each change
- 📊 **Risk Assessment** - Complexity analysis and conflict detection
- 🛡️ **Safety Features** - Backup files, dry-run previews
- 🤖 **Agent-Friendly** - JSON output for programmatic consumption

**Migration Workflow:**
1. `nicestlog migrate .` - Analyze project (shows recommendations)
2. Review suggestions and warnings
3. `nicestlog migrate . --do-migrate` - Apply changes with backups

**For AI Agents:**
```bash
# Get structured analysis data
nicestlog migrate /path/to/project --json > analysis.json

# Parse recommendations
cat analysis.json | jq '.recommendation.strategy'
```

See [Agent Migration Guide](docs/agents/migration_guide.md) for complete workflows.

## License

AGPL-3.0 License
