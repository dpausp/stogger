# stogger

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
pip install stogger
```

## Quick Start

### 🔄 Migration from Existing Logging

Already have a project with print statements or standard logging? Nicestlog can migrate it automatically:

```bash
# Analyze your legacy project (safe, no changes)
stoggertools migrate /path/to/your/project

# Apply migration (dry-run preview by default)
stoggertools migrate /path/to/your/project --no-dry-run

# Validate results in structlog-based projects
stoggertools check /path/to/your/project
```

**Supported migrations:**
- ✅ `print()` statements → structured logging
- ✅ Standard `logging` module → structlog  
- ✅ Eliot integration (already compatible!)
- ✅ Sentry and other libraries

For ongoing code quality in structlog-based projects, use `stoggertools check` to identify logging anti-patterns and best practice violations.

📚 See [Migration Examples](docs/user_guide/migration_examples.md) for concrete before/after code examples.

### 🌱 New Project Setup

### Basic Console Logging

```python
import stogger
import structlog

# Initialize logging for console output
stogger.init_logging(verbose=True, syslog_identifier="myapp")

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
import stogger
import structlog
from pathlib import Path

# Setup with file and console logging
stogger.init_logging(
    logdir=Path("/var/log/myapp"),
    verbose=True,
    syslog_identifier="myapp"
)

log = structlog.get_logger()
log.info(
    "application-started",
    _replace_msg="Starting application",
    component="main"
)
```

📚 **Important**: Read the [Best Practices](docs/user_guide/best_practices.md) guide for effective logging patterns and common pitfalls to avoid.

For detailed CLI reference and command documentation, see [CLI Reference](docs/user_guide/cli_reference.md).

For detailed logging conventions and coding standards, see [Logging Conventions](docs/user_guide/logging_conventions.md).

For internationalization and translation coverage checking, see [i18n documentation](docs/features/i18n.md).

## Quick Command Reference

```bash
# Project analysis and migration (for legacy projects without structlog)
stoggertools migrate .                    # Analyze project (safe, default)
stoggertools migrate . --json            # JSON output for agents
stoggertools migrate . --no-dry-run      # Apply migration changes

# Code quality and fixes (for structlog-based projects)
stoggertools check .                      # Check logging best practices
stoggertools check . --fix                # Fix issues automatically
stoggertools check . --interactive        # Fix issues interactively

# Internationalization
stoggertools tools i18n check .           # Check translation coverage
stoggertools tools i18n check . --strict  # Fail on missing translations

# Setup and utilities
stoggertools init                         # Initialize configuration
stoggertools docs                         # Browse documentation
stoggertools docs --pager                 # Browse documentation with pager
stoggertools tools demo                   # Run interactive demos
```

## 🚀 Project Migration & Code Analysis

stogger includes powerful tools for analyzing existing projects and migrating them to use structured logging:

```bash
# Analyze legacy project for migration opportunities (safe, fast)
stoggertools migrate .

# Get JSON output for automated processing
stoggertools migrate . --json

# Actually apply migration changes (dry-run by default, so --no-dry-run is needed to apply)
stoggertools migrate . --no-dry-run

# Interactive migration with user confirmation
stoggertools migrate . --no-dry-run --interactive

# Specific migration type
stoggertools migrate . --no-dry-run --type logging-to-structlog
```

For ongoing code quality in structlog-based projects, use `stoggertools check` to identify logging anti-patterns and best practice violations.

**Key Features:**
- 🔍 **Project Analysis** - Comprehensive assessment of logging patterns
- 🔄 **Safe Migration** - Analyze first, migrate only with explicit flag
- 🎯 **Interactive Mode** - User confirmation for each change
- 📊 **Risk Assessment** - Complexity analysis and conflict detection
- 🛡️ **Safety Features** - Backup files, dry-run previews
- 🤖 **Agent-Friendly** - JSON output for programmatic consumption

**Migration Workflow:**
1. `stoggertools migrate .` - Analyze project (shows recommendations)
2. Review suggestions and warnings
3. `stoggertools migrate . --no-dry-run` - Apply changes

**For AI Agents:**
```bash
# Get structured analysis data
stoggertools migrate /path/to/project --json > analysis.json

# Parse recommendations
cat analysis.json | jq '.recommendation.strategy'
```

See [Agent Migration Guide](docs/agents/migration_guide.md) for complete workflows.

## License

AGPL-3.0 License
