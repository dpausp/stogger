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

   stogger.factory.build_shared_processors
   stogger.factory.build_renderer
   stogger.factory.configure_stdlib_logging


Module Contents
---------------

.. py:data:: log

.. py:function:: build_shared_processors(config)

   Builds processors that are shared between sync and async modes.


.. py:function:: build_renderer(config)

   Builds the final renderer based on the log format.


.. py:function:: configure_stdlib_logging(config, processors)

   Configures the standard Python logging library.


