# Logging Rules Specification for nicestlog check

This document outlines all current logging rules implemented in nicestlog's linter, along with detailed examples of how the output would appear in the proposed "full" format, oriented towards ruff's style.

## Overview

The "full" output format displays each issue with:
- File path, line number, and column (if applicable)
- Issue code/category and message
- Source code context with highlighting
- Help text for fixing the issue

At the end, a summary of total issues, files affected, and fixable items.

## Current Logging Rules

### 1. Log Level Appropriateness (`level`)

**Rule**: Library code should use `debug` level for internal operations to avoid spamming users. User-facing code can use `info`, but errors should be `error` or higher.

**Detection**: Checks log calls in functions/methods and suggests appropriate levels based on context (e.g., library init → debug).

**Example Output**:
```
src/nicestlog/cli.py:45:level Library initialization should be debug level to avoid user spam
   |
43 |     def __init__(self):
44 |         # Initialize library
45 |         log.info("initializing-library")
   |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   |
   = help: Change to log.debug("initializing-library") for less verbosity
```

### 2. Exception Logging (`except_logging`)

**Rule**: Inside `except` blocks, use `log.exception()` to include full traceback, or pass `exc_info=True` to logging calls.

**Detection**: Scans `except` blocks for log calls without `exc_info` or `log.exception()`.

**Example Output**:
```
src/nicestlog/core.py:120:except_logging Inside except: prefer log.exception(...) or pass exc_info=True to include traceback
   |
118 |     except Exception as e:
119 |         # Handle error
120 |         log.error("failed", error=str(e))
   |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   |
   = help: Use log.exception("failed") or log.error("failed", exc_info=True)
```

### 3. Logging Coverage (`coverage`)

**Rule**: Each file should have a minimum percentage of lines with logging statements (default 5.0%, configurable).

**Detection**: Counts log statements vs. total executable lines in functions.

**Example Output** (file-level issue):
```
src/nicestlog/utils.py: Too little logging! 2.3% coverage (minimum: 5.0%)
   |
   = help: Add more log statements or adjust minimum in config
```

## Summary Format

At the end of the output:

```
Found 3 logging issues across 5 files.
[*] 2 fixable with the `--fix` option.
```

This specification can be expanded as new rules are added.