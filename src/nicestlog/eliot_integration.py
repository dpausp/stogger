"""
Eliot integration for nicestlog - Beautiful human-readable action tracing.

Combines Eliot's powerful action tracking with nicestlog's beautiful output.
"""

import sys
from typing import Any, Dict, Optional, TextIO
from datetime import datetime

try:
    from eliot import start_action, Action, log_message
    from eliot._output import FileDestination
    from eliot._message import WrittenMessage

    ELIOT_AVAILABLE = True
except ImportError:
    ELIOT_AVAILABLE = False
    start_action = Action = log_message = FileDestination = WrittenMessage = None

try:
    from .core import RESET_ALL, BRIGHT, DIM, RED, BLUE, CYAN, MAGENTA, YELLOW, GREEN
except ImportError:
    # When running as standalone script
    import sys

    if sys.stdout.isatty():
        try:
            import colorama

            colorama.init()
            RESET_ALL = colorama.Style.RESET_ALL
            BRIGHT = colorama.Style.BRIGHT
            DIM = colorama.Style.DIM
            RED = colorama.Fore.RED
            BLUE = colorama.Fore.BLUE
            CYAN = colorama.Fore.CYAN
            MAGENTA = colorama.Fore.MAGENTA
            YELLOW = colorama.Fore.YELLOW
            GREEN = colorama.Fore.GREEN
        except ImportError:
            RESET_ALL = BRIGHT = DIM = RED = BLUE = CYAN = MAGENTA = YELLOW = GREEN = ""
    else:
        RESET_ALL = BRIGHT = DIM = RED = BLUE = CYAN = MAGENTA = YELLOW = GREEN = ""


class HumanReadableEliotDestination:
    """
    Eliot destination that outputs beautiful, human-readable action traces.

    Instead of ugly JSON, this creates beautiful nested action logs that
    show the flow of your application with proper indentation and colors.
    """

    def __init__(
        self,
        file: Optional[TextIO] = None,
        show_timestamps: bool = True,
        show_task_ids: bool = False,
        max_width: int = 120,
    ):
        self.file = file or sys.stdout
        self.show_timestamps = show_timestamps
        self.show_task_ids = show_task_ids
        self.max_width = max_width
        self._action_stack: Dict[str, int] = {}  # task_id -> depth
        self._action_names: Dict[str, str] = {}  # task_id -> action name

    def __call__(self, message: Dict[str, Any]):
        """Process an Eliot message and output human-readable format."""
        if not isinstance(message, dict):
            return

        # Modern Eliot uses different message structure
        action_type = message.get("action_type")
        action_status = message.get("action_status")
        task_uuid = message.get("task_uuid", "")

        if action_type and action_status == "started":
            self._handle_action_start(message, task_uuid)
        elif action_type and action_status == "succeeded":
            self._handle_action_result(message, task_uuid)
        elif action_type and action_status == "failed":
            self._handle_action_failure(message, task_uuid)
        else:
            self._handle_regular_message(message, task_uuid)

    def _handle_action_start(self, message: Dict[str, Any], task_id: str):
        """Handle the start of an action."""
        action_type = message.get("action_type", "unknown")
        self._action_names[task_id] = action_type

        # Determine nesting depth from task_level
        task_level = message.get("task_level", [])
        depth = len(task_level) if task_level else 0
        self._action_stack[task_id] = depth

        # Format the action start
        indent = "  " * depth
        timestamp = self._format_timestamp(message.get("timestamp"))

        # Extract action parameters (exclude system fields)
        system_fields = {
            "action_type",
            "action_status",
            "task_uuid",
            "task_level",
            "timestamp",
        }
        params = {k: v for k, v in message.items() if k not in system_fields}

        self.file.write(
            f"{timestamp}{indent}{BLUE}▶{RESET_ALL} {BRIGHT}{action_type}{RESET_ALL}"
        )

        if params:
            param_str = " ".join(
                f"{CYAN}{k}{RESET_ALL}={MAGENTA}{repr(v)}{RESET_ALL}"
                for k, v in params.items()
            )
            self.file.write(f" {param_str}")

        if self.show_task_ids:
            self.file.write(f" {DIM}[{task_id[:8]}]{RESET_ALL}")

        self.file.write("\n")
        self.file.flush()

    def _handle_action_result(self, message: Dict[str, Any], task_id: str):
        """Handle successful action completion."""
        action_name = self._action_names.get(task_id, "unknown")
        depth = self._action_stack.get(task_id, 0)

        indent = "  " * depth
        timestamp = self._format_timestamp(message.get("timestamp"))

        # Extract result data
        result_data = {
            k: v
            for k, v in message.items()
            if k
            not in ["message_type", "action_type", "task_id", "task_level", "timestamp"]
        }

        self.file.write(
            f"{timestamp}{indent}{GREEN}✓{RESET_ALL} {DIM}{action_name}{RESET_ALL}"
        )

        if result_data:
            result_str = " ".join(
                f"{CYAN}{k}{RESET_ALL}={MAGENTA}{repr(v)}{RESET_ALL}"
                for k, v in result_data.items()
            )
            self.file.write(f" {result_str}")

        self.file.write("\n")
        self.file.flush()

        # Clean up
        self._action_stack.pop(task_id, None)
        self._action_names.pop(task_id, None)

    def _handle_action_failure(self, message: Dict[str, Any], task_id: str):
        """Handle failed action."""
        action_name = self._action_names.get(task_id, "unknown")
        depth = self._action_stack.get(task_id, 0)

        indent = "  " * depth
        timestamp = self._format_timestamp(message.get("timestamp"))

        exception = message.get("exception", "Unknown error")
        reason = message.get("reason", "")

        self.file.write(
            f"{timestamp}{indent}{RED}✗{RESET_ALL} {DIM}{action_name}{RESET_ALL} "
        )
        self.file.write(f"{RED}FAILED{RESET_ALL}: {exception}")

        if reason:
            self.file.write(f" ({reason})")

        self.file.write("\n")
        self.file.flush()

        # Clean up
        self._action_stack.pop(task_id, None)
        self._action_names.pop(task_id, None)

    def _handle_regular_message(self, message: Dict[str, Any], task_id: str):
        """Handle regular log messages within actions."""
        # Try to find the current action depth
        task_level = message.get("task_level", [])
        depth = len(task_level) if task_level else 0
        if task_id in self._action_stack:
            depth = self._action_stack[task_id] + 1  # Indent messages within actions

        indent = "  " * depth
        timestamp = self._format_timestamp(message.get("timestamp"))

        msg_type = message.get("message_type", "message")

        # Extract message data (exclude system fields)
        system_fields = {"message_type", "task_uuid", "task_level", "timestamp"}
        msg_data = {k: v for k, v in message.items() if k not in system_fields}

        self.file.write(f"{timestamp}{indent}{YELLOW}•{RESET_ALL} {msg_type}")

        if msg_data:
            data_str = " ".join(
                f"{CYAN}{k}{RESET_ALL}={MAGENTA}{repr(v)}{RESET_ALL}"
                for k, v in msg_data.items()
            )
            self.file.write(f" {data_str}")

        self.file.write("\n")
        self.file.flush()

    def _format_timestamp(self, timestamp: Optional[float]) -> str:
        """Format timestamp for display."""
        if not self.show_timestamps or timestamp is None:
            return ""

        dt = datetime.fromtimestamp(timestamp)
        return f"{DIM}{dt.strftime('%H:%M:%S.%f')[:-3]}{RESET_ALL} "


def setup_eliot_logging(
    destination: Optional[TextIO] = None,
    human_readable: bool = True,
    show_timestamps: bool = True,
    show_task_ids: bool = False,
) -> bool:
    """
    Setup Eliot logging with nicestlog integration.

    Args:
        destination: Where to write logs (default: stdout)
        human_readable: Use human-readable format instead of JSON
        show_timestamps: Include timestamps in output
        show_task_ids: Show Eliot task IDs (useful for debugging)

    Returns:
        True if Eliot was successfully configured, False if not available
    """
    if not ELIOT_AVAILABLE:
        print(
            "Warning: Eliot is not available. Install with: pip install eliot",
            file=sys.stderr,
        )
        return False

    from eliot import to_file, add_destinations

    if human_readable:
        dest = HumanReadableEliotDestination(
            file=destination or sys.stdout,
            show_timestamps=show_timestamps,
            show_task_ids=show_task_ids,
        )
        add_destinations(dest)
    else:
        # Use standard JSON output
        to_file(destination or sys.stdout)

    return True


# Convenience decorators and context managers
if ELIOT_AVAILABLE:

    class _ActionContext:
        def __init__(self, action_name: str, **kwargs):
            self._cm = start_action(action_type=action_name, **kwargs)

        def __enter__(self):
            return self._cm.__enter__()

        def __exit__(self, exc_type, exc, tb):
            return self._cm.__exit__(exc_type, exc, tb)

    def log_action(action_name: str, **kwargs):
        """Return a context manager for logging an action with nicestlog formatting."""
        return _ActionContext(action_name, **kwargs)

    def log_call(action_name: Optional[str] = None, **action_kwargs):
        """Decorator to log function calls as Eliot actions."""

        def decorator(func):
            nonlocal action_name
            if action_name is None:
                action_name = f"{func.__module__}.{func.__name__}"

            def wrapper(*args, **kwargs):
                with start_action(action_type=action_name, **action_kwargs) as action:
                    try:
                        result = func(*args, **kwargs)
                        if result is not None:
                            action.add_success_fields(result=result)
                        return result
                    except Exception:
                        # Log the exception without using add_failure_fields
                        pass
                        raise

            return wrapper

        return decorator
else:
    # Dummy implementations when Eliot is not available
    class _DummyActionContext:
        def __enter__(self):
            return None

        def __exit__(self, exc_type, exc, tb):
            return False

    def log_action(action_name: str, **kwargs):
        return _DummyActionContext()

    def log_call(action_name: Optional[str] = None, **action_kwargs):
        def decorator(func):
            return func

        return decorator


# Example usage functions
def demo_eliot_integration():
    """Demonstrate Eliot integration with beautiful output."""
    if not ELIOT_AVAILABLE:
        print("Eliot not available for demo")
        return

    setup_eliot_logging(human_readable=True, show_timestamps=True)

    print("🎭 Eliot Integration Demo - Beautiful Action Tracing!")
    print("=" * 60)

    with log_action("user_request", user_id=123, endpoint="/api/data"):
        log_message(message_type="request_received", method="GET")

        with log_action("database_query", table="users", query="SELECT * FROM users"):
            log_message(message_type="query_executed", rows_returned=42)

        with log_action("cache_lookup", key="user:123"):
            log_message(message_type="cache_hit", ttl=300)

        log_message(message_type="response_sent", status_code=200, size_bytes=1024)

    print("\n🎉 Demo complete! Much better than ugly JSON, right?")


if __name__ == "__main__":
    demo_eliot_integration()
