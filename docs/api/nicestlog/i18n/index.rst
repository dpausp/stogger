nicestlog.i18n
==============

.. py:module:: nicestlog.i18n

.. autoapi-nested-parse::

   Internationalization support for nicestlog.

   Supports Austrian, Swiss German, and other dialects because why not!



Attributes
----------

.. autoapisummary::

   nicestlog.i18n.toml
   nicestlog.i18n.log


Classes
-------

.. autoapisummary::

   nicestlog.i18n.NicestlogTranslator


Functions
---------

.. autoapisummary::

   nicestlog.i18n.init_i18n
   nicestlog.i18n.get_translator
   nicestlog.i18n.t
   nicestlog.i18n.set_language
   nicestlog.i18n.oida
   nicestlog.i18n.leiwand
   nicestlog.i18n.arsch
   nicestlog.i18n.demo_translations


Module Contents
---------------

.. py:data:: toml
   :value: None


.. py:data:: log

.. py:class:: NicestlogTranslator(language = 'en')

   Translator for nicestlog with dialect support.

   Supports proper Austrian, Swiss German, and other regional variants
   because logging should be in your native language!


   .. py:attribute:: language
      :value: 'en'



   .. py:attribute:: translations
      :type:  dict[str, Any]


   .. py:attribute:: fallback_translations
      :type:  dict[str, Any]


   .. py:method:: get(key, section = 'general', **kwargs)

      Get translated string with Austrian flair.

      Args:
          key: Translation key
          section: Section in translation file
          **kwargs: Variables for string formatting

      Returns:
          Translated string with variables substituted




   .. py:method:: set_language(language)

      Change language and reload translations.



.. py:function:: init_i18n(language = 'en')

   Initialize internationalization.


.. py:function:: get_translator()

   Get current translator instance.


.. py:function:: t(key, section = 'general', **kwargs)

   Shorthand for translation.

   Usage:
       t("success")  # -> "Success!"
       t("file_not_found", "errors", filename="test.log")  # -> "File test.log not found!"


.. py:function:: set_language(language)

   Set global language.


.. py:function:: oida(message)

   Add Austrian flair to any message.


.. py:function:: leiwand(message)

   Make any message sound Austrian-positive.


.. py:function:: arsch(message)

   Austrian way to say something is bad.


.. py:function:: demo_translations()

   Demonstrate translation capabilities.


