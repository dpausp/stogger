stogger.config
==============

.. py:module:: stogger.config

.. autoapi-nested-parse::

   Configuration handling for stogger.



Classes
-------

.. autoapisummary::

   stogger.config.ProjectStructure
   stogger.config.FormatConfig
   stogger.config.StoggerConfig


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
       detection_source: ``"pyproject.toml"``, ``"heuristics"``, or ``"defaults"``.
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




.. py:class:: FormatConfig

   Configuration for log format settings, loaded from ``[tool.stogger.format]``.

   Attributes:
       timestamp_precision: ``"iso"``, ``"iso_seconds"``, ``"iso_no_z"``, or ``"relative"``.
       min_level: Minimum log level to display. Default ``"info"``.
       show_code_info: Include file name and line number. Default ``False``.
       pad_event_width: Minimum width for the event column. Default ``30``.



   .. py:attribute:: timestamp_precision
      :type:  str
      :value: 'iso_seconds'



   .. py:attribute:: min_level
      :type:  str
      :value: 'info'



   .. py:attribute:: show_code_info
      :type:  bool
      :value: False



   .. py:attribute:: pad_event_width
      :type:  int
      :value: 30



.. py:class:: StoggerConfig(**kwargs)

   Central configuration for stogger, merged from ``[tool.stogger]`` in
   ``pyproject.toml`` and keyword arguments passed at construction.

   Key attributes (with defaults):

   Attributes:
       verbose (bool): Enable verbose output. Default ``False``.
       logdir (Path | None): Directory for log files. Default ``None``.
       log_cmd_output (bool): Log subprocess command output. Default ``False``.
       log_to_console (bool): Also log to the console. Default ``True``.
       syslog_identifier (str): Identifier for syslog/systemd journal. Default ``"stogger"``.
       show_caller_info (bool): Include caller file/line in log output. Default ``False``.
       translation_dir (Path | None): Directory containing message translations. Default ``None``.
       language (str): Language code for log messages. Default ``"en"``.
       log_format (str): Output format — ``"simple"`` or ``"json"``. Default ``"simple"``.
       async_logging (bool): Use asynchronous log writing. Default ``False``.
       enable_systemd (bool): Enable systemd/journal integration. Default ``True``.
       systemd_facility (str | None): Syslog facility for systemd output. Default ``None``.
       src_dir (str): Primary source directory name. Default ``"src"``.
       format (FormatConfig): Format configuration. Default ``FormatConfig()``.
       ast_respect_gitignore (bool): Honor ``.gitignore`` during AST analysis. Default ``True``.
       ast_max_parameters (int): Max parameters before flagging a function. Default ``8``.
       ast_logging_focus (bool): Focus AST analysis on logging patterns. Default ``True``.
       ast_enabled_patterns (list | None): Specific AST patterns to enable. Default ``None``.



   .. py:attribute:: verbose
      :type:  bool
      :value: False



   .. py:attribute:: logdir
      :type:  pathlib.Path | None
      :value: None



   .. py:attribute:: log_cmd_output
      :type:  bool
      :value: False



   .. py:attribute:: log_to_console
      :type:  bool
      :value: True



   .. py:attribute:: syslog_identifier
      :type:  str
      :value: 'stogger'



   .. py:attribute:: show_caller_info
      :type:  bool
      :value: False



   .. py:attribute:: translation_dir
      :type:  pathlib.Path | None
      :value: None



   .. py:attribute:: language
      :type:  str
      :value: 'en'



   .. py:attribute:: log_format
      :type:  str
      :value: 'simple'



   .. py:attribute:: async_logging
      :type:  bool
      :value: False



   .. py:attribute:: enable_systemd
      :type:  bool
      :value: True



   .. py:attribute:: systemd_facility
      :type:  str | None
      :value: None



   .. py:attribute:: enable_postgres
      :type:  bool
      :value: False



   .. py:attribute:: postgres_dsn
      :type:  str | None
      :value: None



   .. py:attribute:: postgres_table
      :type:  str
      :value: 'stogger_logs'



   .. py:attribute:: src_dir
      :type:  str
      :value: 'src'



   .. py:attribute:: format
      :type:  FormatConfig


   .. py:attribute:: ast_respect_gitignore
      :type:  bool
      :value: True



   .. py:attribute:: ast_max_parameters
      :type:  int
      :value: 8



   .. py:attribute:: ast_logging_focus
      :type:  bool
      :value: True



   .. py:attribute:: ast_enabled_patterns
      :type:  list | None
      :value: None



.. py:function:: detect_project_structure(project_root = None)

   Detect project structure using smart heuristics.

   Args:
       project_root: Project root directory. If None, uses current working directory.

   Returns:
       ProjectStructure with detected information.

   Raises:
       ValueError: If project structure cannot be determined and user configuration is required.



