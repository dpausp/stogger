nicestlog.cli_output_transformer
================================

.. py:module:: nicestlog.cli_output_transformer

.. autoapi-nested-parse::

   CLI Output to Structlog Transformer.

   This module provides AST transformation capabilities to convert CLI framework
   output functions (typer.echo, click.echo, rich.print, etc.) to structured
   logging with nicestlog, while preserving styling and formatting information.



Classes
-------

.. autoapisummary::

   nicestlog.cli_output_transformer.CLIOutputCall
   nicestlog.cli_output_transformer.CLIOutputToStructlogTransformer


Functions
---------

.. autoapisummary::

   nicestlog.cli_output_transformer.migrate_cli_outputs_file
   nicestlog.cli_output_transformer.analyze_cli_outputs_in_file


Module Contents
---------------

.. py:class:: CLIOutputCall

   Represents a detected CLI output function call.


   .. py:attribute:: framework
      :type:  str


   .. py:attribute:: function
      :type:  str


   .. py:attribute:: line_number
      :type:  int


   .. py:attribute:: original_call
      :type:  ast.Call


   .. py:attribute:: message_arg
      :type:  ast.AST | None
      :value: None



   .. py:attribute:: style_info
      :type:  dict[str, Any] | None
      :value: None



   .. py:attribute:: output_stream
      :type:  str
      :value: 'stdout'



.. py:class:: CLIOutputToStructlogTransformer

   Bases: :py:obj:`ast.NodeTransformer`


   Transform CLI framework output calls to structlog calls.


   .. py:attribute:: SIMPLE_EVENT_RE


   .. py:attribute:: import_structlog_present
      :value: False



   .. py:attribute:: logger_assignment_present
      :value: False



   .. py:attribute:: changed
      :value: False



   .. py:attribute:: detected_calls
      :type:  list[CLIOutputCall]
      :value: []



   .. py:attribute:: imports


   .. py:attribute:: rich_console_vars
      :type:  set[str]


   .. py:method:: slugify(text)
      :staticmethod:


      Convert text to a valid event identifier.



   .. py:method:: derive_event_from_literal(arg)
      :staticmethod:


      Extract event name from string literal.



   .. py:method:: is_simple_event(s)
      :staticmethod:


      Check if string is a valid simple event name.



   .. py:method:: visit_Import(node)

      Track imports of CLI frameworks.



   .. py:method:: visit_ImportFrom(node)

      Track from imports of CLI frameworks.



   .. py:method:: visit_Assign(node)

      Track logger assignments and rich console instances.



   .. py:method:: detect_cli_output_call(node)

      Detect and classify CLI output function calls.



   .. py:method:: visit_Call(node)

      Transform CLI output calls to structlog calls.



   .. py:method:: ensure_imports_and_logger(tree)

      Ensure structlog import and logger assignment are present.



.. py:function:: migrate_cli_outputs_file(content)

   Migrate CLI output calls in a single file.


.. py:function:: analyze_cli_outputs_in_file(content)

   Analyze CLI output calls in a file without transforming.


