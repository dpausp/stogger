nicestlog.core
==============

.. py:module:: nicestlog.core

.. autoapi-nested-parse::

   Core logging functionality for nicestlog.



Attributes
----------

.. autoapisummary::

   nicestlog.core.journal
   nicestlog.core.log
   nicestlog.core.colorama
   nicestlog.core.RESET_ALL
   nicestlog.core.JOURNAL_LEVELS
   nicestlog.core.KEYS_TO_SKIP_IN_JOURNAL_MESSAGE


Classes
-------

.. autoapisummary::

   nicestlog.core.PartialFormatter
   nicestlog.core.TranslationProcessor
   nicestlog.core.ConsoleFileRenderer
   nicestlog.core.JSONRenderer
   nicestlog.core.SelectRenderedString
   nicestlog.core.DummyJournalLogger
   nicestlog.core.JournalLogger
   nicestlog.core.JournalLoggerFactory
   nicestlog.core.SystemdJournalRenderer
   nicestlog.core.CmdOutputFileRenderer
   nicestlog.core.MultiRenderer
   nicestlog.core.MultiOptimisticLoggerFactory
   nicestlog.core.MultiOptimisticLogger


Functions
---------

.. autoapisummary::

   nicestlog.core.prefix
   nicestlog.core.add_pid
   nicestlog.core.add_caller_info
   nicestlog.core.process_exc_info
   nicestlog.core.format_exc_info
   nicestlog.core.log_to_stdlib
   nicestlog.core.init_logging
   nicestlog.core.init_early_logging
   nicestlog.core.init_command_logging
   nicestlog.core.drop_cmd_output_logfile
   nicestlog.core.logging_initialized


Module Contents
---------------

.. py:data:: journal
   :value: None


.. py:data:: log

.. py:data:: colorama
   :value: None


.. py:data:: RESET_ALL
   :value: 0


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


.. py:class:: ConsoleFileRenderer(settings=_default_simple_format_settings, min_level=None, show_caller_info=None)

   Render `event_dict` nicely aligned, in colors, and ordered with
   specific knowledge about fc.agent structures.


   .. py:attribute:: LEVELS
      :type:  ClassVar[list[str]]
      :value: ['alert', 'critical', 'error', 'exception', 'warn', 'warning', 'info', 'debug', 'trace']



   .. py:attribute:: settings


   .. py:attribute:: min_level


   .. py:attribute:: show_caller_info
      :value: False



   .. py:attribute:: pad_event
      :value: 30



   .. py:attribute:: show_logger_brackets
      :value: False



   .. py:attribute:: show_pid
      :value: False



   .. py:attribute:: timestamp_format
      :value: 'iso'



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

   Bridge structlog events to Python's standard logging for test capture.


.. py:function:: init_logging(*args, **kwargs)

   Initialize logging with the new reference-style signature.

   New signature (reference-style):
       init_logging(verbose, logdir=None, log_cmd_output=False, log_to_console=True,
                    syslog_identifier="nicestlog", show_caller_info=False)


.. py:function:: init_early_logging()

   Initialize minimal logging format early to reduce uninitialized structlog messages.

   This sets up a basic structlog configuration with minimal dependencies
   to avoid the block of uninitialized messages at startup. Falls back
   gracefully if initialization fails.


.. py:class:: DummyJournalLogger

   Dummy journal logger when systemd is not available.


   .. py:method:: msg(message)


.. py:class:: JournalLogger

   Logger that sends messages to systemd journal.


   .. py:method:: msg(message)


.. py:class:: JournalLoggerFactory

   Factory for creating journal loggers.


.. py:data:: JOURNAL_LEVELS

.. py:data:: KEYS_TO_SKIP_IN_JOURNAL_MESSAGE
   :value: ['_replace_msg', 'code_file', 'code_func', 'code_lineno', 'code_module', 'event',...


.. py:class:: SystemdJournalRenderer(syslog_identifier, syslog_facility=syslog.LOG_LOCAL0)

   Renderer for systemd journal output.


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

   A logger factory that creates MultiOptimisticLogger instances.
   Stores context and sub-logger factories.


   .. py:attribute:: context


   .. py:attribute:: factories


.. py:class:: MultiOptimisticLogger(loggers)

   A logger which distributes messages to multiple loggers.
   It's initialized with a logger dict where the keys are the logger names
   which correspond to the keyword arguments given to the msg method.
   If the logger's name is not present in the arguments, the logger is skipped.
   Errors in sub loggers are ignored silently.


   .. py:attribute:: loggers


   .. py:method:: msg(**messages)


.. py:function:: init_command_logging(log, logdir=None)

   Adds a cmd_output_file logger factory to an already configured
   MultiOptimisticLoggerFactory, used for logging Nix command output to a
   separate file.
   Overwrites existing log files. If called from a systemd unit, the file
   name will be made unique by adding the time and systemd invocation ID.

   Other factory types are ignored.


.. py:function:: drop_cmd_output_logfile(log)

   Deletes the log file used by the cmd_output_file logger.
   Used to throw away the command log file if nothing interesting has
   happened.


.. py:function:: logging_initialized()

