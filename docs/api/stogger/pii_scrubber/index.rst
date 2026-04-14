stogger.pii_scrubber
====================

.. py:module:: stogger.pii_scrubber

.. autoapi-nested-parse::

   PII (Personally Identifiable Information) Scrubber for stogger.

   Automatically detects and redacts sensitive information from log messages.



Classes
-------

.. autoapisummary::

   stogger.pii_scrubber.PIIScrubber


Functions
---------

.. autoapisummary::

   stogger.pii_scrubber.create_pii_processor
   stogger.pii_scrubber.demo_pii_scrubbing


Module Contents
---------------

.. py:class:: PIIScrubber(custom_patterns = None, sensitive_fields = None, redaction_text = '[REDACTED]')

   Scrubs PII from log messages using regex patterns and field name detection.


   .. py:attribute:: redaction_text
      :value: '[REDACTED]'



   .. py:attribute:: patterns


   .. py:attribute:: compiled_patterns


   .. py:attribute:: sensitive_fields


   .. py:method:: scrub_string(text)

      Scrub PII from a string.



   .. py:method:: scrub_dict(data)

      Scrub PII from dictionary values and sensitive field names.



   .. py:method:: scrub_list(data)

      Scrub PII from list items.



   .. py:method:: scrub_event_dict(event_dict)

      Scrub PII from a structlog event dictionary.

      This is the main method used as a structlog processor.



.. py:function:: create_pii_processor(custom_patterns = None, sensitive_fields = None, redaction_text = '[REDACTED]')

   Create a PII scrubber processor for structlog.


.. py:function:: demo_pii_scrubbing()

   Demonstrate PII scrubbing capabilities.


