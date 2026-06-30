stogger.systemd
===============

.. py:module:: stogger.systemd

.. autoapi-nested-parse::

   stogger.systemd — systemd journal I/O for stogger.

   Lazy-loaded: only imported when systemd journal integration is enabled.
   Uses only stdlib (socket, stat, pathlib) — no external dependencies.



Attributes
----------

.. autoapisummary::

   stogger.systemd.JOURNAL_SOCKET_PATH


Classes
-------

.. autoapisummary::

   stogger.systemd.JournalSender
   stogger.systemd.JournalLogger
   stogger.systemd.DummyJournalLogger
   stogger.systemd.JournalLoggerFactory


Functions
---------

.. autoapisummary::

   stogger.systemd.get_journal_logger_factory


Module Contents
---------------

.. py:data:: JOURNAL_SOCKET_PATH
   :value: '/run/systemd/journal/socket'


.. py:class:: JournalSender(socket_path = JOURNAL_SOCKET_PATH)

   Send structured messages to the systemd journal via AF_UNIX socket.


   .. py:method:: send(fields)


   .. py:method:: format_message(fields)
      :staticmethod:



.. py:class:: JournalLogger(syslog_identifier = 'stogger', syslog_facility = 0, socket_path = JOURNAL_SOCKET_PATH)

   Write log messages to the systemd journal via AF_UNIX socket.


   .. py:attribute:: syslog_identifier
      :value: 'stogger'



   .. py:attribute:: syslog_facility
      :value: 0



   .. py:attribute:: socket_path
      :value: '/run/systemd/journal/socket'



   .. py:method:: msg(messages)


.. py:class:: DummyJournalLogger

   No-op journal logger for non-systemd environments.


   .. py:method:: msg(messages)


.. py:class:: JournalLoggerFactory(socket_path = JOURNAL_SOCKET_PATH)

   Creates JournalLogger or DummyJournalLogger based on systemd availability.


   .. py:attribute:: socket_path
      :value: '/run/systemd/journal/socket'



.. py:function:: get_journal_logger_factory()

   Return a JournalLoggerFactory instance.


