stogger.i18n_check
==================

.. py:module:: stogger.i18n_check

.. autoapi-nested-parse::

   Utilities to check completeness of stogger i18n translation files.

   This scans Python source files for usages of `_replace_msg` and `_msg_key`
   within structlog logger calls and verifies that the translation file contains
   entries for all detected message keys.



Attributes
----------

.. autoapisummary::

   stogger.i18n_check.EXCLUDE_DIRS


Functions
---------

.. autoapisummary::

   stogger.i18n_check.find_required_translation_keys
   stogger.i18n_check.scan_translation_keys
   stogger.i18n_check.load_translation_keys
   stogger.i18n_check.check_translations
   stogger.i18n_check.format_report
   stogger.i18n_check.run_i18n_check_cli


Module Contents
---------------

.. py:data:: EXCLUDE_DIRS

.. py:function:: find_required_translation_keys(paths)

   Scan Python files for keys required by the TranslationProcessor.

   Returns:
       tuple(set(event_keys), set(msg_keys))



.. py:function:: scan_translation_keys(paths)

   Scan Python files for all translation-related keys in a single pass.

   This optimized function reduces IO by scanning files once and extracting
   all needed information: event keys, message keys, and debug events.

   Returns:
       tuple(set(event_keys), set(msg_keys), set(debug_events))



.. py:function:: load_translation_keys(translation_file)

   Load top-level keys from a TOML translation file.

   TranslationProcessor expects a flat dict keyed by event/msg_key.
   Any top-level keys that map to non-dict values are considered message entries.


.. py:function:: check_translations(source_paths, translation_dir, language = 'en')

   Check translation coverage and return a report dict.

   Returns keys:
     - required_keys: set[str]
     - translation_keys: set[str]
     - missing_keys: list[str]
     - missing_by_level: dict[str, list[str]]
     - extra_keys: list[str]
     - translation_file: str
     - msg_keys_found: set[str]
     - debug_with_replace_events: set[str]


.. py:function:: format_report(report, *, include_debug = True)

.. py:function:: run_i18n_check_cli(path = '.', translation_dir = 'translations', language = 'en', *, strict = False)

   Run the i18n check and print a human-friendly report. Returns exit code.


