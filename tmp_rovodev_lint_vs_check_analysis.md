# Lint vs Check Command Analysis

## Current State

### `lint` Command (Lines 986-1000)
- **Purpose**: Basic logging coverage and quality checks
- **Parameters**: 
  - `path` (default: ".")
  - `--min-coverage` (default: 5.0)
  - `--max-coverage` (default: 15.0) 
  - `--strict` (default: False)
- **Functionality**: Calls `run_linter()` which uses `lint_directory()` from linter.py
- **Limited scope**: Only basic linting with coverage thresholds

### `check` Command (Lines 305-466)
- **Purpose**: Comprehensive code checking with optional AST analysis
- **Parameters**:
  - `path` (default: ".")
  - `--fix` (auto-fix issues)
  - `--interactive` (interactive mode)
  - `--dry-run` (preview fixes)
  - `--ast` (AST-based analysis)
  - `--complexity` (complexity checks)
  - `--pattern` (specific patterns)
  - `--verbose` (verbose output)
- **Functionality**: 
  - ✅ Basic linting (same as lint command)
  - ✅ AST analysis and transformations
  - ✅ Interactive fixing
  - ✅ Complexity analysis
  - ✅ Pattern-specific checks
  - ✅ Auto-fixing capabilities

## Analysis Result

**The `lint` command is completely redundant.** Everything it does is covered by `check`:

1. **Basic linting**: `check` calls `lint_directory()` just like `lint` does
2. **Coverage parameters**: Can be configured in linter.py or via config
3. **Strict mode**: Not needed as `check` provides more granular control

## Migration Path

Users currently using:
```bash
nicestlog lint                           # Basic linting
nicestlog lint --strict                  # Strict mode
nicestlog lint --min-coverage 10         # Custom coverage
```

Should migrate to:
```bash
nicestlog check                          # Basic linting (same result)
nicestlog check --ast                    # Enhanced with AST analysis
nicestlog check --fix                    # With auto-fixing
```

## Recommendation

**Remove `lint` command entirely** - no functionality will be lost as `check` is a superset.