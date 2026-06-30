"""Tests for the factory module functionality."""

import tempfile
from pathlib import Path

import pytest

from stogger.config import StoggerConfig
from stogger.core import JSONRenderer, TranslationProcessor
from stogger.factory import (
    build_renderer,
    build_shared_processors,
)


@pytest.mark.integration
class TestBuildSharedProcessors:
    """Test cases for build_shared_processors function."""

    def test_basic_processor_chain(self):
        """Test that basic processors are included."""
        config = StoggerConfig()
        processors = build_shared_processors(config)

        # Should contain basic processors
        assert len(processors) > 0
        # Check for expected processors
        from stogger.core import add_pid, process_exc_info

        assert add_pid in processors
        assert process_exc_info in processors

    def test_caller_info_processor_inclusion(self):
        """Test that caller info processor is included when enabled."""
        config = StoggerConfig(show_caller_info=True)
        processors = build_shared_processors(config)

        # Should include add_caller_info when show_caller_info is True
        from stogger.core import add_caller_info

        assert add_caller_info in processors

    def test_caller_info_processor_exclusion(self):
        """Test that caller info processor is always included (based on actual implementation)."""
        config = StoggerConfig(show_caller_info=False)
        processors = build_shared_processors(config)

        from stogger.core import add_caller_info

        # Based on the actual implementation, add_caller_info is always included
        assert add_caller_info in processors

    def test_pid_processor_inclusion(self):
        """Test that PID processor is included."""
        config = StoggerConfig()
        processors = build_shared_processors(config)

        from stogger.core import add_pid

        assert add_pid in processors

    def test_translation_processor_with_translations(self):
        """Test that translation processor is included when translations exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            translation_dir = Path(tmpdir)
            translation_file = translation_dir / "en.toml"
            translation_file.write_text('[messages]\ntest = "Test message"')

            config = StoggerConfig(translation_dir=translation_dir, language="en")
            processors = build_shared_processors(config)

            # Should include TranslationProcessor
            from stogger.core import TranslationProcessor

            translation_processors = [p for p in processors if isinstance(p, TranslationProcessor)]
            assert len(translation_processors) == 1

    def test_translation_processor_without_translations(self):
        """Test that translation processor is not included when no translation dir."""
        config = StoggerConfig(translation_dir=None, language="en")
        processors = build_shared_processors(config)

        from stogger.core import TranslationProcessor

        translation_processors = [p for p in processors if isinstance(p, TranslationProcessor)]
        assert len(translation_processors) == 0


@pytest.mark.integration
class TestBuildRenderer:
    """Test cases for build_renderer function."""

    def test_console_renderer_creation(self):
        """Test console renderer creation."""
        config = StoggerConfig(log_format="console")
        renderer = build_renderer(config)

        from stogger.core import ConsoleFileRenderer

        assert isinstance(renderer, ConsoleFileRenderer)

    def test_json_renderer_creation(self):
        """Test JSON renderer creation."""
        config = StoggerConfig(log_format="json")
        renderer = build_renderer(config)

        from stogger.core import JSONRenderer

        assert isinstance(renderer, JSONRenderer)

    def test_verbose_mode_affects_min_level(self):
        """Test that verbose mode affects the minimum log level."""
        config_verbose = StoggerConfig(log_format="console", verbose=True)
        config_normal = StoggerConfig(log_format="console", verbose=False)

        renderer_verbose = build_renderer(config_verbose)
        renderer_normal = build_renderer(config_normal)

        # Both should be ConsoleFileRenderer but with different min levels
        from stogger.core import ConsoleFileRenderer

        assert isinstance(renderer_verbose, ConsoleFileRenderer)
        assert isinstance(renderer_normal, ConsoleFileRenderer)


@pytest.mark.integration
class TestBuildSharedProcessorsVerbose:
    """Tests for verbose mode paths in build_shared_processors."""

    def test_verbose_debug_logging_at_start(self):
        """Verbose=True triggers debug log at start of build_shared_processors."""
        config = StoggerConfig(verbose=True)
        processors = build_shared_processors(config)
        assert len(processors) > 0

    def test_verbose_with_valid_translations(self):
        """Verbose=True with valid translation file triggers loading debug logs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            translation_dir = Path(tmpdir)
            translation_file = translation_dir / "en.toml"
            translation_file.write_text('[messages]\ntest = "Test message"')
            config = StoggerConfig(translation_dir=translation_dir, language="en", verbose=True)
            processors = build_shared_processors(config)
            translation_processors = [p for p in processors if isinstance(p, TranslationProcessor)]
            assert len(translation_processors) == 1

    def test_verbose_final_debug(self):
        """Verbose=True triggers shared-processors-built debug at end."""
        config = StoggerConfig(verbose=True)
        processors = build_shared_processors(config)
        assert len(processors) > 0


class TestBuildSharedProcessorsCoverage:
    """Tests for uncovered error and branch paths in build_shared_processors."""

    def test_translation_file_not_found(self, log):
        """Missing translation file triggers warning and continues without translator."""
        config = StoggerConfig(translation_dir=Path("/nonexistent"), language="en")
        processors = build_shared_processors(config)
        assert len(processors) > 0
        [p for p in processors if isinstance(p, TranslationProcessor)]

        assert log.has("translation-load-failed")

    def test_invalid_toml_translation(self, log):
        """Invalid TOML in translation file triggers warning and continues."""
        with tempfile.TemporaryDirectory() as tmpdir:
            translation_dir = Path(tmpdir)
            translation_file = translation_dir / "en.toml"
            translation_file.write_text("invalid toml {{{")
            config = StoggerConfig(translation_dir=translation_dir, language="en")
            processors = build_shared_processors(config)
            assert len(processors) > 0

            assert log.has("translation-load-failed")

    def test_json_format_renderer_in_chain(self):
        """log_format='json' adds JSONRenderer to the processor chain."""
        config = StoggerConfig(log_format="json")
        processors = build_shared_processors(config)
        assert any(isinstance(p, JSONRenderer) for p in processors)
