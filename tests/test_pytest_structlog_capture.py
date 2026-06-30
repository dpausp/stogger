"""Test that pytest-structlog captures events from module-level loggers.

This verifies that the ``log`` fixture (``StructuredLogCapture``) works with
``log.debug()`` and ``log.info()`` called on loggers created at module level.
"""

import structlog
from pytest_structlog import StructuredLogCapture

# Case 1: Plain get_logger() — returns a BoundLoggerLazyProxy
_log_proxy = structlog.get_logger()

# Case 2: get_logger() with positional arg — also a proxy
_log_proxy_with_arg = structlog.get_logger("testmodule")

# Note: The known limitation that ``structlog.get_logger().bind(...)`` at module
# level produces a BoundLogger whose processor chain is snapshotted at creation
# time — and is therefore invisible to pytest-structlog's capture fixture — is
# documented in docs/dev/testing_guide.md ("Bekannte Einschränkung:
# Processor-Snapshot bei BoundLogger") and in docs/user/testing.md. It is a
# structlog upstream behaviour and cannot be pinned by a meaningful runtime
# assertion (the previous xfail test never executed its body).


def test_log_proxy_debug_is_captured(log: StructuredLogCapture) -> None:
    """log.debug() on a proxy logger is captured by the log fixture."""
    _log_proxy.debug("proxy-debug-event")
    assert log.has("proxy-debug-event")


def test_log_proxy_info_is_captured(log: StructuredLogCapture) -> None:
    """log.info() on a proxy logger is captured by the log fixture."""
    _log_proxy.info("proxy-info-event")
    assert log.has("proxy-info-event")


def test_log_proxy_with_arg_debug_is_captured(log: StructuredLogCapture) -> None:
    """log.debug() on a proxy logger (with positional arg) is captured."""
    _log_proxy_with_arg.debug("proxy-arg-debug-event")
    assert log.has("proxy-arg-debug-event")
