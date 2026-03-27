nicestlog.log_statement_analyzer
================================

.. py:module:: nicestlog.log_statement_analyzer

.. autoapi-nested-parse::

   AST-based log statement analyzer for nicestlog.

   Analyzes log statements to detect common issues and patterns.



Classes
-------

.. autoapisummary::

   nicestlog.log_statement_analyzer.LogStatementOptions
   nicestlog.log_statement_analyzer.LogStatement
   nicestlog.log_statement_analyzer.LogAnalysisResult
   nicestlog.log_statement_analyzer.LogStatementAnalyzer


Functions
---------

.. autoapisummary::

   nicestlog.log_statement_analyzer.analyze_file
   nicestlog.log_statement_analyzer.print_analysis_summary


Module Contents
---------------

.. py:class:: LogStatementOptions

   Options for log statement analysis.


   .. py:attribute:: method
      :type:  str


   .. py:attribute:: args
      :type:  list[str]


   .. py:attribute:: kwargs
      :type:  dict[str, str]


   .. py:attribute:: magic_args
      :type:  set[str]


   .. py:attribute:: event_id
      :type:  str | None


   .. py:attribute:: event_id_format
      :type:  str


   .. py:attribute:: prefer_dash_case
      :type:  bool
      :value: True



.. py:class:: LogStatement

   Represents a parsed log statement.


   .. py:attribute:: line_number
      :type:  int


   .. py:attribute:: method
      :type:  str


   .. py:attribute:: event_id
      :type:  str | None


   .. py:attribute:: has_event_id
      :type:  bool


   .. py:attribute:: event_id_format
      :type:  str


   .. py:attribute:: arguments
      :type:  list[str]


   .. py:attribute:: keyword_args
      :type:  dict[str, str]


   .. py:attribute:: magic_args
      :type:  set[str]


   .. py:attribute:: raw_call
      :type:  str


   .. py:attribute:: issues
      :type:  list[str]


.. py:class:: LogAnalysisResult

   Results of analyzing log statements in a file.


   .. py:attribute:: file_path
      :type:  pathlib.Path


   .. py:attribute:: statements
      :type:  list[LogStatement]


   .. py:attribute:: total_statements
      :type:  int


   .. py:attribute:: statements_with_event_id
      :type:  int


   .. py:attribute:: statements_without_event_id
      :type:  int


   .. py:attribute:: dash_case_violations
      :type:  int


   .. py:attribute:: single_string_args
      :type:  int


   .. py:attribute:: magic_args_usage
      :type:  dict[str, int]


.. py:class:: LogStatementAnalyzer(*, prefer_dash_case = True)

   Bases: :py:obj:`ast.NodeVisitor`


   AST visitor that analyzes log statements.


   .. py:attribute:: statements
      :type:  list[LogStatement]
      :value: []



   .. py:attribute:: prefer_dash_case
      :value: True



   .. py:attribute:: log_methods


   .. py:attribute:: magic_args


   .. py:attribute:: logging_imports
      :type:  set[str]


   .. py:attribute:: logger_variables
      :type:  set[str]


   .. py:attribute:: logging_modules


   .. py:attribute:: logger_factory_patterns


   .. py:method:: visit_Import(node)

      Track logging module imports.



   .. py:method:: visit_ImportFrom(node)

      Track logging imports from modules.



   .. py:method:: visit_Assign(node)

      Track logger variable assignments.



   .. py:method:: visit_Call(node)

      Visit function calls to detect log statements.



.. py:function:: analyze_file(file_path, *, prefer_dash_case = True)

   Analyze log statements in a Python file.


.. py:function:: print_analysis_summary(result, *, verbose = False)

   Print analysis summary for a file.


