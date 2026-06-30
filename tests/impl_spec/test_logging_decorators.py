"""Spec validation tests for logging-decorators.

These tests define the CONTRACT that logging-decorators implementation
must fulfill. All tests are marked xfail because the feature doesn't exist yet.
They will be garbage-collected after implementation makes them green.

Spec: .agents/impl_specs/logging-decorators.md

Decision coverage:
  - module-placement: imports from stogger._decorators, Layer 2 module
  - decorator-variants: log_call, log_result, log_operation produce correct events
  - scope-object-design: log_scope returns LogScope, context manager semantics
  - async-support: all decorators and log_scope work with async
  - arg-extraction: defaults, self/cls stripping, include/exclude filtering
  - duration-measurement: duration_ms present and >= 0 for exit decorators
  - exception-handling: exc_type/exc_msg logging, re-raise, log_call no catch
  - func-name: func field is "{__module__}.{__qualname__}"
"""

import asyncio

import pytest
import structlog


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_structlog():
    """Reset structlog configuration after each test to avoid state leakage."""
    yield
    structlog.reset_defaults()


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


# ---------------------------------------------------------------------------
# module-placement: _decorators module exists at Layer 2, re-exported
# ---------------------------------------------------------------------------


def test_import_log_call_from_decorators():
    """from stogger._decorators import log_call must work."""
    from stogger._decorators import log_call  # noqa: F401


def test_import_log_result_from_decorators():
    """from stogger._decorators import log_result must work."""
    from stogger._decorators import log_result  # noqa: F401


def test_import_log_operation_from_decorators():
    """from stogger._decorators import log_operation must work."""
    from stogger._decorators import log_operation  # noqa: F401


def test_import_log_scope_from_decorators():
    """from stogger._decorators import log_scope, LogScope must work."""
    from stogger._decorators import LogScope, log_scope  # noqa: F401


def test_import_log_call_from_stogger_top_level():
    """from stogger import log_call must work (re-exported)."""
    from stogger import log_call  # noqa: F401


def test_import_log_scope_from_stogger_top_level():
    """from stogger import log_scope must work (re-exported)."""
    from stogger import log_scope  # noqa: F401


# ---------------------------------------------------------------------------
# decorator-variants: log_call, log_result, log_operation produce correct events
# ---------------------------------------------------------------------------


def test_log_call_produces_called_event(captured_events):
    """@log_call must produce event='called' with func and args, no result/duration."""
    from stogger._decorators import log_call

    @log_call
    def greet(name: str) -> str:
        return f"hello {name}"

    greet("world")

    assert len(captured_events) == 1
    evt = captured_events[0]
    assert evt["event"] == "called"
    assert "func" in evt
    assert "args" in evt
    assert evt["args"] == {"name": "world"}
    assert "result" not in evt
    assert "duration_ms" not in evt


def test_log_result_produces_returned_event(captured_events):
    """@log_result must produce event='returned' with func, result, duration_ms, no args."""
    from stogger._decorators import log_result

    @log_result
    def compute() -> int:
        return 42

    result = compute()

    assert result == 42
    assert len(captured_events) == 1
    evt = captured_events[0]
    assert evt["event"] == "returned"
    assert "func" in evt
    assert evt["result"] == 42
    assert "duration_ms" in evt
    assert "args" not in evt


def test_log_operation_produces_operation_event(captured_events):
    """@log_operation must produce event='operation' with func, args, result, duration_ms."""
    from stogger._decorators import log_operation

    @log_operation
    def add(a: int, b: int) -> int:
        return a + b

    result = add(3, 4)

    assert result == 7
    assert len(captured_events) == 1
    evt = captured_events[0]
    assert evt["event"] == "operation"
    assert "func" in evt
    assert evt["args"] == {"a": 3, "b": 4}
    assert evt["result"] == 7
    assert "duration_ms" in evt


# ---------------------------------------------------------------------------
# scope-object-design: log_scope returns LogScope, context manager semantics
# ---------------------------------------------------------------------------


def test_log_scope_returns_log_scope_instance():
    """log_scope('name') must return a LogScope instance."""
    from stogger._decorators import LogScope, log_scope

    scope = log_scope("test_scope", key="val")
    assert isinstance(scope, LogScope)


def test_log_scope_has_add_fields_method():
    """LogScope must have an add_fields(**kwargs) method."""
    from stogger._decorators import log_scope

    scope = log_scope("test_scope")
    assert hasattr(scope, "add_fields")
    assert callable(scope.add_fields)


def test_log_scope_success_produces_scope_end_event(captured_events):
    """Successful scope produces event='scope_end' with duration_ms."""
    from stogger._decorators import log_scope

    with log_scope("db_transaction", table="users") as scope:
        scope.add_fields(rows=1)

    assert len(captured_events) >= 1
    evt = captured_events[-1]
    assert evt["event"] == "scope-end"
    assert evt["scope"] == "db_transaction"
    assert evt["table"] == "users"
    assert evt["rows"] == 1
    assert "duration_ms" in evt


def test_log_scope_exception_produces_scope_failed_event(captured_events):
    """Scope with exception produces event='scope_failed' with exc_type/exc_msg."""
    from stogger._decorators import log_scope

    with pytest.raises(RuntimeError, match="boom"):
        with log_scope("failing_scope"):
            raise RuntimeError("boom")

    assert len(captured_events) >= 1
    evt = captured_events[-1]
    assert evt["event"] == "scope-failed"
    assert evt["scope"] == "failing_scope"
    assert evt["exc_type"] == "RuntimeError"
    assert evt["exc_msg"] == "boom"
    assert "duration_ms" in evt


# ---------------------------------------------------------------------------
# async-support: decorators work with async def, log_scope with async with
# ---------------------------------------------------------------------------


def test_log_call_works_with_async(captured_events):
    """@log_call must work with async functions."""
    from stogger._decorators import log_call

    @log_call
    async def fetch_data(query: str) -> str:
        return f"data for {query}"

    result = asyncio.get_event_loop().run_until_complete(fetch_data("test"))

    assert result == "data for test"
    assert len(captured_events) == 1
    evt = captured_events[0]
    assert evt["event"] == "called"
    assert evt["args"] == {"query": "test"}


def test_log_result_works_with_async(captured_events):
    """@log_result must work with async functions."""
    from stogger._decorators import log_result

    @log_result
    async def compute_async() -> int:
        return 99

    result = asyncio.get_event_loop().run_until_complete(compute_async())

    assert result == 99
    assert len(captured_events) == 1
    evt = captured_events[0]
    assert evt["event"] == "returned"
    assert evt["result"] == 99


def test_log_operation_works_with_async(captured_events):
    """@log_operation must work with async functions."""
    from stogger._decorators import log_operation

    @log_operation
    async def async_add(a: int, b: int) -> int:
        return a + b

    result = asyncio.get_event_loop().run_until_complete(async_add(1, 2))

    assert result == 3
    assert len(captured_events) == 1
    evt = captured_events[0]
    assert evt["event"] == "operation"
    assert evt["result"] == 3


def test_log_scope_works_with_async_with(captured_events):
    """log_scope must work with 'async with'."""
    from stogger._decorators import log_scope

    async def run_scope():
        async with log_scope("async_scope", key="val") as scope:
            scope.add_fields(count=5)

    asyncio.get_event_loop().run_until_complete(run_scope())

    assert len(captured_events) >= 1
    evt = captured_events[-1]
    assert evt["event"] == "scope-end"
    assert evt["scope"] == "async_scope"


# ---------------------------------------------------------------------------
# arg-extraction: defaults, self/cls stripping, include/exclude filtering
# ---------------------------------------------------------------------------


def test_args_include_default_values(captured_events):
    """Args dict must include default parameter values."""
    from stogger._decorators import log_call

    @log_call
    def func_with_defaults(x: int, y: int = 10) -> int:
        return x + y

    func_with_defaults(1)

    evt = captured_events[0]
    assert evt["args"] == {"x": 1, "y": 10}


def test_args_strip_self(captured_events):
    """Args dict must not contain 'self'."""
    from stogger._decorators import log_call

    class Service:
        @log_call
        def process(self, data: str) -> str:
            return data.upper()

    Service().process("hello")

    evt = captured_events[0]
    assert "self" not in evt["args"]
    assert evt["args"] == {"data": "hello"}


def test_args_strip_cls(captured_events):
    """Args dict must not contain 'cls'."""
    from stogger._decorators import log_call

    class Handler:
        @classmethod
        @log_call
        def create(cls, name: str) -> str:
            return name

    Handler.create("test")

    evt = captured_events[0]
    assert "cls" not in evt["args"]
    assert evt["args"] == {"name": "test"}


def test_include_args_whitelist_filtering(captured_events):
    """include_args must filter args to only whitelisted names."""
    from stogger._decorators import log_operation

    @log_operation(include_args=["query"])
    def authenticate(query: str, password: str) -> bool:
        return True

    authenticate("admin", "secret")

    evt = captured_events[0]
    assert evt["args"] == {"query": "admin"}
    assert "password" not in evt["args"]


def test_exclude_args_blacklist_filtering(captured_events):
    """exclude_args must remove specified arg names."""
    from stogger._decorators import log_operation

    @log_operation(exclude_args=["password"])
    def authenticate(query: str, password: str) -> bool:
        return True

    authenticate("admin", "secret")

    evt = captured_events[0]
    assert "password" not in evt["args"]
    assert evt["args"]["query"] == "admin"


# ---------------------------------------------------------------------------
# duration-measurement: duration_ms present and >= 0
# ---------------------------------------------------------------------------


def test_log_result_has_duration_ms(captured_events):
    """@log_result must include duration_ms >= 0."""
    from stogger._decorators import log_result

    @log_result
    def fast_func() -> None:
        pass

    fast_func()

    evt = captured_events[0]
    assert "duration_ms" in evt
    assert evt["duration_ms"] >= 0


def test_log_operation_has_duration_ms(captured_events):
    """@log_operation must include duration_ms >= 0."""
    from stogger._decorators import log_operation

    @log_operation
    def another_func() -> str:
        return "done"

    another_func()

    evt = captured_events[0]
    assert "duration_ms" in evt
    assert evt["duration_ms"] >= 0


def test_log_scope_has_duration_ms(captured_events):
    """log_scope must include duration_ms >= 0 in scope_end event."""
    from stogger._decorators import log_scope

    with log_scope("timed_scope"):
        pass

    evt = captured_events[-1]
    assert "duration_ms" in evt
    assert evt["duration_ms"] >= 0


# ---------------------------------------------------------------------------
# exception-handling: exc_type/exc_msg logging, re-raise, log_call no catch
# ---------------------------------------------------------------------------


def test_log_result_logs_exception_and_reraises(captured_events):
    """@log_result on exception: logs event='failed' with exc_type/exc_msg/duration_ms, re-raises."""
    from stogger._decorators import log_result

    @log_result
    def failing_func() -> None:
        raise ValueError("bad input")

    with pytest.raises(ValueError, match="bad input"):
        failing_func()

    evt = captured_events[0]
    assert evt["event"] == "failed"
    assert evt["exc_type"] == "ValueError"
    assert evt["exc_msg"] == "bad input"
    assert "duration_ms" in evt


def test_log_operation_logs_exception_with_args(captured_events):
    """@log_operation on exception: logs event='failed' with args, exc_type, exc_msg, duration_ms."""
    from stogger._decorators import log_operation

    @log_operation
    def failing_with_args(x: int) -> None:
        raise RuntimeError(f"failed on {x}")

    with pytest.raises(RuntimeError, match="failed on 5"):
        failing_with_args(5)

    evt = captured_events[0]
    assert evt["event"] == "failed"
    assert evt["exc_type"] == "RuntimeError"
    assert evt["exc_msg"] == "failed on 5"
    assert evt["args"] == {"x": 5}
    assert "duration_ms" in evt


def test_log_call_does_not_catch_exceptions(captured_events):
    """@log_call must NOT catch exceptions — it logs at entry only."""
    from stogger._decorators import log_call

    @log_call
    def explode() -> None:
        raise TypeError("kaboom")

    with pytest.raises(TypeError, match="kaboom"):
        explode()

    # Only the "called" event, no exception event
    assert len(captured_events) == 1
    assert captured_events[0]["event"] == "called"


def test_log_scope_exception_reraises(captured_events):
    """log_scope must re-raise the exception after logging scope_failed."""
    from stogger._decorators import log_scope

    with pytest.raises(ConnectionError, match="timeout"):
        with log_scope("net_op"):
            raise ConnectionError("timeout")

    evt = captured_events[-1]
    assert evt["event"] == "scope-failed"
    assert evt["exc_type"] == "ConnectionError"
    assert evt["exc_msg"] == "timeout"


# ---------------------------------------------------------------------------
# func-name: func field is "{__module__}.{__qualname__}"
# ---------------------------------------------------------------------------


def test_func_field_is_module_qualname(captured_events):
    """func field must be '{__module__}.{__qualname__}' of the wrapped function."""
    from stogger._decorators import log_call

    @log_call
    def my_function() -> None:
        pass

    my_function()

    evt = captured_events[0]
    assert evt["func"] == f"{my_function.__module__}.{my_function.__qualname__}"


def test_func_field_for_method(captured_events):
    """func field for a method includes class name in qualname."""
    from stogger._decorators import log_call

    class MyClass:
        @log_call
        def do_work(self) -> None:
            pass

    MyClass().do_work()

    evt = captured_events[0]
    # qualname for a method is 'MyClass.do_work' or 'test_func_field_for_method.<locals>.MyClass.do_work'
    assert "MyClass.do_work" in evt["func"]
