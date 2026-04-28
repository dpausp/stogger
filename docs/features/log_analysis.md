# Log Statement Analysis

The stogger Log Statement Analyzer provides AST-based detection of logging anti-patterns and issues in Python code.

## Overview

The AST-based analyzer (`LogStatementAnalyzer`) automatically detects common logging issues and anti-patterns to help you maintain high-quality, structured logs.

## Detected Issues

### Missing Event ID

**Issue**: `missing_event_id`
**Description**: No event ID (first string argument) found in log call.

```python
log.info("user-login", user_id=123, action="login")
```

### Event ID Not Dash-Case

**Issue**: `event_id_not_dash_case`
**Description**: Event ID is not in preferred dash-case format.

```python
log.info("user-login", user_id=123)       # dash-case
```

### Event ID Many Elements

**Issue**: `event_id_many_elements`
**Description**: Event ID has 5 or more elements separated by dashes, underscores, or camelCase boundaries (readability warning).

### Event ID Too Many Elements

**Issue**: `event_id_too_many_elements`
**Description**: Event ID has 7 or more elements (readability error).

### Single String Argument

**Issue**: `single_string_argument`
**Description**: Exactly one string argument with no structured data — missing context.

```python
log.info("user-login", user_id=123, session_id="abc123")
```

### F-String in Event ID

**Issue**: `fstring_in_event_id`
**Description**: Event ID contains `{` or `}` (f-string/template in the ID).

```python
# Bad
log.info(f"user-{action}", user_id=123)

# Fixed
log.info("user-action", action=action, user_id=123)
```

### Debug with Replace Message

**Issue**: `debug_with_replace_msg`
**Description**: `log.debug(...)` used together with `_replace_msg` (usually not needed at debug level).

### Too Many Keyword Arguments

**Issue**: `too_many_kwargs`
**Description**: More than 7 regular keyword arguments (excluding magic args) — too complex/verbose.

```python
log.info("complex-event",
         user_data={"id": 1, "name": "Alice"},
         request_data={"method": "POST", "path": "/api"})
```

### No Structured Data

**Issue**: `no_structured_data`
**Description**: Event ID present, but no keyword arguments and no `_replace_msg` — structured data missing.

```python
log.info("user-login", user_id=123, ip="192.168.1.1")
```

### Debug for Error Event

**Issue**: `debug_for_error_event`
**Description**: `debug` level used for event IDs containing words like `error`, `fail`, `critical`, or `fatal`.

```python
log.error("database-error", error="Connection failed")
```

### Error Level for Info Event

**Issue**: `error_level_for_info_event`
**Description**: `error`/`critical` level while event ID contains words like `debug`, `trace`, or `info`.

```python
log.info("user-info-updated", user_id=123)
```

### Potential Secret Leak

**Issue**: `potential_secret_leak`
**Description**: Keyword argument name matches a known sensitive keyword (possible credential leak).

**Detected sensitive keywords**:
- `password`, `passwd`
- `secret`, `token`
- `auth_key`, `auth_token`
- `api_key`, `api_token`
- `credential`, `private_key`, `session_key`

### Event ID Too Long

**Issue**: `event_id_too_long`
**Description**: Event ID is longer than 50 characters.

## Magic Arguments

The analyzer recognizes these special "magic" arguments that don't count toward the keyword argument limit:

- `_replace_msg` — Custom message replacement
- `exc_info` — Exception information
- `_structured` — Structured data flag
- `_level` — Dynamic level setting
- `_name` — Logger name override

```python
# These magic args don't trigger "too_many_kwargs"
log.info("operation-failed",
         user_id=123,
         operation="payment",
         exc_info=True,              # Magic arg
         _replace_msg="Custom message")  # Magic arg
```

## Usage

### Command Line Analysis

```bash
# Analyze a single file
stoggertools check my_file.py

# Analyze a directory
stoggertools check src/

# Generate detailed analysis
stoggertools check src/ --complexity --verbose

# Dry-run fix
stoggertools check my_file.py --fix --dry-run
```

### Programmatic Analysis

```python
from pathlib import Path
from stoggertools.log_statement_analyzer import (
    LogStatementAnalyzer,
    analyze_file,
    print_analysis_summary,
)

# Module-level function — analyze a file
result = analyze_file(Path("my_module.py"), prefer_dash_case=True)

print(f"Total statements: {result.total_statements}")
print(f"With event ID: {result.statements_with_event_id}")
print(f"Without event ID: {result.statements_without_event_id}")
print(f"Dash-case violations: {result.dash_case_violations}")
print(f"Single string args: {result.single_string_args}")

# Print formatted summary
print_analysis_summary(result, verbose=True)

# Direct AST visitor usage
import ast

analyzer = LogStatementAnalyzer(prefer_dash_case=True)
tree = ast.parse(Path("my_module.py").read_text())
analyzer.visit(tree)
for stmt in analyzer.statements:
    print(f"L{stmt.line_number}: {stmt.method}({stmt.event_id}) issues={stmt.issues}")
```

## Continuous Integration

### GitHub Actions

```yaml
name: Log Quality Check
on: [push, pull_request]

jobs:
  log-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - name: Install stogger
        run: pip install stogger
      - name: Analyze logs
        run: stoggertools check src/ --complexity --verbose
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: stogger-analysis
        name: stogger log analysis
        entry: stoggertools check
        language: system
        files: \.py$
```
