nicestlog
=========

.. py:module:: nicestlog

.. autoapi-nested-parse::

   Advanced structured logging for Python applications.

   This package provides advanced logging capabilities with structured data,
   multiple output formats, and integrations for various logging backends.

   Modules:
       core: Core logging functionality and initialization
       factory: Factory functions for building log processors
       config: Configuration management
       assistant: Tools for migrating print statements to structured logging
       log_reviewer: Log quality analysis and review
       systemd_integration: Systemd journal integration
       web_dashboard: Web-based log viewing dashboard
       eliot_integration: Integration with Eliot logging
       pii_scrubber: PII (Personally Identifiable Information) scrubbing
       i18n: Internationalization support
       interactive_transformer: Interactive code transformation tools
       journal_viewer: Systemd journal viewer
       linter: Log statement analysis and linting
       live_editor: Live code editing tools
       log_statement_analyzer: Analysis of log statements
       advanced_assistant: Advanced AST-based transformation assistant
       cli: Command-line interface

   Functions:
       init_logging: Initialize the logging system
       logging_initialized: Check if logging is configured
       init_early_logging: Initialize minimal logging early in application startup
       init_command_logging: Set up command output logging
       drop_cmd_output_logfile: Remove command output log file



Submodules
----------

.. toctree::
   :maxdepth: 1

   /api/nicestlog/advanced_assistant/index
   /api/nicestlog/assistant/index
   /api/nicestlog/cli/index
   /api/nicestlog/cli_output_transformer/index
   /api/nicestlog/config/index
   /api/nicestlog/core/index
   /api/nicestlog/eliot_integration/index
   /api/nicestlog/factory/index
   /api/nicestlog/gitignore_utils/index
   /api/nicestlog/i18n/index
   /api/nicestlog/i18n_check/index
   /api/nicestlog/interactive_transformer/index
   /api/nicestlog/journal_viewer/index
   /api/nicestlog/linter/index
   /api/nicestlog/live_editor/index
   /api/nicestlog/log_reviewer/index
   /api/nicestlog/log_statement_analyzer/index
   /api/nicestlog/pii_scrubber/index
   /api/nicestlog/project_analyzer/index
   /api/nicestlog/systemd_integration/index
   /api/nicestlog/web_dashboard/index


Classes
-------

.. autoapisummary::

   nicestlog.NicestLogConfig
   nicestlog.JournalLogger
   nicestlog.JournalLoggerFactory
   nicestlog.MultiOptimisticLogger
   nicestlog.MultiOptimisticLoggerFactory
   nicestlog.SystemdJournalRenderer


Functions
---------

.. autoapisummary::

   nicestlog.analyze_python_file
   nicestlog.create_advanced_assistant
   nicestlog.transform_python_file
   nicestlog.migrate_directory
   nicestlog.main
   nicestlog.drop_cmd_output_logfile
   nicestlog.init_command_logging
   nicestlog.init_early_logging
   nicestlog.init_logging
   nicestlog.logging_initialized
   nicestlog.setup_eliot_logging
   nicestlog.arsch
   nicestlog.get_translator
   nicestlog.init_i18n
   nicestlog.leiwand
   nicestlog.oida
   nicestlog.t
   nicestlog.create_interactive_transformer
   nicestlog.transform_directory_interactive
   nicestlog.transform_file_interactive
   nicestlog.create_live_editor
   nicestlog.edit_code_live
   nicestlog.create_pii_processor
   nicestlog.demo_pii_scrubbing
   nicestlog.create_systemd_service_file
   nicestlog.demo_systemd_integration
   nicestlog.setup_systemd_logging
   nicestlog.get_log_stats
   nicestlog.run_dashboard
   nicestlog.setup_web_logging


Package Contents
----------------

.. py:function:: analyze_python_file(file_path)

   Quick analysis of a Python file.


.. py:function:: create_advanced_assistant(verbose = True)

   Create a new Advanced Assistant instance.


.. py:function:: transform_python_file(file_path, dry_run = True)

   Quick transformation of a Python file.


.. py:function:: migrate_directory(input_dir, output_dir, *, dry_run = True)

   Migrate Python files under input_dir. Writes to output_dir if provided, else in-place.


.. py:function:: main()

   Main entry point.


.. py:class:: NicestLogConfig(**kwargs)

   Manages nicestlog configuration by merging pyproject.toml settings
   with keyword arguments.


   .. py:attribute:: verbose
      :type:  bool


   .. py:attribute:: logdir
      :type:  pathlib.Path | None


   .. py:attribute:: log_cmd_output
      :type:  bool


   .. py:attribute:: log_to_console
      :type:  bool


   .. py:attribute:: syslog_identifier
      :type:  str


   .. py:attribute:: show_caller_info
      :type:  bool


   .. py:attribute:: translation_dir
      :type:  pathlib.Path | None


   .. py:attribute:: language
      :type:  str


   .. py:attribute:: log_format
      :type:  str


   .. py:attribute:: async_logging
      :type:  bool


   .. py:attribute:: enable_pii_scrubbing
      :type:  bool


   .. py:attribute:: pii_redaction_text
      :type:  str


   .. py:attribute:: enable_systemd
      :type:  bool


   .. py:attribute:: systemd_facility
      :type:  str | None


   .. py:attribute:: src_dir
      :type:  str


   .. py:attribute:: ast_respect_gitignore
      :type:  bool


   .. py:attribute:: ast_max_parameters
      :type:  int


   .. py:attribute:: ast_logging_focus
      :type:  bool


   .. py:attribute:: ast_enabled_patterns
      :type:  list | None


.. py:class:: JournalLogger

   Logger that sends messages to systemd journal.


   .. py:method:: msg(message)


.. py:class:: JournalLoggerFactory

   Factory for creating journal loggers.


.. py:class:: MultiOptimisticLogger(loggers)

   A logger which distributes messages to multiple loggers.
   It's initialized with a logger dict where the keys are the logger names
   which correspond to the keyword arguments given to the msg method.
   If the logger's name is not present in the arguments, the logger is skipped.
   Errors in sub loggers are ignored silently.


   .. py:attribute:: loggers


   .. py:method:: msg(**messages)


.. py:class:: MultiOptimisticLoggerFactory(context, factories)

   A logger factory that creates MultiOptimisticLogger instances.
   Stores context and sub-logger factories.


   .. py:attribute:: context


   .. py:attribute:: factories


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



.. py:function:: drop_cmd_output_logfile(log)

   Deletes the log file used by the cmd_output_file logger.
   Used to throw away the command log file if nothing interesting has
   happened.


.. py:function:: init_command_logging(log, logdir=None)

   Adds a cmd_output_file logger factory to an already configured
   MultiOptimisticLoggerFactory, used for logging Nix command output to a
   separate file.
   Overwrites existing log files. If called from a systemd unit, the file
   name will be made unique by adding the time and systemd invocation ID.

   Other factory types are ignored.


.. py:function:: init_early_logging()

   Initialize minimal logging format early to reduce uninitialized structlog messages.

   This sets up a basic structlog configuration with minimal dependencies
   to avoid the block of uninitialized messages at startup. Falls back
   gracefully if initialization fails.


.. py:function:: init_logging(*args, **kwargs)

   Initialize logging with the new reference-style signature.

   New signature (reference-style):
       init_logging(verbose, logdir=None, log_cmd_output=False, log_to_console=True,
                    syslog_identifier="nicestlog", show_caller_info=False)


.. py:function:: logging_initialized()

.. py:function:: setup_eliot_logging(*, destination = None, human_readable = True, show_timestamps = True, show_task_ids = False)

   Setup Eliot logging with nicestlog integration.

   Args:
       destination: Where to write logs (default: stdout)
       human_readable: Use human-readable format instead of JSON
       show_timestamps: Include timestamps in output
       show_task_ids: Show Eliot task IDs (useful for debugging)

   Returns:
       True if Eliot was successfully configured, False if not available



.. py:function:: arsch(message)

   Austrian way to say something is bad.


.. py:function:: get_translator()

   Get current translator instance.


.. py:function:: init_i18n(language = 'en')

   Initialize internationalization.


.. py:function:: leiwand(message)

   Make any message sound Austrian-positive.


.. py:function:: oida(message)

   Add Austrian flair to any message.


.. py:function:: t(key, section = 'general', **kwargs)

   Shorthand for translation.

   Usage:
       t("success")  # -> "Success!"
       t("file_not_found", "errors", filename="test.log")  # -> "File test.log not found!"


.. py:function:: create_interactive_transformer(context_lines = 3)

   Create a new Interactive Transformer instance.


.. py:function:: transform_directory_interactive(directory, pattern = '*.py', context_lines = 3)

   Quick interactive transformation of a directory.


.. py:function:: transform_file_interactive(file_path, context_lines = 3)

   Quick interactive transformation of a Python file.


.. py:function:: create_live_editor(*, use_external_editor = False)

   Create a new Live Code Editor instance.


.. py:function:: edit_code_live(original_code, suggested_code, pattern_name, file_path, line_number)

   Quick live editing of a code transformation.


.. py:function:: create_pii_processor(custom_patterns = None, sensitive_fields = None, redaction_text = '[REDACTED]')

   Create a PII scrubber processor for structlog.


.. py:function:: demo_pii_scrubbing()

   Demonstrate PII scrubbing capabilities.


.. py:function:: create_systemd_service_file(config)

   Generate a systemd service file with proper logging configuration.

   Args:
       config: Service configuration parameters

   Returns:
       Service file content as string



.. py:function:: demo_systemd_integration()

   Demonstrate systemd integration features.


.. py:function:: setup_systemd_logging(identifier = None, facility = None)

   Set up systemd journal logging integration.

   This function prefers the detected runtime environment to decide whether to
   enable systemd logging. If a systemd environment is detected, it will attach
   a SystemdJournalHandler even when the systemd-python package is not
   available; in that case, the handler acts as a no-op but preserves the
   processor chain shape. If no systemd environment is detected, the function
   returns False.

   Args:
       identifier: SYSLOG_IDENTIFIER for journal entries
       facility: SYSLOG_FACILITY
       structured_fields: Whether to include structured data as journal fields

   Returns:
       True if systemd logging was successfully configured, otherwise False



.. py:function:: get_log_stats()

   Calculate log statistics.


.. py:function:: run_dashboard(host='127.0.0.1', port=8080, *, debug=False)

   Run the web dashboard.


.. py:function:: setup_web_logging()

   Set up web logging integration.


