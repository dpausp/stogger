stogger.factory
===============

.. py:module:: stogger.factory

.. autoapi-nested-parse::

   Factory functions for building stogger components.



Attributes
----------

.. autoapisummary::

   stogger.factory.log


Functions
---------

.. autoapisummary::

   stogger.factory.build_timestamp_processor
   stogger.factory.build_shared_processors
   stogger.factory.build_renderer
   stogger.factory.configure_stdlib_logging


Module Contents
---------------

.. py:data:: log

.. py:function:: build_timestamp_processor(config)

   Build a TimeStamper processor based on config.format.timestamp_precision.

   Central factory function for timestamp configuration. All TimeStamper
   call sites use this function to ensure consistent utc=True and correct fmt.

   Args:
       config: A config object with a .format attribute containing FormatConfig.

   Returns:
       A TimeStamper processor configured with the appropriate fmt and utc=True.



.. py:function:: build_shared_processors(config)

   Builds processors that are shared between sync and async modes.


.. py:function:: build_renderer(config)

   Builds the final renderer based on the log format.


.. py:function:: configure_stdlib_logging(config, processors)

   Configures the standard Python logging library.


