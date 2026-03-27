nicestlog.interactive_transformer
=================================

.. py:module:: nicestlog.interactive_transformer

.. autoapi-nested-parse::

   🎯 Interactive Code Transformer - Amber-style Search & Replace for AST Transformations.

   Provides interactive, user-guided code transformations with preview and confirmation,
   inspired by the amber search & replace tool.



Attributes
----------

.. autoapisummary::

   nicestlog.interactive_transformer.log
   nicestlog.interactive_transformer.console


Classes
-------

.. autoapisummary::

   nicestlog.interactive_transformer.UserChoice
   nicestlog.interactive_transformer.TransformationProposal
   nicestlog.interactive_transformer.InteractiveSession
   nicestlog.interactive_transformer.InteractiveTransformer


Functions
---------

.. autoapisummary::

   nicestlog.interactive_transformer.create_interactive_transformer
   nicestlog.interactive_transformer.transform_file_interactive
   nicestlog.interactive_transformer.transform_directory_interactive


Module Contents
---------------

.. py:data:: log

.. py:data:: console

.. py:class:: UserChoice(*args, **kwds)

   Bases: :py:obj:`enum.Enum`


   User choices for interactive transformations.


   .. py:attribute:: YES
      :value: 'y'



   .. py:attribute:: NO
      :value: 'n'



   .. py:attribute:: ALL
      :value: 'a'



   .. py:attribute:: QUIT
      :value: 'q'



   .. py:attribute:: SKIP_FILE
      :value: 's'



   .. py:attribute:: PREVIEW
      :value: 'p'



   .. py:attribute:: EDIT
      :value: 'e'



.. py:class:: TransformationProposal

   A proposed transformation with context.


   .. py:attribute:: file_path
      :type:  pathlib.Path


   .. py:attribute:: line_number
      :type:  int


   .. py:attribute:: original_code
      :type:  str


   .. py:attribute:: transformed_code
      :type:  str


   .. py:attribute:: pattern_name
      :type:  str


   .. py:attribute:: pattern_description
      :type:  str


   .. py:attribute:: context_before
      :type:  list[str]


   .. py:attribute:: context_after
      :type:  list[str]


   .. py:attribute:: node_type
      :type:  str


   .. py:attribute:: user_edited
      :type:  bool
      :value: False



   .. py:attribute:: edit_history
      :type:  list[str] | None
      :value: None



.. py:class:: InteractiveSession

   State for an interactive transformation session.


   .. py:attribute:: total_proposals
      :type:  int
      :value: 0



   .. py:attribute:: accepted
      :type:  int
      :value: 0



   .. py:attribute:: rejected
      :type:  int
      :value: 0



   .. py:attribute:: skipped_files
      :type:  int
      :value: 0



   .. py:attribute:: auto_accept_all
      :type:  bool
      :value: False



   .. py:attribute:: quit_requested
      :type:  bool
      :value: False



   .. py:attribute:: edited
      :type:  int
      :value: 0



   .. py:attribute:: edit_sessions
      :type:  list[nicestlog.live_editor.EditSession] | None
      :value: None



.. py:class:: InteractiveTransformer(assistant = None, *, context_lines = 3, enable_live_editing = True, use_external_editor = False)

   🎯 Interactive Code Transformer with Amber-style Interface.

   Provides user-guided code transformations with preview, confirmation,
   and comprehensive logging of all decisions.


   .. py:attribute:: assistant


   .. py:attribute:: context_lines
      :value: 3



   .. py:attribute:: session


   .. py:attribute:: enable_live_editing
      :value: True



   .. py:attribute:: live_editor


   .. py:method:: transform_file_interactive(file_path)

      Transform a file with interactive user confirmation.



   .. py:method:: transform_directory_interactive(directory, pattern = '*.py')

      Transform all files in a directory with interactive confirmation.



.. py:function:: create_interactive_transformer(context_lines = 3)

   Create a new Interactive Transformer instance.


.. py:function:: transform_file_interactive(file_path, context_lines = 3)

   Quick interactive transformation of a Python file.


.. py:function:: transform_directory_interactive(directory, pattern = '*.py', context_lines = 3)

   Quick interactive transformation of a directory.


