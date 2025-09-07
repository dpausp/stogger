# Nicestlog Logging Conventions (structlog)

This project uses [nicestlog](https://github.com/your-repo/nicestlog) for structured logging analysis and improvement, including line-based user messages and diagnostics.

## Core Principles

1. Use dash-case event names
2. Add structured keyword arguments
3. Choose appropriate log levels
4. Use `log.exception()` for errors
5. For CLI, use `log.info()` for user-oriented line-based output
6. Run `nicestlog check` regularly or as part of a CI pipeline

### 1. Event-Style Logging with Dash-Case
Use descriptive event names in **dash-case**:

```python
log.debug("user-login-attempt", user_id=123, ip="192.168.1.1")
log.info("welcome-new-user", _replace_msg="Welcome {username}!", username=user.name)
log.error("package-validation-failed", package_name="hello", reason="invalid_version")
```

### 2. Structured Data with Keyword Arguments
Always use keyword arguments for context:

```python
log.debug("package-processing-completed",
         package_name="hello",
         version="2.10.0",
         processing_time_ms=150,
         files_processed=42)
```

### 3. Log Levels

| Level | When to Use | User Output |
|-------|-------------|-------------|
| `DEBUG` | Diagnostic info for developers | **NEVER** use `_replace_msg` |
| `INFO` | Important business events | **SHOULD** use `_replace_msg` for user-oriented output |
| `WARNING` | Expected problems | Use `_replace_msg` for user warnings |
| `ERROR` | Error conditions | Use `_replace_msg` for user errors |
| `CRITICAL` | Severe errors requiring attention | Use `_replace_msg` for critical user messages |

### 4. Exception Handling
Use `log.exception()` in except blocks. This is equivalent to `log.error()` with `exc_info=True` and automatically includes the stack trace. It's not a separate log level.

```python
try:
    process_package(package_data)
except ValidationError as e:
    log.exception("package-validation-failed",
                  package_name=package_data.get("name"))
    raise
```

### 5. User Output Integration

**nicestlog fuses user output with logging** - use `log.info()` instead of `print()` or `typer.echo()` for line-oriented user output. This creates a "protocol" of what was shown to the user:

```python
# User output via logging with placeholders
log.info("package-installed",
         _replace_msg="Successfully installed {package_name} v{version} ({size_mb:.1f} MB)",
         package_name="hello",
         version="2.10.0",
         size_mb=15.7)
```

Typically, you would configure nicestlog/structlog to show clean user messages while capturing structured data for analysis.

**Benefits:**
- Single source of truth for both user communication and diagnostics
- Structured data available for analysis while showing clean messages to users
- Consistent formatting and filtering capabilities
- Audit trail of user interactions

## Best Practices

### Function Tracing Pattern
```python
def process_package(package_name: str):
    log.info("package-processing-started", package_name=package_name)

    try:
        result = perform_processing(package_name)
        log.info("package-processing-completed",
                package_name=package_name,
                result_size=len(result))
        return result
    except Exception as e:
        log.exception("package-processing-failed", package_name=package_name)
        raise
```

### Timing Operations
```python
import time

def timed_operation():
    start = time.time()
    log.info("operation-started", operation="data_sync")

    result = perform_operation()

    duration = time.time() - start
    log.info("operation-completed",
            operation="data_sync",
            duration_ms=round(duration * 1000))

    return result
```

## Example Configuration

### pyproject.toml
```toml
[tool.nicestlog]
verbose = true
source_dirs = ["src"]
test_dirs = ["tests"]
exclude_patterns = [
    "docs/**",
    ".venv/**",
    "build/**",
    "dist/**"
]
```

## Integration with nicestlog Tools

### Code Quality Checking
Run `nicestlog check` to validate logging practices:

```bash
# Check current directory
nicestlog check .

# Fix issues automatically
nicestlog check . --fix

# Interactive fixing
nicestlog check . --interactive
```

### Migration from Legacy Logging
For existing projects with print statements or standard logging:

```bash
# Analyze migration opportunities
nicestlog migrate .

# Apply migration with backup
nicestlog migrate . --do-migrate --backup
```

## Common Patterns

### CLI Command Logging
```python
def deploy_command(package_name: str, environment: str):
    log.info("deployment-started", 
             _replace_msg="🚀 Deploying {package} to {env}...",
             package=package_name, 
             env=environment)
    
    try:
        result = deploy_package(package_name, environment)
        log.info("deployment-completed",
                 _replace_msg="✅ Successfully deployed {package} to {env}",
                 package=package_name,
                 env=environment,
                 deployment_id=result.id)
    except DeploymentError as e:
        log.exception("deployment-failed",
                      _replace_msg="❌ Failed to deploy {package}: {error}",
                      package=package_name,
                      error=str(e))
        raise
```

### Progress Reporting
```python
def process_files(file_list: List[str]):
    total = len(file_list)
    log.info("batch-processing-started",
             _replace_msg="Processing {total} files...",
             total=total)
    
    for i, file_path in enumerate(file_list, 1):
        log.debug("file-processing-started", file_path=file_path, index=i)
        
        process_file(file_path)
        
        if i % 10 == 0 or i == total:
            log.info("batch-progress-update",
                     _replace_msg="Processed {current}/{total} files",
                     current=i,
                     total=total,
                     progress_percent=round(i/total*100))
    
    log.info("batch-processing-completed",
             _replace_msg="✅ All {total} files processed successfully",
             total=total)
```

### Error Context
```python
def validate_config(config_path: Path):
    log.debug("config-validation-started", config_path=str(config_path))
    
    if not config_path.exists():
        log.error("config-file-missing",
                  _replace_msg="Configuration file not found: {path}",
                  config_path=str(config_path))
        raise FileNotFoundError(f"Config file missing: {config_path}")
    
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        log.exception("config-parse-failed",
                      _replace_msg="Invalid YAML in config file: {error}",
                      config_path=str(config_path),
                      error=str(e))
        raise
    
    log.info("config-validation-completed",
             _replace_msg="✅ Configuration validated successfully",
             config_path=str(config_path),
             config_keys=list(config.keys()))
    
    return config
```