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

   Detected project structure information.


   .. py:attribute:: source_dirs
      :type:  list[str]


   .. py:attribute:: exclude_patterns
      :type:  list[str]


   .. py:attribute:: detection_source
      :type:  str


   .. py:attribute:: project_root
      :type:  pathlib.Path


   .. py:method:: get_source_paths()

      Get absolute paths for source directories.



   .. py:method:: should_exclude_from_logging_analysis(file_path)

      Check if a file should be excluded from logging analysis.



.. py:class:: StoggerConfig(**kwargs)

   Manages stogger configuration by merging pyproject.toml settings
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


.. py:function:: detect_project_structure(project_root = None)

   Detect project structure using smart heuristics.

   Args:
       project_root: Project root directory. If None, uses current working directory.

   Returns:
       ProjectStructure with detected information.

   Raises:
       ValueError: If project structure cannot be determined and user configuration is required.



.. py:class:: SimpleFormatSettings

   Settings for simple console formatting.

   This class provides a way to configure the ConsoleFileRenderer with common formatting options.


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



