.. nicestlog documentation master file

🎯 nicestlog Documentation
==========================

.. image:: assets/nicestlog_logo_ascii.txt
   :alt: nicestlog logo

**A sophisticated multi-target structured logging system built on structlog** 🚀

Welcome to the comprehensive documentation for nicestlog - your go-to solution for elegant, structured, and powerful logging in Python applications.

.. toctree::
   :maxdepth: 2
   :caption: User Guide
   :hidden:

   user_guide/getting_started
   user_guide/best_practices
   user_guide/advanced_features
   user_guide/quick_practices
   user_guide/nix_integration
   user_guide/cli_reference

.. toctree::
   :maxdepth: 2
   :caption: Features
   :hidden:

   features/advanced_assistant
   features/log_analysis
   features/integrations

.. toctree::
   :maxdepth: 2
   :caption: Development
   :hidden:

   development/todo
   development/api_reference
   development/lessons_dogfooding_check

Quick Start
-----------

Install nicestlog and start logging like a pro:

.. code-block:: bash

   pip install nicestlog

.. code-block:: python

   import nicestlog
   import structlog

   # Initialize console logging and get a structlog logger
   nicestlog.init_logging(verbose=True)
   log = structlog.get_logger()
   log.info("hello-world", user_id=123, action="login")

Key Features
------------

✨ **Advanced AST Assistant** - Revolutionary code transformation
🔍 **Log Statement Analysis** - Intelligent issue detection  
📊 **Best Practices** - Proven logging patterns
🎨 **Beautiful Output** - Colorful and structured logs
🔧 **Multiple Integrations** - Eliot, systemd, and more

Navigation
----------

* :doc:`user_guide/getting_started` - Start your nicestlog journey
* :doc:`user_guide/best_practices` - Learn the proven patterns
* :doc:`features/advanced_assistant` - Discover code transformation magic
* :doc:`features/log_analysis` - Understand log issue detection
* :doc:`development/api_reference` - Complete API documentation

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`