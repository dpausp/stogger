# CLI Reference - Current Command Structure

> 📚 **Note:** For concrete before/after migration examples, see [Migration Examples](migration_examples.md)

## 🔄 Supported Migration Types

Nicestlog supports migration from various logging approaches:

| Source | Migration Type | Difficulty | Command |
|--------|---------------|------------|---------|
| **print() statements** | `print-to-structlog` | Easy | `nicestlog migrate . --no-dry-run --type print-to-structlog` |
| **Standard logging** | `logging-to-structlog` | Medium | `nicestlog migrate . --no-dry-run --type logging-to-structlog --interactive` |
| **CLI outputs (typer.echo, click.echo, rich.print)** | `cli-outputs-to-structlog` | Easy | `nicestlog migrate . --no-dry-run --type cli-outputs-to-structlog` |
| **Format strings** | `format-strings` | Easy | `nicestlog migrate . --no-dry-run --type format-strings` |
| **Eliot** | Enhancement | Easy | Already compatible! Use `nicestlog.eliot_integration` |
| **Sentry** | Integration | Easy | Use Sentry's `StructlogIntegration` |

## 🎯 Quick Start Migration

1. **Analyze your project** (safe, no changes):
   ```bash
   nicestlog migrate /path/to/project
   ```

2. **Preview migration changes**:
   ```bash
   nicestlog migrate /path/to/project --no-dry-run
   ```

3. **Apply migration**:
   ```bash
   nicestlog migrate /path/to/project --no-dry-run
   ```

4. **Validate results**:
   ```bash
   nicestlog check /path/to/project
   ```

## 📋 Main Commands

### `migrate` - Project Analysis and Migration

The primary command for analyzing and migrating projects to structured logging.

```bash
# Analyze project (default behavior - safe, dry-run)
nicestlog migrate .

# JSON output for automated processing
nicestlog migrate . --json

# Apply migration changes
nicestlog migrate . --no-dry-run

# Interactive migration with user confirmation
nicestlog migrate . --no-dry-run --interactive

# Specific migration type
nicestlog migrate . --no-dry-run --type logging-to-structlog
```

### `check` - Code Quality and Best Practices

For ongoing code quality in structlog-based projects.

```bash
# Check logging best practices with AST analysis
nicestlog check .

# Fix issues automatically
nicestlog check . --fix

# Fix issues interactively
nicestlog check . --interactive

# Preview fixes without applying
nicestlog check . --fix --dry-run
```

### `init` - Initialize Configuration

Initialize nicestlog configuration in your project.

```bash
# Initialize in current directory
nicestlog init

# Initialize in specific directory
nicestlog init /path/to/project

# Force overwrite existing config
nicestlog init --force
```

### `docs` - Documentation Viewer

Browse documentation directly from the CLI.

```bash
# Show all documentation
nicestlog docs

# Show documentation with pager
nicestlog docs --pager

# Interactive documentation browser
nicestlog docs --interactive

# Show docs for specific feature
nicestlog docs --feature logging
```

### `docs-serve` - Serve HTML Documentation

Serve HTML documentation in browser.

```bash
# Serve on default port (8000)
nicestlog docs-serve

# Serve on specific port
nicestlog docs-serve --port 9000

# Serve and open browser automatically
nicestlog docs-serve --open
```

## 🛠️ Tools Commands

Advanced utilities available under the `tools` subgroup.

### `tools generate-service` - Systemd Service Generator

Generate systemd service files for your applications.

```bash
# Generate service file
nicestlog tools generate-service myapp "/usr/bin/myapp --config /etc/myapp.conf"

# Specify user and working directory
nicestlog tools generate-service myapp "/usr/bin/myapp" --user myuser --working-dir /var/lib/myapp

# Output to file
nicestlog tools generate-service myapp "/usr/bin/myapp" --output myapp.service
```

### `tools review` - Log Quality Review

Review log quality and provide suggestions.

```bash
# Review log file or directory
nicestlog tools review /var/log/myapp.log

# Output in JSON format
nicestlog tools review /var/log/myapp.log --format json

# Set minimum quality score
nicestlog tools review /var/log/myapp.log --min-score 80.0
```

### `tools journal` - Systemd Journal Viewer

Beautiful systemd journal viewer.

```bash
# View last 50 journal entries
nicestlog tools journal

# View entries for specific unit
nicestlog tools journal --unit myapp.service

# Follow log output
nicestlog tools journal --follow

# Show logs since specific time
nicestlog tools journal --since "1 hour ago"

# Filter by log level
nicestlog tools journal --level error
```

### `tools dashboard` - Web Dashboard

Start the web dashboard (requires Flask).

```bash
# Start dashboard on default port (8080)
nicestlog tools dashboard

# Start on specific host and port
nicestlog tools dashboard --host 0.0.0.0 --port 9090

# Start in debug mode
nicestlog tools dashboard --debug
```

### `tools demo` - Interactive Demos

Run interactive demos to explore nicestlog features.

```bash
# List available demos
nicestlog tools demo

# Run specific demo
nicestlog tools demo basic

# Run all demos
nicestlog tools demo --all
```

### `tools i18n check` - Internationalization Check

Check translation completeness and quality.

```bash
# Check translations in source directory
nicestlog tools i18n check src

# Check specific language
nicestlog tools i18n check src --language de

# List missing translations
nicestlog tools i18n check src --list-missing

# Fail on extra translations
nicestlog tools i18n check src --fail-on-extra

# Strict mode (fail on any missing)
nicestlog tools i18n check src --strict

# Verbose output
nicestlog tools i18n check src --verbose
```

## 🔄 Migration Workflow

### Current (v3.x)
```bash
# 1. Analyze project (safe, default behavior)
nicestlog migrate .

# 2. Preview changes
nicestlog migrate . --no-dry-run

# 3. Apply changes
nicestlog migrate . --no-dry-run
```

## 🎯 Key Benefits of Current Design

1. **Safer by default**: Dry-run is default behavior, explicit `--no-dry-run` needed to apply changes
2. **Logical workflow**: Analysis is naturally part of migration
3. **Clear intent**: `--no-dry-run` makes destructive actions explicit
4. **Agent-friendly**: Clean JSON output with `--json`

## 📚 Detailed Migration Examples

### Project Analysis

```bash
# Human-readable analysis
nicestlog migrate .

# Machine-readable analysis
nicestlog migrate . --json
```

### Code Migration

```bash
# Analyze first
nicestlog migrate .

# Apply recommended changes
nicestlog migrate . --no-dry-run

# Specific type with interactive mode
nicestlog migrate . --no-dry-run --type logging-to-structlog --interactive
```

## 🤖 Agent/Script Usage

### JSON Output

```bash
# Get analysis data
nicestlog migrate . --json > analysis.json

# Parse recommendations
STRATEGY=$(cat analysis.json | jq -r '.recommendation.strategy')
```

### Automated Workflows

```bash
#!/bin/bash
# Agent workflow
nicestlog migrate . --json > analysis.json
STRATEGY=$(cat analysis.json | jq -r '.recommendation.strategy')
if [ "$STRATEGY" = "print-to-structlog" ]; then
    nicestlog migrate . --no-dry-run --type print-to-structlog
fi
```

## 🔧 Migration Checklist

### For Individual Users
- [ ] Update your shell aliases and scripts
- [ ] Replace deprecated command references with current ones
- [ ] Add `--no-dry-run` flag to actual migration commands
- [ ] Update any automation scripts

### For Teams/Organizations
- [ ] Update CI/CD pipelines
- [ ] Update team documentation and runbooks
- [ ] Train team members on new commands
- [ ] Update any deployment scripts

### For Tool Integrations
- [ ] Update IDE plugins or extensions
- [ ] Update monitoring/automation tools
- [ ] Update any wrapper scripts
- [ ] Test all integrations with new commands

## 🆘 Troubleshooting

### "Command not found" errors
If you see command not found errors, you might be using a very old version:
```bash
# Check your version
nicestlog --version

# Upgrade to latest
pip install --upgrade nicestlog
```

### Behavior differences
The current `migrate` command is safer by default:
- **Default**: `migrate` analyzes only (dry-run)
- **Apply changes**: Use `--no-dry-run` flag

## 📞 Getting Help

If you encounter issues:

1. **Read the help**: `nicestlog --help` or `nicestlog <command> --help`
2. **Test safely**: Use commands without `--no-dry-run` to analyze first
3. **Check documentation**: Updated guides at `nicestlog docs`

## 🎉 Welcome to the Current Version!

The current CLI design is:
- **Safer**: Dry-run by default prevents accidental changes
- **Cleaner**: Logical command hierarchy
- **Faster**: Quick analysis with `migrate`
- **Agent-friendly**: Consistent JSON output

Thank you for using nicestlog! 🚀