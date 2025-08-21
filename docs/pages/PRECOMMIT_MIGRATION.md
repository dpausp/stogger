# Pre-commit Migration Guide

## Overview

This project is migrating from bundled doit-based pre-commit hooks to individual tool-specific hooks while maintaining synchronization capabilities.

## Current State

- **Legacy**: `.pre-commit-config.yaml` - Uses doit tasks (bundled approach)
- **New**: `.pre-commit-config-individual.yaml` - Individual UV-based hooks
- **New**: `.pre-commit-config-individual-strict.yaml` - Individual UV-based hooks (strict mode)

## Migration Steps

### 1. Test the New Configuration

```bash
# Test individual hooks (development mode)
cp .pre-commit-config-individual.yaml .pre-commit-config.yaml
uv run pre-commit run --all-files

# Test strict hooks (CI-like mode)
cp .pre-commit-config-individual-strict.yaml .pre-commit-config.yaml
uv run pre-commit run --all-files
```

### 2. Compare Outputs

The new individual hooks provide:
- ✅ Tool-specific output and error messages
- ✅ Granular control over which tools run
- ✅ Better performance (parallel execution where possible)
- ✅ Standard pre-commit behavior and reporting

### 3. Synchronization

Use the sync script to keep pre-commit and doit in sync:

```bash
# Generate pre-commit configs from current doit tasks
python sync_precommit_doit.py

# Validate synchronization
python sync_precommit_doit.py --validate
```

## Tool Mapping

| Doit Task | Individual Hooks | Description |
|-----------|------------------|-------------|
| `doit format` | `ruff-format` + `ruff-check-fix` | Code formatting with auto-fix |
| `doit lint` | `ruff-check`, `mypy`, `pylint`, `bandit`, `safety`, `vulture` | All linting tools |
| `doit lint_strict` | Same as lint but with strict failure modes | Strict linting for CI |

## Key Differences

### Legacy (Doit-based)
```yaml
- id: format
  name: format (doit)
  entry: uv run doit format
  language: system
  pass_filenames: false
```

### New (Individual)
```yaml
- id: ruff-format
  name: ruff format
  entry: uv run ruff format
  language: system
  types: [python]
  require_serial: false

- id: ruff-check-fix
  name: ruff check --fix
  entry: uv run ruff check --fix
  language: system
  types: [python]
  require_serial: false
```

## Benefits

1. **Better Output**: Each tool provides its native output format
2. **Granular Control**: Can skip specific tools or run subsets
3. **Performance**: Tools can run in parallel where safe
4. **Standard Behavior**: Follows pre-commit conventions
5. **Debugging**: Easier to identify which specific tool failed

## Rollback Plan

If issues arise, simply restore the original configuration:

```bash
git checkout .pre-commit-config.yaml
```

## Integration with CI

For CI environments, use the strict configuration:

```bash
# In CI scripts
cp .pre-commit-config-individual-strict.yaml .pre-commit-config.yaml
pre-commit run --all-files
```

## Maintaining Synchronization

The `sync_precommit_doit.py` script should be run whenever doit tasks are modified to ensure pre-commit stays in sync.

Consider adding this to your development workflow:

```bash
# After modifying dodo.py
python sync_precommit_doit.py
git add .pre-commit-config-individual*.yaml
```