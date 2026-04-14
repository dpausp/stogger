"""Internationalization support for stogger.

Supports Austrian, Swiss German, and other dialects because why not!
"""

import tomllib
from pathlib import Path
from typing import Any

import structlog

from .config import StoggerConfig

# Get logger for this module
log = structlog.get_logger(__name__)


class NicestlogTranslator:
    """Translation engine that loads localized strings from TOML files.

    Looks up keys in ``{language}.toml`` under a ``translations/`` directory,
    falling back to ``en.toml`` when a key is missing. Use :func:`init_i18n`
    or :func:`get_translator` instead of instantiating this class directly.

    Attributes:
        language: Current BCP-47-ish language code (e.g. ``"en"``, ``"at"``).
        translations: Dict loaded from the requested language TOML.
        fallback_translations: Dict loaded from ``en.toml``.

    """

    def __init__(self, language: str = "en") -> None:
        self.language = language
        self.translations: dict[str, Any] = {}
        self.fallback_translations: dict[str, Any] = {}

        log.debug("initializing-translator", language=language)
        self._load_translations()

    def _load_translations(self) -> None:
        """Load translation files."""
        # Prefer configured translation_dir from pyproject.toml if available
        try:
            cfg = StoggerConfig()
            if cfg.translation_dir:
                translations_dir = Path(cfg.translation_dir)
            else:
                translations_dir = Path(__file__).parent.parent.parent / "translations"
        except (AttributeError, FileNotFoundError, ValueError):
            translations_dir = Path(__file__).parent.parent.parent / "translations"

        # Load fallback (English)
        fallback_file = translations_dir / "en.toml"
        if fallback_file.exists():
            with fallback_file.open("rb") as f:
                self.fallback_translations = tomllib.load(f)
            log.debug("loaded-fallback-translations", file=str(fallback_file))

        # Load requested language
        lang_file = translations_dir / f"{self.language}.toml"
        if lang_file.exists():
            with lang_file.open("rb") as f:
                self.translations = tomllib.load(f)
            log.debug(
                "loaded-translations",
                language=self.language,
                file=str(lang_file),
                keys_loaded=len(self.translations),
            )
        else:
            log.warning(
                "translation-file-not-found",
                language=self.language,
                file=str(lang_file),
                fallback="en",
            )

    def get(self, key: str, section: str = "general", **kwargs) -> str:
        """Get translated string with Austrian flair.

        Args:
            key: Translation key
            section: Section in translation file
            **kwargs: Variables for string formatting

        Returns:
            Translated string with variables substituted

        """
        log.debug(
            "getting-translation",
            key=key,
            section=section,
            language=self.language,
        )

        # Try to get from current language
        translation = self._get_from_dict(self.translations, section, key)

        # Fallback to English
        if not translation:
            translation = self._get_from_dict(self.fallback_translations, section, key)
            log.debug("using_fallback_translation", key=key, section=section)

        # Last resort: return the key itself
        if not translation:
            translation = f"{section}.{key}"
            log.warning(
                "translation_missing",
                key=key,
                section=section,
                language=self.language,
            )

        # Format with variables
        try:
            if kwargs:
                translation = translation.format(**kwargs)
                log.debug("formatted_translation", key=key, variables=kwargs)
        except Exception as e:
            log.exception(
                "translation-formatting-failed",
                key=key,
                translation=translation,
                variables=kwargs,
                error=str(e),
            )

        return translation

    def _get_from_dict(
        self,
        translations: dict[str, Any],
        section: str,
        key: str,
    ) -> str | None:
        """Get translation from nested dictionary."""
        if not translations:
            return None

        if section in translations and key in translations[section]:
            return translations[section][key]

        # Try direct key lookup
        if key in translations:
            return translations[key]

        return None

    def set_language(self, language: str) -> None:
        """Change language and reload translations."""
        log.debug(
            "changing_language",
            old_language=self.language,
            new_language=language,
        )
        self.language = language
        self._load_translations()


# Global translator instance
_translator: NicestlogTranslator | None = None


def init_i18n(language: str = "en") -> NicestlogTranslator:
    """Create the global translator and store it for later :func:`get_translator` calls.

    Args:
        language: Language code matching a TOML file in the translations
            directory (e.g. ``"en"``, ``"at"``, ``"ch"``).  Defaults to ``"en"``.

    Returns:
        The newly created :class:`NicestlogTranslator` instance (also stored
        as the module-level singleton).

    """
    global _translator

    log.debug("initializing-i18n", language=language)
    _translator = NicestlogTranslator(language)
    return _translator


def get_translator() -> NicestlogTranslator:
    """Return the module-level translator, auto-initializing with English if needed.

    Returns:
        The current :class:`NicestlogTranslator` singleton.

    """
    global _translator

    if _translator is None:
        log.debug("auto-initializing-translator", fallback_language="en")
        _translator = NicestlogTranslator()

    return _translator


def t(key: str, section: str = "general", **kwargs) -> str:
    """Look up a translated string by *key* and *section* using the global translator.

    This is the primary i18n helper — a short, memorable name for everyday use.

    Args:
        key: Translation key inside *section* (e.g. ``"success"``).
        section: Top-level section in the TOML file (default ``"general"``).
        **kwargs: Variables passed to :meth:`str.format` on the translated template.

    Returns:
        The translated and formatted string.  Falls back to English, then to
        ``"{section}.{key}"`` if neither language contains the key.

    Examples::

        t("success")                                    # "Success!"
        t("file_not_found", "errors", filename="x.log") # "File x.log not found!"

    """
    return get_translator().get(key, section, **kwargs)


def set_language(language: str) -> None:
    """Set global language."""
    log.debug("setting_global_language", language=language)
    get_translator().set_language(language)


# Austrian shortcuts for fun
def oida(message: str) -> str:
    """Prepend an emphatic Austrian exclamation to *message*.

    **Fun helper** — not part of the core i18n API.  ``"oida"`` is a versatile
    Austrian interjection roughly equivalent to "dude!" or "wow!".

    Args:
        message: Any string to prefix.

    Returns:
        ``"Oida, {message}!"``

    """
    return f"Oida, {message}!"


def leiwand(message: str) -> str:
    """Append Austrian approval to *message*.

    **Fun helper** — not part of the core i18n API.  ``"leiwand"`` means
    "awesome" / "solid" in Austrian slang.

    Args:
        message: Any string to suffix.

    Returns:
        ``"{message} - leiwand!"``

    """
    return f"{message} - leiwand!"


def arsch(message: str) -> str:
    """Append Austrian disapproval to *message*.

    **Fun helper** — not part of the core i18n API.  Roughly translates to
    "that's terrible" in Austrian dialect.

    Args:
        message: Any string to suffix.

    Returns:
        ``"{message} - des is arsch!"``

    """
    return f"{message} - des is arsch!"


# Demo function
def demo_translations() -> None:
    """Demonstrate translation capabilities."""
    languages = ["en", "at", "ch", "wollgesisch"]

    for lang in languages:
        NicestlogTranslator(lang)


if __name__ == "__main__":
    # Setup logging for demo
    import stogger

    stogger.init_logging()

    demo_translations()
