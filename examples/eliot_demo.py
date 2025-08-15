#!/usr/bin/env python3
"""
Demo: Beautiful Eliot action tracing with nicestlog

This shows how to use Eliot for request tracing with human-readable output
instead of ugly JSON logs.
"""

import time
import random
from nicestlog import setup_eliot_logging, log_action, log_call
from eliot import log_message


def simulate_api_request():
    """Simulate a complete API request with nested actions."""

    # Setup beautiful Eliot logging
    setup_eliot_logging(human_readable=True, show_timestamps=True)

    print("🚀 Starting API request simulation with beautiful Eliot tracing...")
    print("=" * 70)

    with log_action(
        "api_request", method="POST", endpoint="/api/users", user_agent="demo/1.0"
    ):
        log_message(message_type="request_started", request_id="req-12345")

        # Authentication step
        with log_action("authenticate", token_type="bearer"):
            time.sleep(0.1)  # Simulate auth delay
            log_message(
                message_type="token_validated",
                user_id=42,
                permissions=["read", "write"],
            )

        # Database operations
        with log_action("database_operations"):
            # User lookup
            with log_action("user_lookup", user_id=42):
                time.sleep(0.05)
                log_message(
                    message_type="query_executed",
                    sql="SELECT * FROM users WHERE id = ?",
                    execution_time_ms=23,
                )

            # Update user data
            with log_action("user_update", fields=["email", "last_login"]):
                time.sleep(0.08)
                log_message(
                    message_type="update_executed",
                    rows_affected=1,
                    execution_time_ms=45,
                )

        # Cache operations
        with log_action("cache_operations"):
            cache_key = "user:42:profile"

            with log_action("cache_invalidate", key=cache_key):
                log_message(message_type="cache_deleted", ttl_remaining=120)

            with log_action("cache_warm", key=cache_key):
                log_message(message_type="cache_populated", size_bytes=1024, ttl=3600)

        # Response preparation
        response_time = random.randint(50, 200)
        log_message(
            message_type="response_prepared",
            status_code=200,
            response_size=2048,
            total_time_ms=response_time,
        )

    print("\n✨ Request completed! Notice the beautiful nested structure!")


@log_call("expensive_calculation")
def calculate_fibonacci(n: int) -> int:
    """Example of using the @log_call decorator."""
    if n <= 1:
        return n

    log_message(message_type="recursive_call", n=n)
    return calculate_fibonacci(n - 1) + calculate_fibonacci(n - 2)


def demonstrate_error_handling():
    """Show how errors are beautifully displayed."""
    print("\n🔥 Demonstrating error handling...")
    print("=" * 70)

    try:
        with log_action("risky_operation", operation="divide_by_zero"):
            log_message(message_type="attempting_calculation", x=10, y=0)
            result = 10 / 0  # This will fail
            log_message(message_type="calculation_result", result=result)
    except ZeroDivisionError as e:
        log_message(message_type="error_handled", error=str(e))

    print("\n💥 Error was beautifully logged!")


if __name__ == "__main__":
    # Main demo
    simulate_api_request()

    print("\n" + "=" * 70)
    print("🧮 Function decorator demo:")
    print("=" * 70)

    # Decorator demo
    setup_eliot_logging(human_readable=True, show_timestamps=True)
    result = calculate_fibonacci(5)
    print(f"\nFibonacci(5) = {result}")

    # Error handling demo
    demonstrate_error_handling()

    print("\n🎉 Demo complete! Much better than ugly JSON logs, right?")
    print("💡 Try running with: python examples/eliot_demo.py")
