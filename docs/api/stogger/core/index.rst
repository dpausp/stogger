stogger.core
============

.. py:module:: stogger.core

.. autoapi-nested-parse::

   Core logging functionality for stogger.



Attributes
----------

.. autoapisummary::

   stogger.core.log
   stogger.core.JOURNAL_LEVELS
   stogger.core.KEYS_TO_SKIP_IN_JOURNAL_MESSAGE


Classes
-------

.. autoapisummary::

   stogger.core.PartialFormatter
   stogger.core.TranslationProcessor
   stogger.core.ConsoleFileRenderer
   stogger.core.JSONRenderer
   stogger.core.SelectRenderedString
   stogger.core.JournalLoggerFactory
   stogger.core.SystemdJournalRenderer
   stogger.core.CmdOutputFileRenderer
   stogger.core.MultiRenderer
   stogger.core.MultiOptimisticLoggerFactory
   stogger.core.MultiOptimisticLogger


Functions
---------

.. autoapisummary::

   stogger.core.prefix
   stogger.core.add_pid
   stogger.core.add_caller_info
   stogger.core.process_exc_info
   stogger.core.format_exc_info
   stogger.core.log_to_stdlib
   stogger.core.init_logging
   stogger.core.init_early_logging
   stogger.core.init_command_logging
   stogger.core.drop_cmd_output_logfile
   stogger.core.logging_initialized


Module Contents
---------------

.. py:data:: log

.. py:class:: PartialFormatter(missing='<missing>', bad_format='<bad format>')

   Bases: :py:obj:`string.Formatter`


   .. py:attribute:: missing
      :value: '<missing>'



   .. py:attribute:: bad_format
      :value: '<bad format>'



   .. py:method:: get_field(field_name, args, kwargs)


   .. py:method:: format_field(value, format_spec)


.. py:class:: TranslationProcessor(translations)

   .. py:attribute:: translations


   .. py:attribute:: formatter


.. py:function:: prefix(name, s)

   Add a prefix to each line of a multi-line string.


.. py:class:: ConsoleFileRenderer(format_config=None, min_level=None, show_caller_info=None)

   Render `event_dict` nicely aligned, in colors, and ordered with
   specific knowledge about stogger structures.


   .. py:attribute:: LEVELS
      :type:  ClassVar[list[str]]
      :value: ['alert', 'critical', 'error', 'exception', 'warn', 'warning', 'info', 'debug', 'trace']



   .. py:attribute:: format_config
      :value: None



   .. py:attribute:: min_level


   .. py:attribute:: show_caller_info


   .. py:attribute:: pad_event


   .. py:attribute:: show_logger_brackets
      :value: False



   .. py:attribute:: show_pid
      :value: False



   .. py:attribute:: timestamp_format


.. py:class:: JSONRenderer(min_level='info')

   JSON renderer for structured logging output.


   .. py:attribute:: min_level_idx


.. py:function:: add_pid(_, __, event_dict)

.. py:function:: add_caller_info(_, __, event_dict)

.. py:function:: process_exc_info(_, __, event_dict)

.. py:function:: format_exc_info(_logger, _name, event_dict)

   Renders exc_info if it's present.
   Expects the tuple format returned by sys.exc_info().
   Compared to structlog's format_exc_info(), this renders the exception
   information separately which is better for structured logging targets.


.. py:class:: SelectRenderedString(key = 'console')

   Processor that selects a string from the dict returned by ConsoleFileRenderer.

   This ensures that structlog.stdlib.ProcessorFormatter receives a string
   as required, avoiding RuntimeWarnings.


   .. py:attribute:: key
      :value: 'console'



.. py:function:: log_to_stdlib(_logger, _name, event_dict)

   Bridge structlog events to Python's standard library logging module.

   This processor forwards every structlog event to ``logging.log()`` so that
   tools relying on stdlib handlers (e.g. ``pytest caplog``) can capture them.

   **Do NOT add this to the default processor pipeline.** Stogger configures
   its own renderers and file handlers. Adding this processor causes every
   event to appear twice — once via stogger's ``MultiRenderer`` and once via
   the stdlib root logger.

   Use cases where this *is* useful:

   - Legacy code that reads from stdlib ``logging`` handlers
   - Ad-hoc debugging with ``logging.basicConfig()``

   For test assertions, prefer ``pytest-structlog`` which captures events
   directly from the structlog pipeline without needing a stdlib bridge.

   Args:
       _logger: The structlog logger (unused).
       _name: The log method name (unused).
       event_dict: The structured event dictionary.

   Returns:
       The unmodified ``event_dict`` (pass-through processor).



.. py:function:: init_logging(*, logdir = None, log_cmd_output = False, log_to_console = True, syslog_identifier = 'stogger', verbose = None, show_caller_info = None)

   Initialize full structured logging with console, file, and journal targets.

   Configures structlog with a multi-target rendering pipeline: systemd journal,
   optional command output file, and a colorized console/file renderer. Sets up
   processors for PID, log level, exception formatting, timestamps, and caller info.

   Args:
       logdir: Directory for log files. A ``{syslog_identifier}.log`` file is created
           here when writable. Required if ``log_cmd_output`` is True.
       log_cmd_output: Enable separate command output logging to a dedicated file
           in ``logdir``. Requires ``logdir`` to be set.
       log_to_console: Log to stderr. Disabled automatically when running under
           systemd journal (detected via ``JOURNAL_STREAM`` env var).
       syslog_identifier: Identifier string for syslog/journal entries. Also used
           as the main log file name (``{syslog_identifier}.log``).
       verbose: When True, sets the console log level to ``"debug"``.
           When None (default), uses the level from settings (typically ``"info"``).
       show_caller_info: Whether to display code location (file, function, line)
           in console output. When None (default), uses the setting from
           ``FormatConfig.show_code_info``.

   Raises:
       ValueError: If ``log_cmd_output`` is True but ``logdir`` is not set.



.. py:function:: init_early_logging()

   Initialize minimal structured logging before full setup.

   Configures a lightweight structlog pipeline (timestamp, level, console renderer)
   so that early startup messages are properly formatted instead of appearing as
   raw dicts. No-op if structlog is already configured. Errors during setup are
   suppressed silently to avoid crashing during early initialization.


.. py:class:: JournalLoggerFactory

   Stub factory for systemd journal logger integration.

   Returns ``None`` by default. Actual systemd journal support is provided by
   the ``stogger-systemd`` package, which replaces this factory with a real
   journal writer. Use this as a placeholder so logging pipelines work without
   the systemd extra installed.


.. py:data:: JOURNAL_LEVELS

.. py:data:: KEYS_TO_SKIP_IN_JOURNAL_MESSAGE
   :value: ['_replace_msg', 'code_file', 'code_func', 'code_lineno', 'code_module', 'event',...


.. py:class:: SystemdJournalRenderer(syslog_identifier, syslog_facility=syslog.LOG_LOCAL0)

   Render structlog events as systemd journal fields.

   Transforms event dicts into journal-compatible key-value pairs with
   uppercased field names, syslog priority/facility, and a human-readable
   message string. Strings are kept un-JSON-encoded to preserve line breaks
   in ``journalctl`` output.

   Args:
       syslog_identifier: Identifier string for SYSLOG_IDENTIFIER field.
       syslog_facility: Syslog facility code (default: ``syslog.LOG_LOCAL0``).



   .. py:attribute:: syslog_identifier


   .. py:attribute:: syslog_facility
      :value: 128



   .. py:method:: handle_json_fallback(obj)

      Same as structlog's json fallback.
      Supports obj.__structlog__() for custom object serialization.



   .. py:method:: dump_for_journal(obj)

      Encode values as JSON, except strings.
      We keep strings unchanged to display line breaks properly in journalctl
      and graylog.



.. py:class:: CmdOutputFileRenderer

   Renderer for command output file logging.


.. py:class:: MultiRenderer(**renderers)

   Calls multiple renderers with a shallow copy of the event dict and collects
   their messages in a dict with the renderer names as keys and their
   rendered output as values. It doesn't care about the rendered messages
   so different logger types can get different types of messages.
   Normally, this should be placed last in the processors chain.
   Errors in renderers are ignored silently.


   .. py:attribute:: renderers


.. py:class:: MultiOptimisticLoggerFactory(context, factories)

   Factory that creates ``MultiOptimisticLogger`` instances.

   Holds shared context (e.g. ``logdir``) and a dict of sub-logger factories
   (e.g. ``"console"`` → ``PrintLoggerFactory``, ``"file"`` → ``PrintLoggerFactory``).
   Each factory is called once per ``MultiOptimisticLogger`` instantiation.

   Args:
       context: Shared context dict available to all created loggers.
       factories: Dict mapping target names to structlog logger factory callables.



   .. py:attribute:: context


   .. py:attribute:: factories


.. py:class:: MultiOptimisticLogger(loggers)

   Distribute log messages to multiple sub-loggers by target name.

   Receives a dict of rendered outputs keyed by target name (e.g. ``"console"``,
   ``"file"``, ``"journal"``) and dispatches each to the corresponding
   sub-logger. Targets not present in the message are skipped. Errors in
   individual sub-loggers are caught and reported to stdlib logging to prevent
   one failing target from affecting others.

   Args:
       loggers: Dict mapping target names to structlog logger instances.



   .. py:attribute:: loggers


   .. py:method:: msg(**messages)


.. py:function:: init_command_logging(log, logdir=None)

   Add a command output file logger to the active multi-logger factory.

   Opens (or overwrites) a dedicated log file for capturing subprocess command
   output separately from the main log. When running under systemd (detected
   via ``INVOCATION_ID`` env var), the filename includes a timestamp and
   invocation ID for uniqueness.

   Args:
       log: A structlog BoundLogger instance (typically from ``structlog.get_logger()``).
       logdir: Directory for the command output file. Falls back to the
           ``logdir`` stored in the current ``MultiOptimisticLoggerFactory`` context.



.. py:function:: drop_cmd_output_logfile(log)

   Close and delete the command output log file.

   Removes the file created by ``init_command_logging``. Use this when no
   meaningful command output was produced to avoid leaving empty log files.

   Args:
       log: A structlog BoundLogger instance for diagnostic messages.

   Raises:
       KeyError: If the ``cmd_output_file`` factory is not present in the
           active ``MultiOptimisticLoggerFactory`` (i.e. ``init_command_logging``
           was never called).



.. py:function:: logging_initialized()

   Check whether structured logging has been configured.

   Returns:
       True if ``init_logging`` or ``init_early_logging`` has been called
       successfully, False otherwise.



