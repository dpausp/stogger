"""
Internationalization support for nicestlog.

Supports Austrian, Swiss German, and other dialects because why not!
"""

from pathlib import Path
from typing import Dict, Any, Optional
import structlog

try:
    import toml  # type: ignore[import-untyped]
except ImportError:
    toml = None  # type: ignore[assignment]

# Get logger for this module
log = structlog.get_logger(__name__)


class NicestlogTranslator:
    """
    Translator for nicestlog with dialect support.

    Supports proper Austrian, Swiss German, and other regional variants
    because logging should be in your native language!
    """

    def __init__(self, language: str = "en"):
        self.language = language
        self.translations: Dict[str, Any] = {}
        self.fallback_translations: Dict[str, Any] = {}

        log.debug("initializing-translator", language=language)
        self._load_translations()

    def _load_translations(self):
        """Load translation files."""
        # Prefer configured translation_dir from pyproject.toml if available
        try:
            from .config import NicestLogConfig

            cfg = NicestLogConfig()
            if cfg.translation_dir:
                translations_dir = Path(cfg.translation_dir)
            else:
                translations_dir = Path(__file__).parent.parent.parent / "translations"
        except Exception:
            translations_dir = Path(__file__).parent.parent.parent / "translations"

        # Load fallback (English)
        fallback_file = translations_dir / "en.toml"
        if fallback_file.exists() and toml:
            try:
                self.fallback_translations = toml.load(fallback_file)
                log.debug("loaded-fallback-translations", file=str(fallback_file))
            except Exception as e:
                log.warning(
                    "failed-to-load-fallback", file=str(fallback_file), error=str(e)
                )

        # Load requested language
        lang_file = translations_dir / f"{self.language}.toml"
        if lang_file.exists() and toml:
            try:
                self.translations = toml.load(lang_file)
                log.debug(
                    "loaded-translations",
                    language=self.language,
                    file=str(lang_file),
                    keys_loaded=len(self.translations),
                )
            except Exception as e:
                log.error(
                    "failed-to-load-translations",
                    language=self.language,
                    file=str(lang_file),
                    error=str(e),
                )
        else:
            log.warning(
                "translation-file-not-found",
                language=self.language,
                file=str(lang_file),
                fallback="en",
            )

    def get(self, key: str, section: str = "general", **kwargs) -> str:
        """
        Get translated string with Austrian flair.

        Args:
            key: Translation key
            section: Section in translation file
            **kwargs: Variables for string formatting

        Returns:
            Translated string with variables substituted
        """
        log.debug(
            "getting-translation", key=key, section=section, language=self.language
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
                "translation_missing", key=key, section=section, language=self.language
            )

        # Format with variables
        try:
            if kwargs:
                translation = translation.format(**kwargs)
                log.debug("formatted_translation", key=key, variables=kwargs)
        except Exception as e:
            log.error(
                "translation_formatting_failed",
                key=key,
                translation=translation,
                variables=kwargs,
                error=str(e),
            )

        return translation

    def _get_from_dict(
        self, translations: Dict[str, Any], section: str, key: str
    ) -> Optional[str]:
        """Get translation from nested dictionary."""
        if not translations:
            return None

        if section in translations and key in translations[section]:
            return translations[section][key]

        # Try direct key lookup
        if key in translations:
            return translations[key]

        return None

    def set_language(self, language: str):
        """Change language and reload translations."""
        log.debug("changing_language", old_language=self.language, new_language=language)
        self.language = language
        self._load_translations()


# Global translator instance
_translator: Optional[NicestlogTranslator] = None


def init_i18n(language: str = "en") -> NicestlogTranslator:
    """Initialize internationalization."""
    global _translator

    log.debug("initializing-i18n", language=language)
    _translator = NicestlogTranslator(language)
    return _translator


def get_translator() -> NicestlogTranslator:
    """Get current translator instance."""
    global _translator

    if _translator is None:
        log.debug("auto-initializing-translator", fallback_language="en")
        _translator = NicestlogTranslator()

    return _translator


def t(key: str, section: str = "general", **kwargs) -> str:
    """
    Shorthand for translation.

    Usage:
        t("success")  # -> "Success!"
        t("file_not_found", "errors", filename="test.log")  # -> "File test.log not found!"
    """
    return get_translator().get(key, section, **kwargs)


def set_language(language: str):
    """Set global language."""
    log.debug("setting_global_language", language=language)
    get_translator().set_language(language)


# Austrian shortcuts for fun
def oida(message: str) -> str:
    """Add Austrian flair to any message."""
    return f"Oida, {message}!"


def leiwand(message: str) -> str:
    """Make any message sound Austrian-positive."""
    return f"{message} - leiwand!"


def arsch(message: str) -> str:
    """Austrian way to say something is bad."""
    return f"{message} - des is arsch!"


# Demo function
def demo_translations():
    """Demonstrate translation capabilities."""
    print("🌍 Nicestlog Translation Demo")
    print("=" * 50)

    languages = ["en", "at", "ch", "wollgesisch"]

    for lang in languages:
        print(f"\n🗣️  {lang.upper()}:")
        translator = NicestlogTranslator(lang)

        print(f"   Setup: {translator.get('welcome', 'setup')}")
        print(f"   Success: {translator.get('success', 'general')}")
        print(
            f"   Error: {translator.get('file_not_found', 'errors', filename='test.log')}"
        )
        print(f"   Quality: {translator.get('verdict_leiwand', 'quality')}")
        print(f"   Goodbye: {translator.get('goodbye', 'general')}")

    print("\n🎉 Austrian Shortcuts:")
    print(f"   {oida('das funktioniert')}")
    print(f"   {leiwand('Translation system')}")
    print(f"   {arsch('Broken code')}")


if __name__ == "__main__":
    # Setup logging for demo
    import nicestlog

    nicestlog.init_logging(verbose=True)

    demo_translations()
