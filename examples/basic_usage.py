#!/usr/bin/env python3
"""
Basic usage examples for nicestlog.

This script demonstrates various logging patterns and best practices
using the nicestlog library.
"""

import sys
import time
import subprocess
from pathlib import Path
import structlog

# Import our logging library
import nicestlog


def demonstrate_basic_logging():
    """Demonstrate basic console logging setup and usage."""
    print("=== Basic Console Logging ===")
    
    # Setup basic console logging
    log = nicestlog.setup_basic_logging(verbose=True, app_name="demo")
    
    # Basic logging examples
    log.info("Application started", version="1.0.0")
    log.debug("Debug information", component="main")
    log.warning("This is a warning", threshold=80, current=85)
    log.error("An error occurred", error_code=404)
    
    # Structured logging with template messages
    log.info(
        "user-login",
        _replace_msg="User {username} logged in from {ip}",
        username="alice",
        user_id=123,
        ip="192.168.1.1",
        session_id="abc-def-123"
    )


def demonstrate_file_logging():
    """Demonstrate file + console logging."""
    print("\n=== File + Console Logging ===")
    
    # Create temporary log directory
    log_dir = Path("/tmp/nicestlog_demo")
    log_dir.mkdir(exist_ok=True)
    
    # Setup file logging
    log = nicestlog.setup_file_logging(
        logdir=log_dir,
        verbose=True,
        app_name="demo",
        log_cmd_output=True
    )
    
    log.info("File logging initialized", log_directory=str(log_dir))
    
    # Demonstrate command output logging
    try:
        result = subprocess.run(
            ["echo", "Hello from subprocess!"],
            capture_output=True,
            text=True,
            check=True
        )
        
        log.info(
            "command-executed",
            command=["echo", "Hello from subprocess!"],
            exit_code=result.returncode,
            stdout_length=len(result.stdout)
        )
        
        # Log command output (goes to separate file if enabled)
        log.debug("command-output", output=result.stdout.strip())
        
    except subprocess.CalledProcessError as e:
        log.error("command-failed", error=str(e), exit_code=e.returncode)
    
    print(f"Logs written to: {log_dir}")
    print("Files created:")
    for log_file in log_dir.glob("*.log"):
        print(f"  - {log_file.name}")


def demonstrate_bound_loggers():
    """Demonstrate using bound loggers for context."""
    print("\n=== Bound Loggers (Context) ===")
    
    log = nicestlog.setup_basic_logging(verbose=True, app_name="demo")
    
    # Create a request-scoped logger
    request_log = log.bind(
        request_id="req-12345",
        user_id=456,
        endpoint="/api/users"
    )
    
    request_log.info("request-started", method="POST")
    request_log.debug("validating-input", fields=["username", "email"])
    request_log.info("user-created", new_user_id=789)
    request_log.info("request-completed", status_code=201, duration_ms=150)


def demonstrate_error_handling():
    """Demonstrate proper error logging."""
    print("\n=== Error Handling ===")
    
    log = nicestlog.setup_basic_logging(verbose=True, app_name="demo")
    
    def risky_operation():
        raise ValueError("Something went wrong!")
    
    try:
        risky_operation()
    except ValueError as e:
        log.error(
            "operation-failed",
            _replace_msg="Operation failed: {error}",
            operation="risky_operation",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True  # Include full traceback
        )
    
    # Demonstrate recovery logging
    def get_data_with_fallback():
        try:
            # Simulate a failing operation
            raise ConnectionError("Database unavailable")
        except ConnectionError as e:
            log.warning(
                "fallback-used",
                _replace_msg="Using cached data due to error: {error}",
                error=str(e),
                fallback_type="cache"
            )
            return {"cached": True, "data": "fallback_value"}
    
    result = get_data_with_fallback()
    log.info("operation-completed", result_type="fallback", cached=result.get("cached"))


def demonstrate_performance_patterns():
    """Demonstrate performance-conscious logging patterns."""
    print("\n=== Performance Patterns ===")
    
    log = nicestlog.setup_basic_logging(verbose=True, app_name="demo")
    
    # Lazy evaluation for expensive operations
    def expensive_debug_data():
        time.sleep(0.1)  # Simulate expensive operation
        return {"expensive": "data", "computed_at": time.time()}
    
    # This only calls expensive_debug_data() if debug logging is enabled
    log.debug("expensive-debug", data=lambda: expensive_debug_data())
    
    # Batch logging instead of logging every iteration
    items = list(range(100))
    batch_size = 25
    
    log.info("batch-processing-started", total_items=len(items), batch_size=batch_size)
    
    for i, item in enumerate(items):
        # Only log every batch_size items
        if i % batch_size == 0:
            log.debug("processing-batch", batch_start=i, items_remaining=len(items) - i)
        
        # Simulate processing
        time.sleep(0.001)
    
    log.info("batch-processing-completed", total_items=len(items))


def demonstrate_different_log_levels():
    """Demonstrate when to use different log levels."""
    print("\n=== Log Levels ===")
    
    log = nicestlog.setup_basic_logging(verbose=True, app_name="demo")
    
    # TRACE - Very detailed debugging (using debug since trace is not standard)
    log.debug("function-entry", function="process_data", args={"id": 123})
    
    # DEBUG - Detailed debugging information
    log.debug("cache-lookup", key="user:123", hit=True, ttl=300)
    
    # INFO - General information (default production level)
    log.info("user-action", action="create_post", user_id=123, post_id=456)
    
    # WARNING - Potentially harmful situations
    log.warning("rate-limit-approaching", current_requests=95, limit=100)
    
    # ERROR - Error events that don't stop the application
    log.error("external-service-failed", service="payment_api", retry_count=3)
    
    # CRITICAL - Very serious errors that might cause program abort
    log.critical("database-connection-lost", attempts=5, max_attempts=5)


def main():
    """Run all demonstration functions."""
    print("Nicestlog Usage Examples")
    print("=" * 50)
    
    try:
        demonstrate_basic_logging()
        demonstrate_file_logging()
        demonstrate_bound_loggers()
        demonstrate_error_handling()
        demonstrate_performance_patterns()
        demonstrate_different_log_levels()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        
    except Exception as e:
        # Even our demo can have proper error logging!
        log = structlog.get_logger()
        log.critical(
            "demo-failed",
            _replace_msg="Demo script failed: {error}",
            error=str(e),
            exc_info=True
        )
        sys.exit(1)


if __name__ == "__main__":
    main()