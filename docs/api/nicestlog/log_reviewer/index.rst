nicestlog.log_reviewer
======================

.. py:module:: nicestlog.log_reviewer

.. autoapi-nested-parse::

   Log Quality Reviewer - Analyzes your logs and tells you if they're "arsch" or not.

   Reviews log quality, structure, and usefulness with Austrian directness.



Attributes
----------

.. autoapisummary::

   nicestlog.log_reviewer.MIN_FIELDS_FOR_STRUCTURED
   nicestlog.log_reviewer.MIN_LEVELS_FOR_GOOD_COVERAGE
   nicestlog.log_reviewer.MIN_EVENTS_FOR_DIVERSITY
   nicestlog.log_reviewer.MIN_FIELDS_FOR_USAGE


Classes
-------

.. autoapisummary::

   nicestlog.log_reviewer.LogQualityReport
   nicestlog.log_reviewer.LogQualityReviewer


Functions
---------

.. autoapisummary::

   nicestlog.log_reviewer.print_report


Module Contents
---------------

.. py:data:: MIN_FIELDS_FOR_STRUCTURED
   :value: 2


.. py:data:: MIN_LEVELS_FOR_GOOD_COVERAGE
   :value: 3


.. py:data:: MIN_EVENTS_FOR_DIVERSITY
   :value: 5


.. py:data:: MIN_FIELDS_FOR_USAGE
   :value: 10


.. py:class:: LogQualityReport

   Report on log quality with Austrian honesty.


   .. py:attribute:: overall_score
      :type:  float


   .. py:attribute:: overall_verdict
      :type:  str


   .. py:attribute:: issues
      :type:  list[str]


   .. py:attribute:: good_practices
      :type:  list[str]


   .. py:attribute:: suggestions
      :type:  list[str]


   .. py:attribute:: stats
      :type:  dict[str, Any]


.. py:class:: LogQualityReviewer

   Reviews log quality with Austrian directness.

   Analyzes logs for structure, usefulness, and best practices.
   Gives honest feedback about whether your logs are "arsch" or not.


   .. py:attribute:: event_patterns
      :value: []



   .. py:attribute:: field_patterns
      :value: []



   .. py:attribute:: bad_patterns
      :value: ['debug\\s*print', 'console\\.log', 'System\\.out\\.println', 'print\\s*\\(']



   .. py:attribute:: quality_levels


   .. py:method:: analyze_log_file(file_path)

      Analyze a log file for quality.



   .. py:method:: analyze_log_content(log_content)

      Analyze log content directly.



.. py:function:: print_report(report, format_type = 'text')

   Print the quality report.


