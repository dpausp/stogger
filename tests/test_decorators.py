"""Permanent tests for logging decorators and log_scope context manager."""

import asyncio

import pytest
import structlog

from stogger._decorators import log_call, log_operation, log_result, log_scope


@pytest.fixture
def captured_events():
    """Configure structlog to capture all events into a list."""
    events: list[dict] = []

    structlog.configure(
        processors=[lambda _, __, ed: (events.append(dict(ed)), str(ed))[1]],
        wrapper_class=structlog.BoundLogger,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )

    return events


# --- log_call ---


def test_log_call_captures_args(captured_events):
    @log_call
    def greet(name: str, greeting: str = "hello") -> str:
        return f"{greeting} {name}"

    greet("world")

    evt = captured_events[0]
    assert evt["event"] == "called"
    assert evt["args"] == {"name": "world", "greeting": "hello"}
    assert "result" not in evt
    assert "duration_ms" not in evt


def test_log_call_returns_original_result():
    @log_call
    def compute() -> int:
        return 42

    assert compute() == 42


# --- log_result ---


def test_log_result_captures_duration(captured_events):
    @log_result
    def fast_func() -> str:
        return "done"

    fast_func()

    evt = captured_events[0]
    assert evt["event"] == "returned"
    assert evt["result"] == "done"
    assert isinstance(evt["duration_ms"], float)
    assert evt["duration_ms"] >= 0


def test_log_result_no_args_in_event(captured_events):
    @log_result
    def add(a: int, b: int) -> int:
        return a + b

    add(1, 2)

    evt = captured_events[0]
    assert "args" not in evt


# --- log_operation ---


def test_log_operation_captures_all(captured_events):
    @log_operation
    def multiply(a: int, b: int) -> int:
        return a * b

    result = multiply(3, 7)

    assert result == 21
    evt = captured_events[0]
    assert evt["event"] == "operation"
    assert evt["args"] == {"a": 3, "b": 7}
    assert evt["result"] == 21
    assert "duration_ms" in evt


# --- log_scope ---


def test_log_scope_context_manager(captured_events):
    with log_scope("test_scope", key="val") as scope:
        scope.add_fields(count=1)

    evt = captured_events[-1]
    assert evt["event"] == "scope-end"
    assert evt["scope"] == "test_scope"
    assert evt["key"] == "val"
    assert evt["count"] == 1


def test_log_scope_exception_logs_failed(captured_events):
    with pytest.raises(ValueError, match="bad"):
        with log_scope("failing"):
            raise ValueError("bad")

    evt = captured_events[-1]
    assert evt["event"] == "scope-failed"
    assert evt["exc_type"] == "ValueError"
    assert evt["exc_msg"] == "bad"


# --- async support ---


def test_log_call_async(captured_events):
    @log_call
    async def async_greet(name: str) -> str:
        return f"hi {name}"

    result = asyncio.get_event_loop().run_until_complete(async_greet("world"))

    assert result == "hi world"
    evt = captured_events[0]
    assert evt["event"] == "called"
    assert evt["args"] == {"name": "world"}


def test_log_scope_async(captured_events):
    async def run():
        async with log_scope("async_ctx", x=1) as scope:
            scope.add_fields(y=2)

    asyncio.get_event_loop().run_until_complete(run())

    evt = captured_events[-1]
    assert evt["event"] == "scope-end"
    assert evt["scope"] == "async_ctx"
    assert evt["x"] == 1
    assert evt["y"] == 2


# --- include/exclude args ---


def test_include_args_filters(captured_events):
    @log_operation(include_args=["x"])
    def func(x: int, y: int) -> int:
        return x + y

    func(1, 2)

    evt = captured_events[0]
    assert evt["args"] == {"x": 1}


def test_exclude_args_filters(captured_events):
    @log_operation(exclude_args=["password"])
    def login(user: str, password: str) -> bool:
        return True

    login("admin", "secret")

    evt = captured_events[0]
    assert "password" not in evt["args"]
    assert evt["args"]["user"] == "admin"


# --- self/cls stripping ---


def test_self_stripped(captured_events):
    class Service:
        @log_call
        def run(self, data: str) -> str:
            return data

    Service().run("test")

    evt = captured_events[0]
    assert "self" not in evt["args"]
    assert evt["args"] == {"data": "test"}


# --- top-level imports ---


def test_top_level_imports():
    from stogger import log_call as lc
    from stogger import log_operation as lo
    from stogger import log_result as lr
    from stogger import log_scope as ls

    assert callable(lc)
    assert callable(lr)
    assert callable(lo)
    assert callable(ls)
