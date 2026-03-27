nicestlog.project_analyzer
==========================

.. py:module:: nicestlog.project_analyzer

.. autoapi-nested-parse::

   🔍 Project Analyzer for AI Agents.

   This module provides automated analysis of existing Python projects to determine
   the best nicestlog migration strategy and identify potential issues.



Attributes
----------

.. autoapisummary::

   nicestlog.project_analyzer.MIN_FILES_SIMPLE
   nicestlog.project_analyzer.MIN_LINES_SIMPLE
   nicestlog.project_analyzer.MIN_FILES_MEDIUM
   nicestlog.project_analyzer.MIN_LINES_MEDIUM
   nicestlog.project_analyzer.MIN_CONFLICTING_FRAMEWORKS
   nicestlog.project_analyzer.MIN_HIGH_PRIORITY
   nicestlog.project_analyzer.MAX_HIGH_PRIORITY_PATTERNS
   nicestlog.project_analyzer.MAX_COMPLEXITY_THRESHOLD
   nicestlog.project_analyzer.log


Classes
-------

.. autoapisummary::

   nicestlog.project_analyzer.LoggingPattern
   nicestlog.project_analyzer.ProjectComplexity
   nicestlog.project_analyzer.DependencyAnalysis
   nicestlog.project_analyzer.MigrationRecommendation
   nicestlog.project_analyzer.ProjectAnalysisResult
   nicestlog.project_analyzer.ProjectAnalyzer


Functions
---------

.. autoapisummary::

   nicestlog.project_analyzer.analyze_project_for_agents


Module Contents
---------------

.. py:data:: MIN_FILES_SIMPLE
   :value: 5


.. py:data:: MIN_LINES_SIMPLE
   :value: 500


.. py:data:: MIN_FILES_MEDIUM
   :value: 20


.. py:data:: MIN_LINES_MEDIUM
   :value: 2000


.. py:data:: MIN_CONFLICTING_FRAMEWORKS
   :value: 2


.. py:data:: MIN_HIGH_PRIORITY
   :value: 8


.. py:data:: MAX_HIGH_PRIORITY_PATTERNS
   :value: 50


.. py:data:: MAX_COMPLEXITY_THRESHOLD
   :value: 20


.. py:data:: log

.. py:class:: LoggingPattern

   Represents a detected logging pattern in the codebase.


   .. py:attribute:: pattern_type
      :type:  str


   .. py:attribute:: file_path
      :type:  str


   .. py:attribute:: line_number
      :type:  int


   .. py:attribute:: code_snippet
      :type:  str


   .. py:attribute:: severity
      :type:  str


   .. py:attribute:: migration_priority
      :type:  int


.. py:class:: ProjectComplexity

   Project complexity metrics.


   .. py:attribute:: total_files
      :type:  int


   .. py:attribute:: python_files
      :type:  int


   .. py:attribute:: total_lines
      :type:  int


   .. py:attribute:: average_complexity
      :type:  float


   .. py:attribute:: max_complexity
      :type:  float


   .. py:attribute:: complexity_category
      :type:  str


.. py:class:: DependencyAnalysis

   Analysis of project dependencies related to logging.


   .. py:attribute:: has_logging
      :type:  bool


   .. py:attribute:: has_structlog
      :type:  bool


   .. py:attribute:: has_other_logging
      :type:  list[str]


   .. py:attribute:: dependency_conflicts
      :type:  list[str]


   .. py:attribute:: package_manager
      :type:  str


.. py:class:: MigrationRecommendation

   Recommended migration strategy for the project.


   .. py:attribute:: strategy
      :type:  str


   .. py:attribute:: priority
      :type:  str


   .. py:attribute:: estimated_effort
      :type:  str


   .. py:attribute:: recommended_approach
      :type:  str


   .. py:attribute:: risk_level
      :type:  str


   .. py:attribute:: prerequisites
      :type:  list[str]


   .. py:attribute:: steps
      :type:  list[str]


.. py:class:: ProjectAnalysisResult

   Complete analysis result for a project.


   .. py:attribute:: project_path
      :type:  str


   .. py:attribute:: analysis_timestamp
      :type:  str


   .. py:attribute:: logging_patterns
      :type:  list[LoggingPattern]


   .. py:attribute:: complexity
      :type:  ProjectComplexity


   .. py:attribute:: dependencies
      :type:  DependencyAnalysis


   .. py:attribute:: recommendation
      :type:  MigrationRecommendation


   .. py:attribute:: warnings
      :type:  list[str]


   .. py:method:: to_dict()

      Convert to dictionary for JSON serialization.



   .. py:method:: to_json()

      Convert to JSON string.



.. py:class:: ProjectAnalyzer(*, verbose = False)

   Analyzes Python projects for nicestlog migration opportunities.


   .. py:attribute:: verbose
      :value: False



   .. py:attribute:: log


   .. py:attribute:: print_patterns
      :value: ['print\\s*\\(', 'sys\\.stdout\\.write', 'sys\\.stderr\\.write']



   .. py:attribute:: logging_patterns
      :value: ['logging\\.', 'logger\\.', 'log\\.', 'getLogger']



   .. py:attribute:: structlog_patterns
      :value: ['structlog\\.', 'get_logger', 'bind\\(']



   .. py:attribute:: cli_output_patterns
      :value: ['typer\\.echo\\s*\\(', 'click\\.echo\\s*\\(', 'rich\\.print\\s*\\(', 'console\\.print\\s*\\(',...



   .. py:attribute:: wrapper_patterns
      :value: ['def\\s+\\w*log\\w*\\s*\\(', 'def\\s+write_\\w+\\s*\\(', 'def\\s+emit_\\w+\\s*\\(']



   .. py:attribute:: logging_libraries


   .. py:attribute:: default_ignore_patterns


   .. py:method:: analyze_project(project_path)

      Perform comprehensive analysis of a Python project.



.. py:function:: analyze_project_for_agents(project_path, *, verbose = False)

   Convenience function for AI agents to analyze a project.

   Args:
       project_path: Path to the project to analyze
       verbose: Enable verbose logging

   Returns:
       ProjectAnalysisResult with comprehensive analysis



