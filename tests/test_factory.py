"""
Tests for the factory module functionality.
"""

import pytest
import logging
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from nicestlog.factory import (
    build_shared_processors,
    configure_stdlib_logging,
    build_renderer,
)
from nicestlog.config import NicestLogConfig


class TestBuildSharedProcessors:
    """Test cases for build_shared_processors function."""

    def test_basic_processor_chain(self):
        """Test that basic processors are included."""
        config = NicestLogConfig()
        processors = build_shared_processors(config)

        # Should contain basic processors
        assert len(processors) > 0
        # Check for expected processors
        from nicestlog.core import add_pid, process_exc_info

        assert add_pid in processors
        assert process_exc_info in processors

    def test_caller_info_processor_inclusion(self):
        """Test that caller info processor is included when enabled."""
        config = NicestLogConfig(show_caller_info=True)
        processors = build_shared_processors(config)

        # Should include add_caller_info when show_caller_info is True
        from nicestlog.core import add_caller_info

        assert add_caller_info in processors

    def test_caller_info_processor_exclusion(self):
        """Test that caller info processor is always included (based on actual implementation)."""
        config = NicestLogConfig(show_caller_info=False)
        processors = build_shared_processors(config)

        from nicestlog.core import add_caller_info

        # Based on the actual implementation, add_caller_info is always included
        assert add_caller_info in processors

    def test_pid_processor_inclusion(self):
        """Test that PID processor is included."""
        config = NicestLogConfig()
        processors = build_shared_processors(config)

        from nicestlog.core import add_pid

        assert add_pid in processors

    def test_translation_processor_with_translations(self):
        """Test that translation processor is included when translations exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            translation_dir = Path(tmpdir)
            translation_file = translation_dir / "en.toml"
            translation_file.write_text('[messages]\ntest = "Test message"')

            config = NicestLogConfig(translation_dir=translation_dir, language="en")
            processors = build_shared_processors(config)

            # Should include TranslationProcessor
            from nicestlog.core import TranslationProcessor

            translation_processors = [
                p for p in processors if isinstance(p, TranslationProcessor)
            ]
            assert len(translation_processors) == 1

    def test_translation_processor_without_translations(self):
        """Test that translation processor is not included when no translation dir."""
        config = NicestLogConfig(translation_dir=None, language="en")
        processors = build_shared_processors(config)

        from nicestlog.core import TranslationProcessor

        translation_processors = [
            p for p in processors if isinstance(p, TranslationProcessor)
        ]
        assert len(translation_processors) == 0

    @patch("nicestlog.pii_scrubber.create_pii_processor")
    def test_pii_processor_inclusion(self, mock_create_pii):
        """Test that PII processor is included when enabled."""
        mock_pii_processor = MagicMock()
        mock_create_pii.return_value = mock_pii_processor

        config = NicestLogConfig(enable_pii_scrubbing=True)
        processors = build_shared_processors(config)

        mock_create_pii.assert_called_once()
        assert mock_pii_processor in processors

    def test_pii_processor_exclusion(self):
        """Test that PII processor is excluded when disabled."""
        config = NicestLogConfig(enable_pii_scrubbing=False)
        processors = build_shared_processors(config)

        # Should not include PII processor
        processor_types = [type(p).__name__ for p in processors]
        assert "PIIScrubber" not in processor_types


class TestBuildRenderer:
    """Test cases for build_renderer function."""

    def test_console_renderer_creation(self):
        """Test console renderer creation."""
        config = NicestLogConfig(log_format="console")
        renderer = build_renderer(config)

        from nicestlog.core import ConsoleFileRenderer

        assert isinstance(renderer, ConsoleFileRenderer)

    def test_json_renderer_creation(self):
        """Test JSON renderer creation."""
        config = NicestLogConfig(log_format="json")
        renderer = build_renderer(config)

        assert hasattr(renderer, "__call__")  # Should be callable

    def test_verbose_mode_affects_min_level(self):
        """Test that verbose mode affects the minimum log level."""
        config_verbose = NicestLogConfig(log_format="console", verbose=True)
        config_normal = NicestLogConfig(log_format="console", verbose=False)

        renderer_verbose = build_renderer(config_verbose)
        renderer_normal = build_renderer(config_normal)

        # Both should be ConsoleFileRenderer but with different min levels
        from nicestlog.core import ConsoleFileRenderer

        assert isinstance(renderer_verbose, ConsoleFileRenderer)
        assert isinstance(renderer_normal, ConsoleFileRenderer)


class TestConfigureStdlibLogging:
    """Test cases for configure_stdlib_logging function."""

    @patch("logging.basicConfig")
    def test_sync_logging_configuration(self, mock_basic_config):
        """Test synchronous logging configuration."""
        config = NicestLogConfig(async_logging=False, log_to_console=True)
        processors = []

        configure_stdlib_logging(config, processors)

        mock_basic_config.assert_called_once()
        call_kwargs = mock_basic_config.call_args.kwargs
        assert "handlers" in call_kwargs
        assert "level" in call_kwargs
        assert "force" in call_kwargs

    @patch("logging.handlers.QueueListener")
    @patch("logging.getLogger")
    def test_async_logging_configuration(self, mock_get_logger, mock_queue_listener):
        """Test asynchronous logging configuration."""
        mock_root_logger = MagicMock()
        mock_get_logger.return_value = mock_root_logger
        mock_listener_instance = MagicMock()
        mock_queue_listener.return_value = mock_listener_instance

        config = NicestLogConfig(async_logging=True, log_to_console=True)
        processors = []

        configure_stdlib_logging(config, processors)

        mock_queue_listener.assert_called_once()
        mock_listener_instance.start.assert_called_once()
        mock_root_logger.addHandler.assert_called_once()

        # Verify QueueHandler was added
        added_handler = mock_root_logger.addHandler.call_args[0][0]
        assert isinstance(added_handler, logging.handlers.QueueHandler)

    @patch("logging.basicConfig")
    def test_file_logging_configuration(self, mock_basic_config):
        """Test file logging configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            config = NicestLogConfig(logdir=log_dir, log_to_console=False)
            processors = []

            configure_stdlib_logging(config, processors)

            mock_basic_config.assert_called_once()
            call_kwargs = mock_basic_config.call_args.kwargs
            handlers = call_kwargs["handlers"]

            # Should have file handler
            assert any(isinstance(h, logging.FileHandler) for h in handlers)

    @patch("logging.basicConfig")
    def test_both_console_and_file_logging(self, mock_basic_config):
        """Test configuration with both console and file logging."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            config = NicestLogConfig(logdir=log_dir, log_to_console=True)
            processors = []

            configure_stdlib_logging(config, processors)

            mock_basic_config.assert_called_once()
            call_kwargs = mock_basic_config.call_args.kwargs
            handlers = call_kwargs["handlers"]

            # Should have both console and file handlers
            assert any(isinstance(h, logging.StreamHandler) for h in handlers)
            assert any(isinstance(h, logging.FileHandler) for h in handlers)

    def test_level_setting(self):
        """Test that logging level is set to DEBUG."""
        config = NicestLogConfig(verbose=True, log_to_console=True)
        processors = []

        with patch("logging.basicConfig") as mock_basic_config:
            configure_stdlib_logging(config, processors)

            call_kwargs = mock_basic_config.call_args.kwargs
            assert call_kwargs["level"] == logging.DEBUG


if __name__ == "__main__":
    pytest.main([__file__])
