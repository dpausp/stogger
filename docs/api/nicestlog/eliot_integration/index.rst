nicestlog.eliot_integration
===========================

.. py:module:: nicestlog.eliot_integration

.. autoapi-nested-parse::

   Eliot integration for nicestlog - Beautiful human-readable action tracing.

   Combines Eliot's powerful action tracking with nicestlog's beautiful output.



Attributes
----------

.. autoapisummary::

   nicestlog.eliot_integration.ELIOT_AVAILABLE
   nicestlog.eliot_integration.RESET_ALL


Classes
-------

.. autoapisummary::

   nicestlog.eliot_integration.HumanReadableEliotDestination


Functions
---------

.. autoapisummary::

   nicestlog.eliot_integration.setup_eliot_logging
   nicestlog.eliot_integration.demo_eliot_integration


Module Contents
---------------

.. py:data:: ELIOT_AVAILABLE
   :value: True


.. py:data:: RESET_ALL
   :value: 0


.. py:class:: HumanReadableEliotDestination(*, file = None, show_timestamps = True, show_task_ids = False, max_width = 120)

   Eliot destination that outputs beautiful, human-readable action traces.

   Instead of ugly JSON, this creates beautiful nested action logs that
   show the flow of your application with proper indentation and colors.


   .. py:attribute:: file


   .. py:attribute:: show_timestamps
      :value: True



   .. py:attribute:: show_task_ids
      :value: False



   .. py:attribute:: max_width
      :value: 120



.. py:function:: setup_eliot_logging(*, destination = None, human_readable = True, show_timestamps = True, show_task_ids = False)

   Setup Eliot logging with nicestlog integration.

   Args:
       destination: Where to write logs (default: stdout)
       human_readable: Use human-readable format instead of JSON
       show_timestamps: Include timestamps in output
       show_task_ids: Show Eliot task IDs (useful for debugging)

   Returns:
       True if Eliot was successfully configured, False if not available



.. py:function:: demo_eliot_integration()

   Demonstrate Eliot integration with beautiful output.


