"""CLI layer with intentional convention violations.

This file triggers ALL pytest-stogger rules to demonstrate what they catch.
"""

import structlog

log = structlog.get_logger(__name__)


def create_user(name: str, email: str) -> None:
    """Violation 1: No context (check_context_required)."""
    log.info("user-created")  # No keyword args!


def send_notification(message: str) -> None:
    """Violation 2: f-string in log call (check_no_fstring)."""
    log.info("notification-sent", message=f"Hello {message}", _replace_msg="Sent: {message}")


def update_settings(key: str, value: str) -> None:
    """Violation 3: Missing _replace_msg for info (check_info_requires_replace_msg)."""
    log.info("settings-updated", key=key, value=value)


def debug_helper(data: str) -> None:
    """Violation 4: debug with _replace_msg (check_debug_no_replace_msg)."""
    log.debug("debug-data", data=data, _replace_msg="Data: {data}")


def handle_error(code: int) -> None:
    """Violation 5: duplicate error key in exception (check_exception_no_dupe)."""
    try:
        msg = "Something failed"
        raise RuntimeError(msg)
    except RuntimeError:
        log.exception("error-occurred", error="bad", code=code)  # 'error' is redundant


def repeat_keys() -> None:
    """Violation 6: repeating keys without bind (check_bind_for_repeating)."""
    log.info("step-one", task_id="abc", _replace_msg="Step one {task_id}")
    log.info("step-two", task_id="abc", _replace_msg="Step two {task_id}")
    log.info("step-three", task_id="abc", _replace_msg="Step three {task_id}")


def _internal_helper() -> None:
    """Violation 7: private method with log.info (check_private_no_info)."""
    log.info("internal-event", _replace_msg="Internal")


def save_to_file(path: str) -> None:
    """Violation 8: except block without logging (check_except_must_log)."""
    try:
        with open(path) as f:  # noqa: PTH123
            data = f.read()
    except OSError:
        pass  # Silent! Should log.


def process_many() -> None:
    """Violation 9: complex function without log (check_complexity_needs_log).

    Has CC >= 1 but no log call.
    """
    x = 1
    if x > 0:
        x += 1
        if x > 1:
            x += 1
    # Intentionally no log call — violates complexity rule


def admin_action(action: str) -> None:
    """Violation 10: log.info outside allowed layer (check_info_layer).

    This file is in the 'cli' layer, but info_allowed_layers = ["service"].
    """
    log.info("admin-action-taken", action=action, _replace_msg="Admin: {action}")
