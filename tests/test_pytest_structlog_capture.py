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

# Case 3: get_logger().bind() — returns a direct BoundLogger with snapshotted processors!
_log_bound = structlog.get_logger("testmodule").bind(scope="module-level")


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


def test_log_bound_debug_not_captured_by_design(log: StructuredLogCapture) -> None:
    """log.debug() on a BoundLogger (from .bind()) is NOT captured.

    ``get_logger().bind(...)`` at module level creates a direct ``BoundLogger``
    that snapshots ``_processors`` at creation time
    (structlog._base.BoundLoggerBase line 58). The ``log`` fixture's
    ``structlog.configure()`` updates ``_CONFIG.default_processors``, but
    existing ``BoundLogger`` instances still use their snapshotted chain.

    This is a known structlog limitation — avoid ``.bind()`` at module level.
    Use ``structlog.get_logger()`` (returns a lazy proxy) and bind inside
    functions instead.
    """
    import pytest

    pytest.xfail(
        "BoundLogger stores _processors snapshot at creation time; "
        "structlog.configure() does not update existing instances"
    )
    _log_bound.debug("bound-debug-event")
    assert log.has("bound-debug-event")
