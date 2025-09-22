# 🔍 Log Statement Analysis

The nicestlog Log Statement Analyzer provides intelligent detection of logging anti-patterns and issues in your Python code using AST-based analysis.

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

### Single String Argument

**Issue**: `single_string_argument`
**Description**: Exactly one string argument with no structured data - missing context.

```python
log.info("user-login", user_id=123, session_id="abc123")
```

### F-String in Event ID

**Issue**: `fstring_in_event_id`
**Description**: Event ID contains `{` or `}` (f-string/template in the ID).

```python
# ❌ Problematic
log.info(f"user-{action}", user_id=123)

# ✅ Fixed
log.info("user-action", action=action, user_id=123)
```

### Debug with Replace Message

**Issue**: `debug_with_replace_msg`
**Description**: `log.debug(...)` used together with `_replace_msg` (usually not needed).

```python
log.debug("debug-info", data=value)
```

### Too Many Keyword Arguments

**Issue**: `too_many_kwargs`
**Description**: More than 7 regular keyword arguments (excluding magic args) - too complex/verbose.

```python
log.info("complex-event", 
         user_data={"id": 1, "name": "Alice"},
         request_data={"method": "POST", "path": "/api"})
```

### No Structured Data

**Issue**: `no_structured_data`
**Description**: Event ID present, but no keyword arguments and no `_replace_msg` - structured data missing.

```python
log.info("user-login", user_id=123, ip="192.168.1.1")
```

### Debug for Error Event

**Issue**: `debug_for_error_event`
**Description**: `debug` level used for event IDs that sound like errors.

```python
log.error("database-error", error="Connection failed")
```

### Error Level for Info Event

**Issue**: `error_level_for_info_event`
**Description**: `error`/`critical` level while event ID looks like info/debug.

```python
log.info("user-info-updated", user_id=123)
```

### Potential Secret Leak

**Issue**: `potential_secret_leak`
**Description**: Keyword name appears sensitive (possible credential leak).

```python
log.info("api-call", user_id=123, endpoint="/api/users")
```

**Detected sensitive keywords**:
- `password`, `passwd`, `pwd`
- `secret`, `token`, `key`
- `api_key`, `private_key`, `access_token`
- `credential`, `auth`, `authorization`

### Event ID Too Long

**Issue**: `event_id_too_long`
**Description**: Event ID is longer than 50 characters.

```python
log.info("long-operation-completed", operation_type="data-processing")
```

### Log Wrapper Anti-Patterns

**Issue**: `wrapper_function`
**Description**: Functions that unnecessarily wrap logging calls with additional indirection.

Log wrapper functions create unnecessary abstraction layers that make debugging harder and reduce the effectiveness of structured logging. They often hide the actual location where logging occurs and can make it difficult to trace log statements back to their source.

```python
# ❌ Problematic - Wrapper functions
def log_debug(message):
    print(f"DEBUG: {message}")

def write_info(msg):
    logging.info(msg)

def emit_warning(text):
    logger.warning(text)

def log_user_action(user_id, action):
    log.info(f"User {user_id} performed {action}")

# Usage
log_debug("Starting application")
write_info("Processing data")
emit_warning("Low disk space")
log_user_action(123, "login")

# ✅ Fixed - Direct logging calls
import structlog
log = structlog.get_logger()

# Usage
log.debug("application-starting")
log.info("data-processing", status="started")
log.warning("disk-space-low", available_gb=2.1)
log.info("user-action", user_id=123, action="login")
```

**Why wrapper functions are problematic:**

1. **Hidden source location**: Stack traces and debugging tools show the wrapper function, not the actual call site
2. **Reduced flexibility**: Wrapper functions often limit the structured data you can pass
3. **Maintenance overhead**: Extra functions to maintain and test
4. **Inconsistent patterns**: Different developers create different wrapper styles
5. **Lost context**: The wrapper function becomes a bottleneck that loses calling context

**Common wrapper patterns detected:**
- Functions with names containing "log", "write_", "emit_", "debug_", "info_", "warn_", "error_"
- Functions that only call logging methods internally
- Utility functions that format and log messages

**Migration strategy:**
1. Replace wrapper function calls with direct `log.*` calls
2. Convert string formatting to structured keyword arguments
3. Use proper event IDs instead of dynamic messages
4. Remove the wrapper functions entirely

## Magic Arguments

The analyzer recognizes these special "magic" arguments that don't count toward the keyword argument limit:

- `_replace_msg` - Custom message replacement
- `exc_info` - Exception information
- `_structured` - Structured data flag
- `_level` - Dynamic level setting
- `_name` - Logger name override

```python
# These magic args don't trigger "too_many_kwargs"
log.info("operation-failed", 
         user_id=123, 
         operation="payment",
         exc_info=True,        # Magic arg
         _replace_msg="Custom message")  # Magic arg
```

## Usage

### Command Line Analysis

```bash
# Analyze a single file
nicestlog check my_file.py

# Analyze a directory
nicestlog check src/

# Generate detailed analysis with complexity
nicestlog check src/ --complexity --verbose

# Check specific patterns
nicestlog check src/ --pattern specific_pattern
```

### Programmatic Analysis

```python
from nicestlog.log_statement_analyzer import LogStatementAnalyzer

analyzer = LogStatementAnalyzer()

# Analyze a file
results = analyzer.analyze_file("my_module.py")

for issue in results.issues:
    print(f"{issue.type}: {issue.message} at line {issue.line}")

# Analyze code string
code = '''
log.info(f"User {user_id} logged in")
log.debug("critical-system-failure")
'''

results = analyzer.analyze_code(code)
print(f"Found {len(results.issues)} issues")
```

### Custom Configuration

```python
# Configure issue detection
analyzer = LogStatementAnalyzer(
    max_kwargs=5,                    # Lower threshold
    event_id_max_length=30,          # Shorter event IDs
    enforce_dash_case=True,          # Strict dash-case
    detect_pii=True,                 # Enable PII detection
    sensitive_keywords=["custom_secret"]  # Custom sensitive words
)
```

## Integration with IDEs

### VS Code

The nicestlog VS Code extension provides real-time issue detection:

```json
{
    "nicestlog.enableAnalysis": true,
    "nicestlog.showInlineWarnings": true,
    "nicestlog.analysisOnSave": true
}
```

### PyCharm

Install the nicestlog PyCharm plugin for:
- Real-time code inspection
- Quick-fix suggestions
- Issue highlighting
- Batch analysis

## Metrics and Reporting

### Analysis Metrics

The analyzer tracks various metrics:

```python
results = analyzer.analyze_directory("src/")

print(f"Files analyzed: {results.metrics.files_analyzed}")
print(f"Log statements: {results.metrics.log_statements_found}")
print(f"Issues found: {results.metrics.total_issues}")
print(f"Dash-case violations: {results.metrics.dash_case_violations}")
print(f"Single string args: {results.metrics.single_string_args}")
print(f"Magic args usage: {results.metrics.magic_args_usage}")
```

### Report Formats

Generate reports in various formats:

```bash
# Basic analysis
nicestlog check src/ --verbose

# Complexity analysis
nicestlog check src/ --complexity

# Pattern-specific analysis
nicestlog check src/ --pattern specific_pattern

# Interactive analysis
nicestlog check src/ --interactive
```

### Sample JSON Report

```json
{
    "summary": {
        "files_analyzed": 25,
        "total_issues": 42,
        "issue_types": {
            "missing_event_id": 8,
            "single_string_argument": 12,
            "event_id_not_dash_case": 6,
            "potential_secret_leak": 2,
            "too_many_kwargs": 3
        }
    },
    "files": [
        {
            "path": "src/user_service.py",
            "issues": [
                {
                    "type": "missing_event_id",
                    "line": 45,
                    "message": "Log call missing event ID",
                    "code": "log.info(user_id=123)"
                }
            ]
        }
    ]
}
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
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install nicestlog
        run: pip install nicestlog
      - name: Analyze logs
        run: |
          nicestlog check src/ --complexity --verbose
          # Use exit code to fail on issues
          nicestlog check src/ --pattern critical_issues
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: nicestlog-analysis
        name: nicestlog log analysis
        entry: nicestlog check
        language: system
        files: \.py$
        args: [--fail-on, error]
```

## Custom Rules

### Creating Custom Analyzers

```python
from nicestlog.log_statement_analyzer import BaseAnalyzer, Issue

class CustomAnalyzer(BaseAnalyzer):
    def analyze_log_call(self, node, context):
        issues = []
        
        # Custom analysis logic
        if self.has_custom_issue(node):
            issues.append(Issue(
                type="custom_issue",
                message="Custom issue detected",
                line=node.lineno,
                severity="warning"
            ))
        
        return issues

# Use custom analyzer
analyzer = LogStatementAnalyzer(custom_analyzers=[CustomAnalyzer()])
```

### Rule Configuration

```toml
# .nicestlog.toml
[analyzer]
max_kwargs = 7
event_id_max_length = 50
enforce_dash_case = true
detect_pii = true

[analyzer.rules]
# Enable/disable specific rules
missing_event_id = true
single_string_argument = true
too_many_kwargs = true
potential_secret_leak = true

[analyzer.sensitive_keywords]
# Custom sensitive keywords
custom = ["internal_token", "private_data"]
```

## Best Practices

### 1. Regular Analysis

Run analysis regularly as part of your development workflow:

```bash
# Daily analysis
nicestlog check src/ --verbose

# Pre-commit analysis
nicestlog check .
```

### 2. Gradual Improvement

Fix issues incrementally:

```bash
# Fix high-priority issues first
nicestlog check src/ --fix --pattern critical_issues

# Then address warnings
nicestlog check src/ --fix --verbose
```

### 3. Team Standards

Establish team-wide logging standards:

```toml
# Team configuration
[analyzer]
max_kwargs = 5              # Stricter limit
event_id_max_length = 40    # Shorter IDs
enforce_dash_case = true    # Consistent naming
detect_pii = true          # Security focus
```

## Troubleshooting

### False Positives

Configure the analyzer to reduce false positives:

```python
# Whitelist certain patterns
analyzer = LogStatementAnalyzer(
    whitelist_patterns=[
        r"test_.*",           # Test functions
        r"debug_.*",          # Debug functions
    ],
    ignore_files=["tests/", "migrations/"]
)
```

### Performance Issues

For large codebases:

```python
# Enable parallel processing
analyzer = LogStatementAnalyzer(
    parallel=True,
    max_workers=4,
    cache_results=True
)
```

The Log Statement Analyzer helps you maintain consistent, high-quality logging practices across your entire codebase! 🔍✨