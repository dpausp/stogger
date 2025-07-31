# Nicestlog Best Practices

## Overview

Nicestlog uses a sophisticated structured logging system built on top of `structlog` that provides multi-target logging with different renderers for console output, systemd journal, and file logging. This document outlines best practices for using this logging system effectively.

## Table of Contents

1. [Basic Setup and Initialization](#basic-setup-and-initialization)
2. [Logger Creation and Usage](#logger-creation-and-usage)
3. [Log Levels and When to Use Them](#log-levels-and-when-to-use-them)
4. [Structured Logging Patterns](#structured-logging-patterns)
5. [Message Formatting](#message-formatting)
6. [Command Output Logging](#command-output-logging)
7. [Error Handling and Exception Logging](#error-handling-and-exception-logging)
8. [Performance Considerations](#performance-considerations)
9. [Testing Logging](#testing-logging)
10. [Common Patterns and Examples](#common-patterns-and-examples)

## Basic Setup and Initialization

### Initialize Logging Early

Always initialize logging at the start of your application:

```python
import nicestlog
import structlog

# Initialize logging with appropriate settings
nicestlog.init_logging(
    verbose=verbose,
    logdir=logdir,
    log_cmd_output=True,  # For command-heavy operations
    log_to_console=True,
    syslog_identifier="your-component",
    show_caller_info=False  # Enable for debugging
)

# Get logger instance
log = structlog.get_logger()
```

### Configuration Parameters

- **verbose**: Controls console log level (trace vs info)
- **logdir**: Directory for file logging (required for command output logging)
- **log_cmd_output**: Enable separate command output logging
- **log_to_console**: Enable console output (auto-disabled in systemd context)
- **syslog_identifier**: Identifier for journal entries
- **show_caller_info**: Add caller information to logs (useful for debugging)

### Environment Detection

The logging system automatically detects the runtime environment:

```python
# Automatically detects systemd environment
# Disables console output when running under systemd
# Enables journal logging when systemd-python is available
```

## Logger Creation and Usage

### Get Logger Instances

```python
import structlog

# Get the root logger
log = structlog.get_logger()

# Get a component-specific logger
log = structlog.get_logger("component_name")

# Bind context to create a specialized logger
user_log = log.bind(user_id=123, session="abc-def")
```

### Basic Logging

```python
# Simple message
log.info("User logged in")

# With structured data
log.info("User logged in", user_id=123, ip="192.168.1.1")

# With template message
log.info(
    "user-login",
    _replace_msg="User {username} logged in from {ip}",
    username="alice",
    ip="192.168.1.1"
)
```

## Log Levels and When to Use Them

### TRACE
Use for very detailed debugging information, typically only of interest when diagnosing problems.

```python
log.trace("Entering function", function="process_data", args=args)
log.trace("Variable state", var_name="counter", value=counter)
```

### DEBUG
Use for detailed information, typically only of interest when diagnosing problems.

```python
log.debug("Processing item", item_id=item.id, status=item.status)
log.debug("Cache hit", key="user:123", ttl=300)
```

### INFO
Use for general information about program execution. This is the default level for production.

```python
log.info("Application started", version="1.2.3", port=8080)
log.info("User action", action="create_post", user_id=123)
```

### WARNING
Use for potentially harmful situations that don't prevent the program from continuing.

```python
log.warning("Deprecated API used", endpoint="/old/api", user_id=123)
log.warning("High memory usage", usage_percent=85, threshold=80)
```

### ERROR
Use for error events that might still allow the application to continue running.

```python
log.error("Failed to process item", item_id=123, error=str(e))
log.error("Database connection failed", attempt=3, max_attempts=5)
```

### CRITICAL
Use for very serious error events that might cause the program to abort.

```python
log.critical("Database unavailable", error=str(e))
log.critical("Out of disk space", available_mb=0)
```

## Structured Logging Patterns

### Structure Your Data

Always include relevant context in your log entries:

```python
# Good - includes relevant context
log.info(
    "order-processed",
    order_id=order.id,
    customer_id=order.customer_id,
    amount=order.total,
    processing_time_ms=elapsed_ms
)

# Avoid - lacks context
log.info("Order processed")
```

### Use Consistent Field Names

Establish conventions for field names across your application:

```python
# Consistent naming
log.info("request-started", request_id=req_id, method="POST", path="/api/users")
log.info("request-completed", request_id=req_id, status_code=201, duration_ms=150)

# Use snake_case for field names
log.info("user-created", user_id=123, email_address="user@example.com")
```

### Hierarchical Context

Use bound loggers to maintain context throughout request processing:

```python
def handle_request(request):
    # Create request-scoped logger
    req_log = log.bind(
        request_id=request.id,
        user_id=request.user.id,
        method=request.method,
        path=request.path
    )
    
    req_log.info("request-started")
    
    try:
        result = process_request(request, req_log)
        req_log.info("request-completed", status="success")
        return result
    except Exception as e:
        req_log.error("request-failed", error=str(e), exc_info=True)
        raise

def process_request(request, log):
    # Logger already has request context
    log.debug("validating-input")
    # ... processing ...
    log.debug("input-validated", valid=True)
```

## Message Formatting

### Template Messages

Use `_replace_msg` for human-readable messages while maintaining structured data:

```python
log.info(
    "user-login-success",
    _replace_msg="User {username} successfully logged in from {ip_address}",
    username=user.username,
    user_id=user.id,
    ip_address=request.remote_addr,
    session_id=session.id
)
```

### Event-Style Messages

Use kebab-case event names as the primary message:

```python
# Good - clear event names
log.info("database-connection-established", host="db.example.com", port=5432)
log.info("cache-miss", key="user:123", cache_type="redis")
log.info("email-sent", recipient="user@example.com", template="welcome")

# Avoid - unclear or inconsistent naming
log.info("DB connected")
log.info("cache miss for user:123")
```

### Message Guidelines

1. **Primary message should be machine-readable** (kebab-case event names)
2. **Use `_replace_msg` for human-readable versions**
3. **Include relevant structured data as separate fields**
4. **Be consistent with naming conventions**

## Command Output Logging

### Enable Command Output Logging

```python
# Initialize with command output logging
nicestlog.init_logging(
    logdir=Path("/var/log/myapp"),
    log_cmd_output=True,  # Enables separate command output file
    verbose=True
)
```

### Log Command Execution

```python
import subprocess

def run_command(cmd, log):
    log.info("command-starting", command=cmd)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        log.info(
            "command-completed",
            command=cmd,
            exit_code=result.returncode,
            stdout_lines=len(result.stdout.splitlines()),
            stderr_lines=len(result.stderr.splitlines())
        )
        
        # Log command output to separate file
        if result.stdout:
            log.trace("command-stdout", command=cmd, output=result.stdout)
        if result.stderr:
            log.trace("command-stderr", command=cmd, output=result.stderr)
            
        return result
        
    except subprocess.CalledProcessError as e:
        log.error(
            "command-failed",
            command=cmd,
            exit_code=e.returncode,
            error=str(e),
            stdout=e.stdout,
            stderr=e.stderr
        )
        raise
```

## Error Handling and Exception Logging

### Exception Logging

Always include exception information when logging errors:

```python
try:
    risky_operation()
except Exception as e:
    log.error(
        "operation-failed",
        operation="risky_operation",
        error=str(e),
        error_type=type(e).__name__,
        exc_info=True  # Includes full traceback
    )
    raise  # Re-raise if appropriate
```

### Structured Error Information

```python
try:
    process_user_data(user_id, data)
except ValidationError as e:
    log.error(
        "validation-failed",
        _replace_msg="Validation failed for user {user_id}: {error}",
        user_id=user_id,
        error=str(e),
        validation_errors=e.errors if hasattr(e, 'errors') else None,
        data_keys=list(data.keys()) if data else None
    )
except DatabaseError as e:
    log.error(
        "database-error",
        _replace_msg="Database operation failed for user {user_id}",
        user_id=user_id,
        error=str(e),
        operation="process_user_data",
        exc_info=True
    )
```

### Recovery Logging

Log recovery actions and fallback behavior:

```python
def get_user_preferences(user_id):
    try:
        return database.get_user_preferences(user_id)
    except DatabaseError as e:
        log.warning(
            "preferences-fallback",
            _replace_msg="Using default preferences for user {user_id} due to database error",
            user_id=user_id,
            error=str(e),
            fallback="default_preferences"
        )
        return get_default_preferences()
```

## Performance Considerations

### Lazy Evaluation

Structure your logging to avoid expensive operations when not needed:

```python
# Good - only evaluates expensive_operation() if debug logging is enabled
log.debug("debug-info", expensive_data=lambda: expensive_operation())

# Avoid - always evaluates expensive operation
log.debug("debug-info", expensive_data=expensive_operation())
```

### Avoid Logging in Tight Loops

```python
# Avoid - logs every iteration
for item in large_list:
    log.debug("processing-item", item_id=item.id)
    process_item(item)

# Better - log batches or summary
batch_size = 100
for i, item in enumerate(large_list):
    if i % batch_size == 0:
        log.debug("processing-batch", batch_start=i, total_items=len(large_list))
    process_item(item)

log.info("processing-completed", total_items=len(large_list))
```

### Conditional Logging

```python
# Use log level checks for expensive operations
if log.isEnabledFor(logging.DEBUG):
    log.debug("expensive-debug-info", data=generate_expensive_debug_data())
```

## Testing Logging

### Capture Logs in Tests

```python
import pytest
import structlog
from structlog.testing import LogCapture

def test_user_creation():
    cap = LogCapture()
    structlog.configure(processors=[cap])
    
    # Your code that logs
    create_user("testuser")
    
    # Assert log entries
    assert len(cap.entries) == 1
    assert cap.entries[0]["event"] == "user-created"
    assert cap.entries[0]["username"] == "testuser"
```

### Mock External Dependencies

```python
def test_command_execution(mocker):
    # Mock subprocess to avoid actual command execution
    mock_run = mocker.patch('subprocess.run')
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "success"
    
    # Test your logging
    result = run_command_with_logging(["echo", "test"])
    
    # Verify logging behavior
    # ... assertions ...
```

## Common Patterns and Examples

### Application Startup

```python
def main():
    # Initialize logging first
    nicestlog.init_logging(
        verbose=args.verbose,
        logdir=args.logdir,
        syslog_identifier="myapp"
    )
    
    log = structlog.get_logger()
    
    log.info(
        "application-starting",
        _replace_msg="Starting {app_name} version {version}",
        app_name="myapp",
        version=__version__,
        python_version=sys.version,
        args=vars(args)
    )
    
    try:
        app = create_app(args)
        log.info("application-ready", port=args.port)
        app.run()
    except Exception as e:
        log.critical("application-startup-failed", error=str(e), exc_info=True)
        sys.exit(1)
```

### Request Processing

```python
@app.route('/api/users', methods=['POST'])
def create_user():
    req_log = log.bind(
        request_id=str(uuid.uuid4()),
        endpoint="create_user",
        method="POST"
    )
    
    req_log.info("request-started")
    
    try:
        data = request.get_json()
        req_log.debug("request-data", data_keys=list(data.keys()))
        
        user = User.create(data)
        req_log.info(
            "user-created",
            _replace_msg="Created user {username} with ID {user_id}",
            user_id=user.id,
            username=user.username
        )
        
        return jsonify(user.to_dict()), 201
        
    except ValidationError as e:
        req_log.warning("validation-failed", errors=e.errors)
        return jsonify({"error": "Validation failed"}), 400
        
    except Exception as e:
        req_log.error("request-failed", error=str(e), exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
```

### Background Tasks

```python
def process_queue():
    task_log = log.bind(worker_id=worker_id, queue="main")
    
    task_log.info("worker-started")
    
    while True:
        try:
            task = queue.get(timeout=30)
            if task is None:
                continue
                
            task_log = task_log.bind(task_id=task.id, task_type=task.type)
            task_log.info("task-started")
            
            start_time = time.time()
            result = process_task(task, task_log)
            duration = time.time() - start_time
            
            task_log.info(
                "task-completed",
                duration_seconds=duration,
                result_size=len(str(result)) if result else 0
            )
            
        except queue.Empty:
            task_log.trace("queue-empty")
            continue
        except Exception as e:
            task_log.error("task-failed", error=str(e), exc_info=True)
```

### Service Management

```python
class ServiceManager:
    def __init__(self):
        self.log = structlog.get_logger("service_manager")
        
    def start_service(self, service_name):
        svc_log = self.log.bind(service=service_name)
        
        svc_log.info("service-starting")
        
        try:
            service = self.services[service_name]
            service.start()
            
            svc_log.info(
                "service-started",
                _replace_msg="Service {service} started successfully",
                pid=service.pid,
                port=getattr(service, 'port', None)
            )
            
        except Exception as e:
            svc_log.error(
                "service-start-failed",
                _replace_msg="Failed to start service {service}: {error}",
                error=str(e),
                exc_info=True
            )
            raise
```

## Best Practices Summary

1. **Initialize logging early** in your application lifecycle
2. **Use structured data** consistently throughout your application
3. **Employ bound loggers** to maintain context across function calls
4. **Choose appropriate log levels** based on the importance and frequency of events
5. **Include relevant context** in every log entry
6. **Use template messages** for human-readable output while maintaining structure
7. **Handle exceptions properly** with full context and stack traces
8. **Avoid performance pitfalls** like logging in tight loops
9. **Test your logging** to ensure it provides value
10. **Be consistent** with naming conventions and patterns

Remember that logging is not just for debugging - it's a crucial part of system observability and operational intelligence. Good logging practices will make your systems easier to monitor, debug, and maintain.