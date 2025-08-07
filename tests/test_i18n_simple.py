"""
Simplified tests for the i18n module functionality.
"""

import pytest
from unittest.mock import patch

from nicestlog.i18n import (
    NicestlogTranslator,
    init_i18n,
    get_translator,
    t,
    set_language,
    demo_translations,
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

    @patch("builtins.print")
    def test_demo_translations(self, mock_print):
        """Test demo function."""
        demo_translations()
        assert mock_print.called


if __name__ == "__main__":
    pytest.main([__file__])
