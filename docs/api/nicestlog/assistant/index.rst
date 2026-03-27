nicestlog.assistant
===================

.. py:module:: nicestlog.assistant

.. autoapi-nested-parse::

   Assistant tools to migrate print/logging statements to structlog.

   This is a minimal, safe transformer that:
   - ensures each module imports structlog and has a top-level `log = structlog.get_logger()`
   - rewrites `print(...)` calls to `log.info("print-output", items=[...])`

   It intentionally avoids complex logging-module rewrites for safety.



Classes
-------

.. autoapisummary::

   nicestlog.assistant.MigrationResult
   nicestlog.assistant.PrintToStructlogTransformer


Functions
---------

.. autoapisummary::

   nicestlog.assistant.migrate_file
   nicestlog.assistant.migrate_directory


Module Contents
---------------

.. py:class:: MigrationResult

   Result of migration operations.


   .. py:attribute:: files_processed
      :type:  int
      :value: 0



   .. py:attribute:: files_transformed
      :type:  int
      :value: 0



   .. py:attribute:: diffs
      :type:  dict[str, list[str]]


.. py:class:: PrintToStructlogTransformer

   Bases: :py:obj:`ast.NodeTransformer`


   AST transformer to convert print statements to structlog calls.


   .. py:attribute:: SIMPLE_EVENT_RE


   .. py:method:: slugify(text)
      :staticmethod:


      Convert text to slug format.



   .. py:method:: derive_event_from_literal(arg)
      :staticmethod:


      Derive event name from AST literal.



   .. py:method:: is_simple_event(s)
      :staticmethod:


      Check if string is a simple event name.



   .. py:attribute:: import_structlog_present
      :value: False



   .. py:attribute:: logger_assignment_present
      :value: False



   .. py:attribute:: changed
      :value: False



   .. py:method:: visit_Import(node)

      Visit import statements.



   .. py:method:: visit_ImportFrom(node)

      Visit import from statements.



   .. py:method:: visit_Assign(node)

      Visit assignment statements.



   .. py:method:: visit_call_build_print(node)

      Build print call transformation.



   .. py:method:: visit_Call(node)

      Visit call statements.



   .. py:method:: ensure_imports_and_logger(tree)

      Ensure necessary imports and logger setup.



.. py:function:: migrate_file(content)

   Migrate a single file's content.


.. py:function:: migrate_directory(input_dir, output_dir, *, dry_run = True)

   Migrate Python files under input_dir. Writes to output_dir if provided, else in-place.


