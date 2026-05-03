"""Logging decorators and context manager for structured call/result logging."""

import functools
import inspect
import time

import structlog


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

    Does NOT catch exceptions — logs at entry only, before execution.
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

    On exception: logs event='failed' with exc_type/exc_msg/duration_ms, then re-raises.
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

    On exception: logs event='failed' with args, exc_type, exc_msg, duration_ms, then re-raises.
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
    """Context manager for scoped structured logging.

    Binds fields on enter, logs scope_end on clean exit,
    logs scope_failed on exception (with exc_type/exc_msg), then re-raises.
    Supports both ``with`` and ``async with``.
    """

    def __init__(self, name, **fields):
        self._name = name
        self._fields = fields
        self._extra_fields = {}
        self._t0 = 0.0

    def add_fields(self, **kwargs):
        """Add fields to the scope that appear in the exit event."""
        self._extra_fields.update(kwargs)

    def __enter__(self):
        self._t0 = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, _exc_tb):
        log = structlog.get_logger()
        duration_ms = (time.perf_counter() - self._t0) * 1000
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
        return self

    async def __aexit__(self, exc_type, exc_val, _exc_tb):
        log = structlog.get_logger()
        duration_ms = (time.perf_counter() - self._t0) * 1000
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
    """Create a LogScope context manager for structured scoped logging."""
    return LogScope(name, **fields)
