nicestlog.advanced_assistant
============================

.. py:module:: nicestlog.advanced_assistant

.. autoapi-nested-parse::

   🚀 Advanced AST Assistant - Revolutionary Code Transformation with Comprehensive Logging.

   This module provides sophisticated AST analysis and transformation capabilities with
   extensive logging of every step. Perfect for complex code migrations and refactoring.

   Features:
   - Deep AST analysis with pattern detection
   - Multi-stage transformation pipeline
   - Comprehensive logging of all operations
   - Rollback capabilities
   - Performance metrics
   - Safety checks and validation



Attributes
----------

.. autoapisummary::

   nicestlog.advanced_assistant.log


Classes
-------

.. autoapisummary::

   nicestlog.advanced_assistant.NodeType
   nicestlog.advanced_assistant.ASTPattern
   nicestlog.advanced_assistant.TransformationMetrics
   nicestlog.advanced_assistant.CodeAnalysisResult
   nicestlog.advanced_assistant.TransformationResult
   nicestlog.advanced_assistant.AdvancedASTAnalyzer
   nicestlog.advanced_assistant.AdvancedTransformer
   nicestlog.advanced_assistant.AdvancedAssistant


Functions
---------

.. autoapisummary::

   nicestlog.advanced_assistant.create_advanced_assistant
   nicestlog.advanced_assistant.analyze_python_file
   nicestlog.advanced_assistant.transform_python_file


Module Contents
---------------

.. py:data:: log

.. py:class:: NodeType(*args, **kwds)

   Bases: :py:obj:`enum.Enum`


   Types of AST nodes we can analyze.


   .. py:attribute:: FUNCTION_DEF
      :value: 'function_def'



   .. py:attribute:: CALL
      :value: 'call'



.. py:class:: ASTPattern

   Represents a pattern to match in the AST.


   .. py:attribute:: name
      :type:  str


   .. py:attribute:: description
      :type:  str


   .. py:attribute:: node_type
      :type:  NodeType


   .. py:attribute:: matcher
      :type:  collections.abc.Callable[[ast.AST], bool]


   .. py:attribute:: transformer
      :type:  collections.abc.Callable[[ast.AST], ast.AST] | None
      :value: None



   .. py:attribute:: priority
      :type:  int
      :value: 0



   .. py:attribute:: enabled
      :type:  bool
      :value: True



.. py:class:: TransformationMetrics

   Metrics collected during transformation.


   .. py:attribute:: start_time
      :type:  float


   .. py:attribute:: end_time
      :type:  float | None
      :value: None



   .. py:attribute:: nodes_analyzed
      :type:  int
      :value: 0



   .. py:attribute:: nodes_transformed
      :type:  int
      :value: 0



   .. py:attribute:: patterns_matched
      :type:  dict[str, int]


   .. py:attribute:: errors_encountered
      :type:  list[str]
      :value: []



   .. py:attribute:: warnings_generated
      :type:  list[str]
      :value: []



   .. py:property:: duration
      :type: float


      Calculate transformation duration.



.. py:class:: CodeAnalysisResult

   Results of deep code analysis.


   .. py:attribute:: file_path
      :type:  pathlib.Path


   .. py:attribute:: original_hash
      :type:  str


   .. py:attribute:: ast_tree
      :type:  ast.Module


   .. py:attribute:: node_counts
      :type:  dict[str, int]


   .. py:attribute:: complexity_score
      :type:  int
      :value: 0



   .. py:attribute:: detected_patterns
      :type:  list[str]
      :value: []



   .. py:attribute:: potential_issues
      :type:  list[str]
      :value: []



   .. py:attribute:: transformation_suggestions
      :type:  list[str]
      :value: []



   .. py:property:: lines_of_code
      :type: int


      Calculate lines of code from the AST.



   .. py:property:: function_count
      :type: int


      Count of function definitions.



   .. py:property:: class_count
      :type: int


      Count of class definitions.



   .. py:property:: issues
      :type: list[str]


      Alias for potential_issues for CLI compatibility.



   .. py:method:: to_dict()

      Convert to dictionary for JSON serialization.



.. py:class:: TransformationResult

   Complete result of a transformation operation.


   .. py:attribute:: original_code
      :type:  str


   .. py:attribute:: transformed_code
      :type:  str


   .. py:attribute:: analysis
      :type:  CodeAnalysisResult


   .. py:attribute:: metrics
      :type:  TransformationMetrics


   .. py:attribute:: success
      :type:  bool


   .. py:attribute:: changes_made
      :type:  list[str]
      :value: []



   .. py:property:: file_path
      :type: pathlib.Path


      Get the file path from the analysis.



.. py:class:: AdvancedASTAnalyzer(file_path)

   Bases: :py:obj:`ast.NodeVisitor`


   🔍 Advanced AST Analyzer with comprehensive logging.

   Performs deep analysis of Python code structure, detecting patterns,
   complexity, and potential transformation opportunities.


   .. py:attribute:: file_path


   .. py:attribute:: metrics


   .. py:attribute:: node_counts
      :type:  dict[str, int]


   .. py:attribute:: complexity_score
      :value: 0



   .. py:attribute:: detected_patterns
      :type:  list[str]
      :value: []



   .. py:attribute:: potential_issues
      :type:  list[str]
      :value: []



   .. py:attribute:: transformation_suggestions
      :type:  list[str]
      :value: []



   .. py:attribute:: current_depth
      :value: 0



   .. py:method:: analyze(tree)

      Perform comprehensive analysis of the AST.



   .. py:method:: visit(node)

      Visit a node with comprehensive logging.



.. py:class:: AdvancedTransformer(patterns)

   Bases: :py:obj:`ast.NodeTransformer`


   🔄 Advanced AST Transformer with pattern-based transformations.

   Applies sophisticated transformations based on detected patterns,
   with comprehensive logging and rollback capabilities.


   .. py:attribute:: patterns


   .. py:attribute:: metrics


   .. py:attribute:: changes_made
      :type:  list[str]
      :value: []



   .. py:attribute:: transformation_id
      :value: ''



   .. py:method:: transform(tree)

      Apply all transformations to the AST.



   .. py:method:: visit(node)

      Visit and potentially transform a node.



.. py:class:: AdvancedAssistant(verbose = True)

   🎯 Advanced Code Assistant - The Ultimate AST Transformation Engine.

   Combines deep analysis, pattern detection, and sophisticated transformations
   with comprehensive logging of every operation.


   .. py:attribute:: verbose
      :value: True



   .. py:attribute:: patterns
      :type:  list[ASTPattern]
      :value: []



   .. py:attribute:: session_id
      :value: ''



   .. py:method:: add_pattern(pattern)

      Add a custom transformation pattern.



   .. py:method:: analyze_file(file_path)

      Perform comprehensive analysis of a Python file.



   .. py:method:: transform_file(file_path, dry_run = False)

      Transform a Python file using all enabled patterns.



   .. py:method:: transform_directory(directory, pattern = '*.py', dry_run = False)

      Transform all Python files in a directory.



.. py:function:: create_advanced_assistant(verbose = True)

   Create a new Advanced Assistant instance.


.. py:function:: analyze_python_file(file_path)

   Quick analysis of a Python file.


.. py:function:: transform_python_file(file_path, dry_run = True)

   Quick transformation of a Python file.


