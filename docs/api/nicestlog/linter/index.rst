nicestlog.linter
================

.. py:module:: nicestlog.linter

.. autoapi-nested-parse::

   Logging Linter - Ensures proper logging coverage in your codebase.

   Like a politeness compiler, but for log statements!



Attributes
----------

.. autoapisummary::

   nicestlog.linter.log
   nicestlog.linter.SINGLE_LOGGING_CALL
   nicestlog.linter.MAX_BODY_STATEMENTS_FOR_PASSTHROUGH


Classes
-------

.. autoapisummary::

   nicestlog.linter.LintOptions
   nicestlog.linter.LoggingStats
   nicestlog.linter.LoggingLevelIssue
   nicestlog.linter.LoggingVisitor


Functions
---------

.. autoapisummary::

   nicestlog.linter.analyze_file
   nicestlog.linter.check_logging_quality
   nicestlog.linter.lint_directory


Module Contents
---------------

.. py:class:: LintOptions

   Options for linting operations.


   .. py:attribute:: min_coverage
      :type:  float
      :value: 5.0



   .. py:attribute:: max_coverage
      :type:  float
      :value: 15.0



   .. py:attribute:: analyze_statements
      :type:  bool
      :value: False



   .. py:attribute:: verbose
      :type:  bool
      :value: False



   .. py:attribute:: allow_snake_case
      :type:  bool
      :value: False



   .. py:attribute:: project_structure
      :type:  Any
      :value: None



.. py:data:: log

.. py:data:: SINGLE_LOGGING_CALL
   :value: 1


.. py:data:: MAX_BODY_STATEMENTS_FOR_PASSTHROUGH
   :value: 3


.. py:class:: LoggingStats

   Statistics about logging in a file.


   .. py:attribute:: total_lines
      :type:  int


   .. py:attribute:: code_lines
      :type:  int


   .. py:attribute:: log_statements
      :type:  int


   .. py:attribute:: functions
      :type:  int


   .. py:attribute:: functions_with_logging
      :type:  int


   .. py:attribute:: log_coverage_percent
      :type:  float


   .. py:attribute:: function_coverage_percent
      :type:  float


.. py:class:: LoggingLevelIssue

   Represents a logging level issue or related logging suggestion.


   .. py:attribute:: line_no
      :type:  int


   .. py:attribute:: current_level
      :type:  str


   .. py:attribute:: suggested_level
      :type:  str


   .. py:attribute:: event_name
      :type:  str


   .. py:attribute:: reason
      :type:  str


   .. py:attribute:: severity
      :type:  str
      :value: 'warning'



   .. py:attribute:: category
      :type:  str
      :value: 'level'



.. py:class:: LoggingVisitor(source_lines = None)

   Bases: :py:obj:`ast.NodeVisitor`


   AST visitor to analyze logging patterns.


   .. py:attribute:: log_statements
      :value: 0



   .. py:attribute:: functions
      :value: 0



   .. py:attribute:: functions_with_logging
      :value: 0



   .. py:attribute:: current_function_has_logs
      :value: False



   .. py:attribute:: source_lines
      :value: []



   .. py:attribute:: level_issues
      :type:  list[LoggingLevelIssue]
      :value: []



   .. py:attribute:: log_patterns


   .. py:method:: visit_FunctionDef(node)

      Visit function definitions.



   .. py:method:: visit_Try(node)


   .. py:method:: visit_Call(node)

      Visit function calls to detect logging.



.. py:function:: analyze_file(file_path)

   Analyze a Python file for logging coverage.


.. py:function:: check_logging_quality(stats, min_coverage = 5.0, max_coverage = 15.0)

   Check if logging coverage is appropriate.


.. py:function:: lint_directory(directory, options_or_min_coverage=None, **kwargs)

   Lint all Python files in a directory and its subdirectories.

   Uses smart project structure detection to exclude tests from logging analysis.


