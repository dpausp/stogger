"""Permanent tests for logging decorators and log_scope context manager."""

import asyncio

import pytest

from stogger._decorators import log_call, log_operation, log_result, log_scope


# --- log_call ---


def test_log_call_captures_args(log):
    @log_call
    def greet(name: str, greeting: str = "hello") -> str:
        return f"{greeting} {name}"

    greet("world")

    evt = log.events[0]
    assert evt["event"] == "called"
    assert evt["args"] == {"name": "world", "greeting": "hello"}
    assert "result" not in evt
    assert "duration_ms" not in evt
    assert log.has("called")


def test_log_call_returns_original_result():
    @log_call
    def compute() -> int:
        return 42

    assert compute() == 42


# --- log_result ---


def test_log_result_captures_duration(log):
    @log_result
    def fast_func() -> str:
        return "done"

    fast_func()

    evt = log.events[0]
    assert evt["event"] == "returned"
    assert evt["result"] == "done"
    assert isinstance(evt["duration_ms"], float)
    assert evt["duration_ms"] >= 0
    assert log.has("returned")


def test_log_result_no_args_in_event(log):
    @log_result
    def add(a: int, b: int) -> int:
        return a + b

    add(1, 2)

    evt = log.events[0]
    assert "args" not in evt


def test_log_result_exception_logs_failed(log):
    @log_result
    def risky():
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        risky()

    evt = log.events[-1]
    assert evt["event"] == "failed"
    assert evt["exc_type"] == "ValueError"
    assert evt["exc_msg"] == "boom"
    assert isinstance(evt["duration_ms"], float)
    assert evt["duration_ms"] >= 0
    assert log.has("failed")


# --- log_operation ---


def test_log_operation_captures_all(log):
    @log_operation
    def multiply(a: int, b: int) -> int:
        return a * b

    result = multiply(3, 7)

    assert result == 21
    evt = log.events[0]
    assert evt["event"] == "operation"
    assert evt["args"] == {"a": 3, "b": 7}
    assert evt["result"] == 21
    assert "duration_ms" in evt
    assert log.has("operation")


def test_log_operation_exception_logs_failed(log):
    @log_operation(include_args=["x"])
    def crash(x: int):
        raise TypeError("ouch")

    with pytest.raises(TypeError, match="ouch"):
        crash(x=5)

    evt = log.events[-1]
    assert evt["event"] == "failed"
    assert evt["exc_type"] == "TypeError"
    assert evt["exc_msg"] == "ouch"
    assert evt["args"] == {"x": 5}
    assert isinstance(evt["duration_ms"], float)
    assert log.has("failed")


# --- log_scope ---


def test_log_scope_context_manager(log):
    with log_scope("test_scope", key="val") as scope:
        scope.add_fields(count=1)

    evt = log.events[-1]
    assert evt["event"] == "scope-end"
    assert evt["scope"] == "test_scope"
    assert evt["key"] == "val"
    assert evt["count"] == 1
    assert log.has("scope-end")


def test_log_scope_exception_logs_failed(log):
    with pytest.raises(ValueError, match="bad"):
        with log_scope("failing"):
            raise ValueError("bad")

    evt = log.events[-1]
    assert evt["event"] == "scope-failed"
    assert evt["exc_type"] == "ValueError"
    assert evt["exc_msg"] == "bad"
    assert log.has("scope-failed")


# --- async support ---


def test_log_call_async(log):
    @log_call
    async def async_greet(name: str) -> str:
        return f"hi {name}"

    result = asyncio.get_event_loop().run_until_complete(async_greet("world"))

    assert result == "hi world"
    evt = log.events[0]
    assert evt["event"] == "called"
    assert evt["args"] == {"name": "world"}
    assert log.has("called")


def test_log_scope_async(log):
    async def run():
        async with log_scope("async_ctx", x=1) as scope:
            scope.add_fields(y=2)

    asyncio.get_event_loop().run_until_complete(run())

    evt = log.events[-1]
    assert evt["event"] == "scope-end"
    assert evt["scope"] == "async_ctx"
    assert evt["x"] == 1
    assert evt["y"] == 2
    assert log.has("scope-end")


# --- include/exclude args ---


def test_include_args_filters(log):
    @log_operation(include_args=["x"])
    def func(x: int, y: int) -> int:
        return x + y

    func(1, 2)

    evt = log.events[0]
    assert evt["args"] == {"x": 1}


def test_exclude_args_filters(log):
    @log_operation(exclude_args=["password"])
    def login(user: str, password: str) -> bool:
        return True

    login("admin", "secret")

    evt = log.events[0]
    assert "password" not in evt["args"]
    assert evt["args"]["user"] == "admin"


# --- self/cls stripping ---


def test_self_stripped(log):
    class Service:
        @log_call
        def run(self, data: str) -> str:
            return data

    Service().run("test")

    evt = log.events[0]
    assert "self" not in evt["args"]
    assert evt["args"] == {"data": "test"}
    assert log.has("called")


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
