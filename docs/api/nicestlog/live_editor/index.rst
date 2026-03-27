nicestlog.live_editor
=====================

.. py:module:: nicestlog.live_editor

.. autoapi-nested-parse::

   🔥 Live Code Editor - Interactive editing of transformation proposals.

   Provides in-terminal code editing with syntax highlighting and validation.
   Records all user edits for machine learning and pattern improvement.



Attributes
----------

.. autoapisummary::

   nicestlog.live_editor.log
   nicestlog.live_editor.console


Classes
-------

.. autoapisummary::

   nicestlog.live_editor.EditSession
   nicestlog.live_editor.LiveCodeEditor


Functions
---------

.. autoapisummary::

   nicestlog.live_editor.create_live_editor
   nicestlog.live_editor.edit_code_live


Module Contents
---------------

.. py:data:: log

.. py:data:: console

.. py:class:: EditSession

   Records an editing session for machine learning.


   .. py:attribute:: original_code
      :type:  str


   .. py:attribute:: ai_suggestion
      :type:  str


   .. py:attribute:: user_final_code
      :type:  str


   .. py:attribute:: edit_steps
      :type:  list[str]


   .. py:attribute:: pattern_name
      :type:  str


   .. py:attribute:: file_path
      :type:  str


   .. py:attribute:: line_number
      :type:  int


   .. py:attribute:: accepted
      :type:  bool


   .. py:attribute:: edit_duration_seconds
      :type:  float


   .. py:attribute:: syntax_errors_encountered
      :type:  int
      :value: 0



.. py:class:: LiveCodeEditor(*, use_external_editor = False)

   🔥 Live Code Editor for Interactive Transformations.

   Allows users to edit AI transformation suggestions in real-time
   with syntax highlighting, validation, and comprehensive logging.


   .. py:attribute:: use_external_editor
      :value: False



   .. py:attribute:: edit_sessions
      :type:  list[EditSession]
      :value: []



   .. py:method:: edit_transformation(original_code, suggested_code, pattern_name, file_path, line_number)

      Edit a transformation suggestion interactively.

      Returns:
          - Final code (user-edited or original suggestion)
          - Whether user accepted the result
          - Edit session data for ML




   .. py:method:: save_edit_sessions(output_path)

      Save all edit sessions for machine learning analysis.



   .. py:method:: get_learning_insights()

      Analyze edit sessions to extract learning insights.



.. py:function:: create_live_editor(*, use_external_editor = False)

   Create a new Live Code Editor instance.


.. py:function:: edit_code_live(original_code, suggested_code, pattern_name, file_path, line_number)

   Quick live editing of a code transformation.


