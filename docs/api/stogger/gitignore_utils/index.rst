stogger.gitignore_utils
=======================

.. py:module:: stogger.gitignore_utils

.. autoapi-nested-parse::

   Utilities for respecting .gitignore patterns in file analysis.



Attributes
----------

.. autoapisummary::

   stogger.gitignore_utils.log


Functions
---------

.. autoapisummary::

   stogger.gitignore_utils.load_gitignore_patterns
   stogger.gitignore_utils.should_ignore_path
   stogger.gitignore_utils.filter_python_files


Module Contents
---------------

.. py:data:: log

.. py:function:: load_gitignore_patterns(directory)

   Load patterns from .gitignore file.


.. py:function:: should_ignore_path(file_path, base_dir, patterns)

   Check if a file path should be ignored based on gitignore patterns.


.. py:function:: filter_python_files(directory, *, respect_gitignore = True)

   Get Python files in directory, respecting .gitignore if requested.


