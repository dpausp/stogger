# CLI Migration Guide - v2.1 Command Changes

> 📚 **New!** For concrete before/after examples, see [Migration Examples](migration_examples.md)

## 🔄 Supported Migration Types

Nicestlog supports migration from various logging approaches:

| Source | Migration Type | Difficulty | Command |
|--------|---------------|------------|---------|
| **print() statements** | `print-to-structlog` | Easy | `stoggertools migrate . --do-migrate --type print-to-structlog` |
| **Standard logging** | `logging-to-structlog` | Medium | `stoggertools migrate . --do-migrate --type logging-to-structlog --interactive` |
| **Format strings** | `format-strings` | Easy | `stoggertools migrate . --do-migrate --type format-strings` |
| **Eliot** | Enhancement | Easy | Already compatible! Use `stogger_eliot` |
| **Sentry** | Integration | Easy | Use Sentry's `StructlogIntegration` |

## 🎯 Quick Start Migration

1. **Analyze your project** (safe, no changes):
   ```bash
   stoggertools migrate /path/to/project
   ```

2. **Apply migration with backup**:
   ```bash
   stoggertools migrate /path/to/project --do-migrate --backup
   ```

3. **Validate results**:
   ```bash
   stoggertools check /path/to/project --ast
   ```

## Overview

stogger v2.1 introduces a cleaner, more intuitive CLI structure. This guide helps existing users migrate to the new commands.

## 🚨 Breaking Changes Summary

The CLI has been restructured for better usability and logical workflow:

### Major Changes

1. **`analyze` command integrated into `migrate`**
   - Analysis is now the default behavior of `migrate`
   - Use `--do-migrate` flag to actually apply changes

2. **Deprecated commands moved or removed**
   - `tools analyze-project` → `migrate --json`
   - `tools ast *` → integrated into `check` and `fix`

## 📋 Command Migration Table

| Old Command | New Command | Notes |
|-------------|-------------|-------|
| `tools analyze-project .` | `migrate .` | Analysis is now default behavior |
| `tools analyze-project . --agent` | `migrate . --json` | Cleaner flag name |
| `analyze .` | `migrate .` | Top-level analyze deprecated |
| `analyze . --json` | `migrate . --json` | Same functionality |
| `tools init-config` | `init` | Merged into main init command |
| `tools ast analyze` | `check --ast` | AST analysis integrated |
| `tools ast transform` | `fix --ast` | AST transforms integrated |
| `tools ast interactive` | `fix --interactive` | Interactive mode integrated |

## 🔄 Migration Workflow Changes

### Before (v2.0)
```bash
# Separate commands for analysis and migration
stoggertools migrate .                   # Analyze project
stoggertools migrate . --dry-run          # Preview migration
stoggertools migrate .                    # Apply migration
```

### After (v2.1)
```bash
# Integrated workflow - safer and more logical
stoggertools migrate .                    # Analyze project (safe, default)
stoggertools migrate . --do-migrate      # Apply migration changes
```

## 🎯 Key Benefits of New Design

1. **Safer by default**: No accidental changes without explicit `--do-migrate`
2. **Logical workflow**: Analysis is naturally part of migration
3. **Faster typing**: `stogger migrate` for quick analysis
4. **Clear intent**: `--do-migrate` makes destructive actions explicit
5. **Agent-friendly**: Clean JSON output with `--json`

## 📚 Detailed Migration Examples

### Project Analysis

**Before:**
```bash
# Multiple ways to analyze (confusing)
stoggertools migrate .
stoggertools migrate . --json
stoggertools migrate . --json
```

**After:**
```bash
# Single, clear way
stoggertools migrate .                    # Human-readable analysis
stoggertools migrate . --json            # Machine-readable analysis
```

### Code Migration

**Before:**
```bash
# Separate analysis and migration steps
stoggertools check .
stoggertools migrate . --type print-to-structlog
```

**After:**
```bash
# Integrated workflow
stoggertools migrate .                              # Analyze first
stoggertools migrate . --do-migrate                # Apply recommended changes
stoggertools migrate . --do-migrate --type logging-to-structlog  # Specific type
```

### AST Operations

**Before:**
```bash
# Buried under tools ast
stoggertools check file.py --ast
stoggertools fix file.py --interactive
```

**After:**
```bash
# Integrated into main commands
stoggertools check file.py --ast
stoggertools fix file.py --interactive
```

### Configuration Setup

**Before:**
```bash
# Duplicate commands
stogger init
stogger init
```

**After:**
```bash
# Single, enhanced command
stoggertools init                         # Current directory
stoggertools init /path/to/project        # Specific directory
```

## 🤖 Agent/Script Migration

### JSON Output

**Before:**
```bash
# Multiple inconsistent ways
stoggertools migrate . --json
stoggertools migrate . --json
```

**After:**
```bash
# Single, consistent way
stoggertools migrate . --json
```

### Automated Workflows

**Before:**
```bash
#!/bin/bash
# Old agent workflow
stoggertools migrate . --json > analysis.json
STRATEGY=$(cat analysis.json | jq -r '.recommendation.strategy')
if [ "$STRATEGY" = "print-to-structlog" ]; then
    stoggertools migrate . --type print-to-structlog
fi
```

**After:**
```bash
#!/bin/bash
# New agent workflow
stoggertools migrate . --json > analysis.json
STRATEGY=$(cat analysis.json | jq -r '.recommendation.strategy')
if [ "$STRATEGY" = "print-to-structlog" ]; then
    stoggertools migrate . --do-migrate --type print-to-structlog
fi
```

## ⚠️ Deprecation Timeline

### Current Status (v2.1)
- ✅ **New commands available** and fully functional
- ⚠️ **Old commands deprecated** but still work with warnings
- 📚 **Documentation updated** to use new commands

### Future Versions
- **v2.2**: Deprecated commands show stronger warnings
- **v2.3**: Deprecated commands removed (breaking change)

## 🔧 Migration Checklist

### For Individual Users
- [ ] Update your shell aliases and scripts
- [ ] Replace `analyze` with `migrate` in documentation
- [ ] Add `--do-migrate` flag to actual migration commands
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
stogger --version

# Upgrade to latest
pip install --upgrade stogger
```

### Deprecated command warnings
These are normal during the transition period:
```bash
⚠️ DEPRECATED: 'analyze' command is deprecated.
   Use 'stogger migrate' instead (analysis is default behavior).
```

Simply replace the command as indicated in the warning.

### Behavior differences
The new `migrate` command is safer by default:
- **Old**: `migrate` would apply changes immediately
- **New**: `migrate` analyzes only, use `--do-migrate` to apply

## 📞 Getting Help

If you encounter issues during migration:

1. **Check the warnings**: Deprecated commands show exact replacements
2. **Read the help**: `stoggertools migrate --help`
3. **Test safely**: Use `migrate` without `--do-migrate` to analyze first
4. **Check documentation**: Updated guides at `stogger docs`

## 🎉 Welcome to v2.1!

The new CLI design is:
- **Safer**: No accidental changes
- **Cleaner**: Logical command hierarchy  
- **Faster**: Quick analysis with `migrate`
- **Agent-friendly**: Consistent JSON output

Thank you for using stogger! 🚀