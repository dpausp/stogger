stogger.config
==============

.. py:module:: stogger.config

.. autoapi-nested-parse::

   Configuration handling for stogger.



Classes
-------

.. autoapisummary::

   stogger.config.ProjectStructure
   stogger.config.StoggerConfig
   stogger.config.SimpleFormatSettings


Functions
---------

.. autoapisummary::

   stogger.config.detect_project_structure


Module Contents
---------------

.. py:class:: ProjectStructure

   Detected project layout used for source and test discovery.

   Attributes:
       source_dirs: Relative paths to source directories (e.g. ``["src"]``).
       test_dirs: Relative paths to test directories (e.g. ``["tests"]``).
       exclude_patterns: Glob patterns for files excluded from logging analysis.
       detection_source: How the structure was determined — ``"pyproject.toml"``,
           ``"heuristics"``, or ``"defaults"``.
       project_root: Absolute path to the project root directory.



   .. py:attribute:: source_dirs
      :type:  list[str]


   .. py:attribute:: exclude_patterns
      :type:  list[str]


   .. py:attribute:: detection_source
      :type:  str


   .. py:attribute:: project_root
      :type:  pathlib.Path


   .. py:method:: get_source_paths()

      Resolve source directories to absolute paths.

      Returns:
          List of absolute Paths joining ``project_root`` with each
          entry in ``source_dirs``.




   .. py:method:: should_exclude_from_logging_analysis(file_path)

      Check whether a file should be excluded from logging analysis.

      Files inside ``test_dirs`` or matching any ``exclude_patterns`` glob are
      excluded. Files outside ``project_root`` are always excluded.

      Args:
          file_path: Absolute path to the file to check.

      Returns:
          ``True`` if the file should be excluded.




.. py:class:: StoggerConfig(**kwargs)

   Central configuration for stogger, merged from ``[tool.stogger]`` in
   ``pyproject.toml`` and keyword arguments passed at construction.

   Key attributes (with defaults):

   Attributes:
       verbose (bool): Enable verbose output. Default ``False``.
       logdir (Path | None): Directory for log files. Default ``None``.
       log_cmd_output (bool): Log subprocess command output. Default ``False``.
       log_to_console (bool): Also log to the console. Default ``True``.
       syslog_identifier (str): Identifier for syslog/systemd journal.
           Default ``"stogger"``.
       show_caller_info (bool): Include caller file/line in log output.
           Default ``False``.
       translation_dir (Path | None): Directory containing message
           translations. Default ``None``.
       language (str): Language code for log messages. Default ``"en"``.
       log_format (str): Output format — ``"simple"`` or ``"json"``.
           Default ``"simple"``.
       async_logging (bool): Use asynchronous log writing. Default ``False``.
       enable_pii_scrubbing (bool): Scrub PII from log messages.
           Default ``True``.
       pii_redaction_text (str): Replacement text for redacted PII.
           Default ``"[REDACTED]"``.
       enable_systemd (bool): Enable systemd/journal integration.
           Default ``True``.
       systemd_facility (str | None): Syslog facility for systemd output.
           Default ``None``.
       src_dir (str): Primary source directory name. Default ``"src"``.
       ast_respect_gitignore (bool): Honor ``.gitignore`` during AST
           analysis. Default ``True``.
       ast_max_parameters (int): Max parameters before flagging a function.
           Default ``8``.
       ast_logging_focus (bool): Focus AST analysis on logging patterns.
           Default ``True``.
       ast_enabled_patterns (list | None): Specific AST patterns to enable.
           ``None`` enables all. Default ``None``.



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


.. py:function:: detect_project_structure(project_root = None)

   Detect project structure using smart heuristics.

   Args:
       project_root: Project root directory. If None, uses current working directory.

   Returns:
       ProjectStructure with detected information.

   Raises:
       ValueError: If project structure cannot be determined and user configuration is required.



.. py:class:: SimpleFormatSettings

   Configuration for the simple console log renderer.

   Attributes:
       min_level: Minimum log level to display. Default ``"info"``.
       show_logger_brackets: Wrap logger name in brackets. Default ``False``.
       show_pid: Include process ID in output. Default ``False``.
       show_code_info: Include file name and line number. Default ``False``.
       timestamp_format: Timestamp style — ``"iso"`` or ``"relative"``.
           Default ``"iso"``.
       pad_event_width: Minimum width for the event column. Default ``30``.



   .. py:attribute:: min_level
      :type:  str
      :value: 'info'



   .. py:attribute:: show_logger_brackets
      :type:  bool
      :value: False



   .. py:attribute:: show_pid
      :type:  bool
      :value: False



   .. py:attribute:: show_code_info
      :type:  bool
      :value: False



   .. py:attribute:: timestamp_format
      :type:  str
      :value: 'iso'



   .. py:attribute:: pad_event_width
      :type:  int
      :value: 30



