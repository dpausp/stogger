"""Logging decorators and context manager for structured call/result logging."""

import functools
import inspect
import time

import structlog
from structlog import contextvars


def _extract_args(func, args, kwargs, include_args, exclude_args):
    """Extract, normalize, and filter function arguments into a dict.

    Uses inspect.signature + sig.bind + bound.apply_defaults() for full
    resolution of positional args, keyword args, and defaults.
    Strips self/cls, then applies include/exclude filtering.
    """
    sig = inspect.signature(func)
    bound = sig.bind(*args, **kwargs)
    bound.apply_defaults()
    all_args = dict(bound.arguments)

    # Strip self and cls
    all_args.pop("self", None)
    all_args.pop("cls", None)

    # Apply include/exclude filtering
    return _filter_args(all_args, include_args, exclude_args)


def _filter_args(args_dict, include_args, exclude_args):
    """Apply include/exclude filtering to an args dict."""
    if include_args is not None:
        args_dict = {k: v for k, v in args_dict.items() if k in include_args}
    if exclude_args is not None:
        args_dict = {k: v for k, v in args_dict.items() if k not in exclude_args}
    return args_dict


def _make_func_name(func):
    """Compute '{__module__}.{__qualname__}' for a function at decoration time."""
    return f"{func.__module__}.{func.__qualname__}"


def log_call(func=None, *, include_args=None, exclude_args=None):
    """Decorator that logs function entry with args. No result, no duration.

    Logs an event before the function executes. Does NOT catch exceptions —
    exceptions propagate normally since logging happens at entry, before execution.

    Supports both sync and async functions. Automatically strips ``self`` and
    ``cls`` from logged args.

    Args:
        func: The function to decorate. When ``None``, returns a partial that
            accepts the function as a positional argument (enables
            ``@log_call(include_args=[...])`` usage).
        include_args: Optional whitelist of argument names to include.
            When set, only these arguments appear in the logged ``args`` dict.
        exclude_args: Optional blacklist of argument names to exclude.
            When set, these arguments are removed from the logged ``args`` dict.

    Event emitted on function entry::

        {"event": "called", "func": "module.qualname", "args": {...}}

    Example:
        Basic usage::

            from stogger import log_call

            @log_call
            def fetch_user(user_id: int):
                ...

        With argument filtering::

            @log_call(include_args=["user_id"])
            def fetch_user(user_id: int, password: str):
                ...

    """
    if func is None:
        return functools.partial(log_call, include_args=include_args, exclude_args=exclude_args)

    func_name = _make_func_name(func)

    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            log = structlog.get_logger()
            all_args = _extract_args(func, args, kwargs, include_args, exclude_args)
            log.info(
                "called",
                _replace_msg="{func} called with {args}",
                func=func_name,
                args=all_args,
            )
            return await func(*args, **kwargs)

        return async_wrapper

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        log = structlog.get_logger()
        all_args = _extract_args(func, args, kwargs, include_args, exclude_args)
        log.info(
            "called",
            _replace_msg="{func} called with {args}",
            func=func_name,
            args=all_args,
        )
        return func(*args, **kwargs)

    return sync_wrapper


def log_result(func=None, *, include_args=None, exclude_args=None):
    """Decorator that logs function exit with result and duration_ms.

    On success: logs ``event="returned"`` with the function's return value and
    wall-clock duration. On exception: logs ``event="failed"`` with
    ``exc_type``/``exc_msg`` and duration, then re-raises the exception.

    Supports both sync and async functions. Automatically strips ``self`` and
    ``cls`` from logged args.

    Args:
        func: The function to decorate. When ``None``, returns a partial that
            accepts the function as a positional argument (enables
            ``@log_result(include_args=[...])`` usage).
        include_args: Optional whitelist of argument names to include.
            When set, only these arguments appear in the logged ``args`` dict.
        exclude_args: Optional blacklist of argument names to exclude.
            When set, these arguments are removed from the logged ``args`` dict.

    Event emitted on success::

        {"event": "returned", "func": "module.qualname",
         "result": <return_value>, "duration_ms": <float>}

    Event emitted on exception::

        {"event": "failed", "func": "module.qualname",
         "exc_type": "ValueError", "exc_msg": "...", "duration_ms": <float>}

    Example:
        Basic usage::

            from stogger import log_result

            @log_result
            def compute_hash(data: bytes) -> str:
                ...

        Exception is logged and re-raised::

            @log_result
            def risky_operation():
                raise ValueError("bad input")
                # Logs: {"event": "failed", "exc_type": "ValueError", ...}

    """
    if func is None:
        return functools.partial(log_result, include_args=include_args, exclude_args=exclude_args)

    func_name = _make_func_name(func)

    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            log = structlog.get_logger()
            t0 = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
            except Exception as exc:
                duration_ms = (time.perf_counter() - t0) * 1000
                log.warning(
                    "failed",
                    _replace_msg="{func} failed: {exc_type}: {exc_msg}",
                    func=func_name,
                    exc_type=type(exc).__name__,
                    exc_msg=str(exc),
                    duration_ms=duration_ms,
                )
                raise
            duration_ms = (time.perf_counter() - t0) * 1000
            log.info(
                "returned",
                _replace_msg="{func} returned {result} in {duration_ms:.1f}ms",
                func=func_name,
                result=result,
                duration_ms=duration_ms,
            )
            return result

        return async_wrapper

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        log = structlog.get_logger()
        t0 = time.perf_counter()
        try:
            result = func(*args, **kwargs)
        except Exception as exc:
            duration_ms = (time.perf_counter() - t0) * 1000
            log.warning(
                "failed",
                _replace_msg="{func} failed: {exc_type}: {exc_msg}",
                func=func_name,
                exc_type=type(exc).__name__,
                exc_msg=str(exc),
                duration_ms=duration_ms,
            )
            raise
        duration_ms = (time.perf_counter() - t0) * 1000
        log.info(
            "returned",
            _replace_msg="{func} returned {result} in {duration_ms:.1f}ms",
            func=func_name,
            result=result,
            duration_ms=duration_ms,
        )
        return result

    return sync_wrapper


def log_operation(func=None, *, include_args=None, exclude_args=None):
    """Decorator that logs full operation: args, result, and duration_ms.

    Combines the behavior of :func:`log_call` and :func:`log_result` into a
    single event that contains arguments, return value, and timing. On
    exception: logs ``event="failed"`` with args, ``exc_type``/``exc_msg``,
    and duration, then re-raises.

    Supports both sync and async functions. Automatically strips ``self`` and
    ``cls`` from logged args.

    Args:
        func: The function to decorate. When ``None``, returns a partial that
            accepts the function as a positional argument (enables
            ``@log_operation(include_args=[...])`` usage).
        include_args: Optional whitelist of argument names to include.
            When set, only these arguments appear in the logged ``args`` dict.
        exclude_args: Optional blacklist of argument names to exclude.
            When set, these arguments are removed from the logged ``args`` dict.

    Event emitted on success::

        {"event": "operation", "func": "module.qualname",
         "args": {...}, "result": <return_value>, "duration_ms": <float>}

    Event emitted on exception::

        {"event": "failed", "func": "module.qualname", "args": {...},
         "exc_type": "ValueError", "exc_msg": "...", "duration_ms": <float>}

    Example:
        Full audit logging with filtering::

            from stogger import log_operation

            @log_operation(include_args=["query"], exclude_args=["password"])
            def authenticate(query: str, password: str) -> bool:
                ...

    """
    if func is None:
        return functools.partial(log_operation, include_args=include_args, exclude_args=exclude_args)

    func_name = _make_func_name(func)

    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            log = structlog.get_logger()
            all_args = _extract_args(func, args, kwargs, include_args, exclude_args)
            t0 = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
            except Exception as exc:
                duration_ms = (time.perf_counter() - t0) * 1000
                log.warning(
                    "failed",
                    _replace_msg="{func} failed: {exc_type}: {exc_msg}",
                    func=func_name,
                    args=all_args,
                    exc_type=type(exc).__name__,
                    exc_msg=str(exc),
                    duration_ms=duration_ms,
                )
                raise
            duration_ms = (time.perf_counter() - t0) * 1000
            log.info(
                "operation",
                _replace_msg="{func}({args}) -> {result} in {duration_ms:.1f}ms",
                func=func_name,
                args=all_args,
                result=result,
                duration_ms=duration_ms,
            )
            return result

        return async_wrapper

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        log = structlog.get_logger()
        all_args = _extract_args(func, args, kwargs, include_args, exclude_args)
        t0 = time.perf_counter()
        try:
            result = func(*args, **kwargs)
        except Exception as exc:
            duration_ms = (time.perf_counter() - t0) * 1000
            log.warning(
                "failed",
                _replace_msg="{func} failed: {exc_type}: {exc_msg}",
                func=func_name,
                args=all_args,
                exc_type=type(exc).__name__,
                exc_msg=str(exc),
                duration_ms=duration_ms,
            )
            raise
        duration_ms = (time.perf_counter() - t0) * 1000
        log.info(
            "operation",
            _replace_msg="{func}({args}) -> {result} in {duration_ms:.1f}ms",
            func=func_name,
            args=all_args,
            result=result,
            duration_ms=duration_ms,
        )
        return result

    return sync_wrapper


class LogScope:
    """Context manager for scoped structured logging with sync and async support.

    Binds structured fields on enter, logs ``scope-end`` on clean exit with
    ``duration_ms`` and all accumulated fields. On exception: logs
    ``scope-failed`` with ``exc_type``/``exc_msg`` and duration, then re-raises.

    Fields passed to the constructor are bound to every exit event. Additional
    fields can be added mid-scope via :meth:`add_fields`.

    Args:
        name: Scope identifier used as the ``scope`` field in log events.
        **fields: Arbitrary key-value pairs bound to the scope. Included in
            both success and failure exit events.

    Event emitted on clean exit::

        {"event": "scope-end", "scope": "<name>", <bound_fields>,

    Event emitted on exception::

        {"event": "scope-failed", "scope": "<name>,

    Example:
        ::

            from stogger import log_scope

            with log_scope("db_transaction", table="users") as scope:
                insert(user)
                scope.add_fields(rows_inserted=1)
                # Exit event: {"event": "scope-end", "scope": "db_transaction",

    """

    def __init__(self, name, **fields):
        self._name = name
        self._fields = fields
        self._extra_fields = {}
        self._t0 = 0.0

    def add_fields(self, **kwargs):
        """Add fields to the scope that appear in the exit event.

        Can be called multiple times. Fields accumulate across calls. Fields
        set here are merged with constructor fields on exit, with ``add_fields``
        values taking precedence on key collision.

        Args:
            **kwargs: Arbitrary key-value pairs to include in the exit event.

        """
        self._extra_fields.update(kwargs)
        contextvars.bind_contextvars(**kwargs)

    def __enter__(self):
        self._t0 = time.perf_counter()
        contextvars.bind_contextvars(**self._fields)
        return self

    def __exit__(self, exc_type, exc_val, _exc_tb):
        log = structlog.get_logger()
        duration_ms = (time.perf_counter() - self._t0) * 1000
        contextvars.unbind_contextvars(*self._fields, *self._extra_fields)
        all_fields = {**self._fields, **self._extra_fields}
        if exc_type is not None:
            log.warning(
                "scope-failed",
                _replace_msg="Scope '{scope}' failed: {exc_type}: {exc_msg}",
                scope=self._name,
                exc_type=exc_type.__name__,
                exc_msg=str(exc_val),
                duration_ms=duration_ms,
                **all_fields,
            )
        else:
            log.debug(
                "scope-end",
                scope=self._name,
                duration_ms=duration_ms,
                **all_fields,
            )
        return False

    async def __aenter__(self):
        self._t0 = time.perf_counter()
        contextvars.bind_contextvars(**self._fields)
        return self

    async def __aexit__(self, exc_type, exc_val, _exc_tb):
        log = structlog.get_logger()
        duration_ms = (time.perf_counter() - self._t0) * 1000
        contextvars.unbind_contextvars(*self._fields, *self._extra_fields)
        all_fields = {**self._fields, **self._extra_fields}
        if exc_type is not None:
            log.warning(
                "scope-failed",
                _replace_msg="Scope '{scope}' failed: {exc_type}: {exc_msg}",
                scope=self._name,
                exc_type=exc_type.__name__,
                exc_msg=str(exc_val),
                duration_ms=duration_ms,
                **all_fields,
            )
        else:
            log.debug(
                "scope-end",
                scope=self._name,
                duration_ms=duration_ms,
                **all_fields,
            )
        return False


def log_scope(name, **fields):
    """Create a :class:`LogScope` context manager for structured scoped logging.

    Factory function that constructs a :class:`LogScope` instance. Use as a
    ``with`` statement or ``async with`` statement for scoped logging with
    automatic timing and exception handling.

    Args:
        name: Scope identifier used as the ``scope`` field in log events.
        **fields: Arbitrary key-value pairs bound to the scope.

    Returns:
        LogScope: A context manager instance that logs scope entry/exit.

    Example:
        ::

            from stogger import log_scope

            with log_scope("migration", version="2.0"):
                run_migration()

    """
    return LogScope(name, **fields)
