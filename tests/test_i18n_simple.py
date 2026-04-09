"""Simplified tests for the i18n module functionality."""

from unittest.mock import patch

import pytest

from stogger.i18n import (
    NicestlogTranslator,
    demo_translations,
    get_translator,
    init_i18n,
    set_language,
    t,
)


class TestI18nBasics:
    """Basic tests for i18n functionality."""

    def test_translator_creation(self):
        """Test creating a translator."""
        translator = NicestlogTranslator("en")
        assert translator.language == "en"

    def test_init_i18n(self):
        """Test i18n initialization."""
        translator = init_i18n("en")
        assert isinstance(translator, NicestlogTranslator)

    def test_get_translator(self):
        """Test getting translator instance."""
        translator = get_translator()
        assert isinstance(translator, NicestlogTranslator)

    def test_t_function(self):
        """Test translation shorthand function."""
        result = t("test_key")
        assert isinstance(result, str)

    def test_set_language(self):
        """Test setting global language."""
        set_language("de")
        # Should not raise exception

    def test_demo_translations(self):
        """Test demo function."""
        # Demo runs without printing (uses structured logging)
        demo_translations()
        # Just verify it completes without error


if __name__ == "__main__":
    pytest.main([__file__])
