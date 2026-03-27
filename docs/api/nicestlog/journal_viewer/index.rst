nicestlog.journal_viewer
========================

.. py:module:: nicestlog.journal_viewer

.. autoapi-nested-parse::

   Beautiful systemd journal viewer - makes journalctl actually usable!

   Reads binary journal logs and displays them with nicestlog's beautiful formatting.



Attributes
----------

.. autoapisummary::

   nicestlog.journal_viewer.log
   nicestlog.journal_viewer.SYSTEMD_AVAILABLE
   nicestlog.journal_viewer.RESET_ALL


Classes
-------

.. autoapisummary::

   nicestlog.journal_viewer.JournalQueryOptions
   nicestlog.journal_viewer.JournalEntry
   nicestlog.journal_viewer.JournalViewer


Functions
---------

.. autoapisummary::

   nicestlog.journal_viewer.main


Module Contents
---------------

.. py:data:: log

.. py:class:: JournalQueryOptions

   Options for journal queries.


   .. py:attribute:: service
      :type:  str | None
      :value: None



   .. py:attribute:: since
      :type:  str | None
      :value: None



   .. py:attribute:: until
      :type:  str | None
      :value: None



   .. py:attribute:: level
      :type:  str | None
      :value: None



   .. py:attribute:: lines
      :type:  int | None
      :value: None



   .. py:attribute:: follow
      :type:  bool
      :value: False



.. py:data:: SYSTEMD_AVAILABLE
   :value: True


.. py:data:: RESET_ALL
   :value: 0


.. py:class:: JournalEntry

   Structured representation of a journal entry.


   .. py:attribute:: timestamp
      :type:  datetime.datetime


   .. py:attribute:: hostname
      :type:  str


   .. py:attribute:: service
      :type:  str


   .. py:attribute:: pid
      :type:  str


   .. py:attribute:: level
      :type:  str


   .. py:attribute:: message
      :type:  str


   .. py:attribute:: fields
      :type:  dict[str, Any]


   .. py:attribute:: raw_entry
      :type:  dict[str, Any]


.. py:class:: JournalViewer(*, show_hostname = False, show_pid = True, show_service = True, max_width = 120)

   Beautiful viewer for systemd journal logs.

   Converts binary journal entries back into human-readable format
   with the same beautiful styling as nicestlog console output.


   .. py:attribute:: PRIORITY_TO_LEVEL
      :type:  ClassVar[dict[int, str]]


   .. py:attribute:: LEVEL_COLORS
      :type:  ClassVar[dict[str, str]]


   .. py:attribute:: show_hostname
      :value: False



   .. py:attribute:: show_pid
      :value: True



   .. py:attribute:: show_service
      :value: True



   .. py:attribute:: max_width
      :value: 120



   .. py:method:: parse_journal_entry(entry)

      Parse a raw journal entry into structured format.



   .. py:method:: format_entry(entry)

      Format a journal entry with beautiful styling.



   .. py:method:: query_journal(options_or_service=None, **kwargs)

      Query systemd journal and yield formatted entries.

      Args:
          service: Filter by service/identifier
          since: Start time (e.g., "1 hour ago", "2023-01-01 10:00")
          until: End time
          level: Minimum log level
          lines: Maximum number of lines
          follow: Follow new entries (like tail -f)




   .. py:method:: parse_time_string(time_str)

      Parse various time string formats.



.. py:function:: main()

   CLI interface for journal viewer.


