stogger.processors
==================

.. py:module:: stogger.processors

.. autoapi-nested-parse::

   Processor factory functions.



Functions
---------

.. autoapisummary::

   stogger.processors.build_timestamp_processor


Module Contents
---------------

.. py:function:: build_timestamp_processor(config)

   Build a TimeStamper processor based on config.format.timestamp_precision.

   Central factory function for timestamp configuration. All TimeStamper
   call sites use this function to ensure consistent utc=True and correct fmt.

   Args:
       config: A config object with a .format attribute containing FormatConfig.

   Returns:
       A TimeStamper processor configured with the appropriate fmt and utc=True.



