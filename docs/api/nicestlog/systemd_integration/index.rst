nicestlog.systemd_integration
=============================

.. py:module:: nicestlog.systemd_integration

.. autoapi-nested-parse::

   Advanced systemd integration for nicestlog.

   Makes systemd logging actually usable and powerful.



Attributes
----------

.. autoapisummary::

   nicestlog.systemd_integration.logger
   nicestlog.systemd_integration.SYSTEMD_AVAILABLE


Classes
-------

.. autoapisummary::

   nicestlog.systemd_integration.SystemdJournalHandler
   nicestlog.systemd_integration.ServiceConfig


Functions
---------

.. autoapisummary::

   nicestlog.systemd_integration.detect_systemd_environment
   nicestlog.systemd_integration.setup_systemd_logging
   nicestlog.systemd_integration.create_systemd_service_file
   nicestlog.systemd_integration.query_journal_logs
   nicestlog.systemd_integration.parse_time_delta
   nicestlog.systemd_integration.demo_systemd_integration


Module Contents
---------------

.. py:data:: logger

.. py:data:: SYSTEMD_AVAILABLE
   :value: True


.. py:class:: SystemdJournalHandler(identifier = None, facility = None)

   Advanced systemd journal handler with proper field mapping and priorities.


   .. py:attribute:: PRIORITY_MAP
      :type:  ClassVar[dict[str, int]]


   .. py:attribute:: identifier
      :value: 'nicestlog'



   .. py:attribute:: facility
      :value: None



   .. py:attribute:: hostname


   .. py:attribute:: pid


.. py:function:: detect_systemd_environment()

   Detect if we're running under systemd and gather environment info.


.. py:function:: setup_systemd_logging(identifier = None, facility = None)

   Set up systemd journal logging integration.

   This function prefers the detected runtime environment to decide whether to
   enable systemd logging. If a systemd environment is detected, it will attach
   a SystemdJournalHandler even when the systemd-python package is not
   available; in that case, the handler acts as a no-op but preserves the
   processor chain shape. If no systemd environment is detected, the function
   returns False.

   Args:
       identifier: SYSLOG_IDENTIFIER for journal entries
       facility: SYSLOG_FACILITY
       structured_fields: Whether to include structured data as journal fields

   Returns:
       True if systemd logging was successfully configured, otherwise False



.. py:class:: ServiceConfig

   Configuration for systemd service creation.


   .. py:attribute:: service_name
      :type:  str


   .. py:attribute:: exec_command
      :type:  str


   .. py:attribute:: user
      :type:  str | None
      :value: None



   .. py:attribute:: working_directory
      :type:  str | None
      :value: None



   .. py:attribute:: environment
      :type:  dict[str, str] | None
      :value: None



   .. py:attribute:: restart_policy
      :type:  str
      :value: 'always'



.. py:function:: create_systemd_service_file(config)

   Generate a systemd service file with proper logging configuration.

   Args:
       config: Service configuration parameters

   Returns:
       Service file content as string



.. py:function:: query_journal_logs(service_name = None, since = '1 hour ago', level = None, lines = 100)

   Query systemd journal for logs.

   Args:
       service_name: Filter by service name
       since: Time filter (e.g., "1 hour ago", "today")
       level: Log level filter
       lines: Maximum number of lines

   Returns:
       List of log entries as dictionaries



.. py:function:: parse_time_delta(time_str)

   Parse time strings like '1 hour ago' into seconds.


.. py:function:: demo_systemd_integration()

   Demonstrate systemd integration features.


