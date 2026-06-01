stogger.decorators
==================

.. py:module:: stogger.decorators

.. autoapi-nested-parse::

   Logging decorators and context manager for structured call/result logging.



Classes
-------

.. autoapisummary::

   stogger.decorators.LogScope


Functions
---------

.. autoapisummary::

   stogger.decorators.log_call
   stogger.decorators.log_result
   stogger.decorators.log_operation
   stogger.decorators.log_scope


Module Contents
---------------

.. py:function:: log_call(func=None, *, include_args=None, exclude_args=None)

   Decorator that logs function entry with args. No result, no duration.

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



.. py:function:: log_result(func=None, *, include_args=None, exclude_args=None)

   Decorator that logs function exit with result and duration_ms.

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



.. py:function:: log_operation(func=None, *, include_args=None, exclude_args=None)

   Decorator that logs full operation: args, result, and duration_ms.

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



.. py:class:: LogScope(name, **fields)

   Context manager for scoped structured logging with sync and async support.

   Binds structured fields on enter, logs ``scope-end`` on clean exit with
   ``duration_ms`` and all accumulated fields. On exception: logs
   ``scope-failed`` with ``exc_type``/``exc_msg`` and duration, then re-raises.

   Fields passed to the constructor are bound to every exit event. Additional
   fields can be added mid-scope via :meth:`add_fields`.

   Args:
       name: Scope identifier used as the ``scope`` field in log events.
       fields: Key-value pairs bound to the scope, included in all exit events.

   Event emitted on clean exit::

       {"event": "scope-end", "scope": "<name>", "duration_ms": <float>, <bound_fields>}

   Event emitted on exception::

       {"event": "scope-failed", "scope": "<name>", "exc_type": "ValueError", "exc_msg": "...", "duration_ms": <float>}

   Example:
       ::

           from stogger import log_scope

           with log_scope("db_transaction", table="users") as scope:
               insert(user)
               scope.add_fields(rows_inserted=1)
               # Exit event: {"event": "scope-end", "scope": "db_transaction", "duration_ms": 12.3, "table": "users"}



   .. py:method:: add_fields(**kwargs)

      Add fields to the scope that appear in the exit event.

      Can be called multiple times. Fields accumulate across calls. Fields
      set here are merged with constructor fields on exit, with ``add_fields``
      values taking precedence on key collision.

      Args:
          kwargs: Arbitrary key-value pairs to include in the exit event.




.. py:function:: log_scope(name, **fields)

   Create a :class:`LogScope` context manager for structured scoped logging.

   Factory function that constructs a :class:`LogScope` instance. Use as a
   ``with`` statement or ``async with`` statement for scoped logging with
   automatic timing and exception handling.

   Args:
       name: Scope identifier used as the ``scope`` field in log events.
       fields: Arbitrary key-value pairs bound to the scope.

   Returns:
       LogScope: A context manager instance that logs scope entry/exit.

   Example:
       ::

           from stogger import log_scope

           with log_scope("migration", version="2.0"):
               run_migration()



