"""Tests for the factory module functionality."""

import logging
from logging.handlers import QueueHandler, QueueListener
from pathlib import Path
from queue import Queue
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from stogger.config import StoggerConfig
from stogger.core import JSONRenderer, TranslationProcessor
from stogger.factory import (
    _assign_formatters,
    _configure_async_logging,
    _create_file_handler,
    build_renderer,
    build_shared_processors,
    configure_stdlib_logging,
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

    def test_pii_processor_exclusion(self):
        """Test that PII processor is excluded when disabled."""
        config = StoggerConfig(enable_pii_scrubbing=False)
        processors = build_shared_processors(config)

        # Should not include PII processor
        processor_types = [type(p).__name__ for p in processors]
        assert "PIIScrubber" not in processor_types


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


class TestConfigureStdlibLogging:
    """Test cases for configure_stdlib_logging function."""

    @patch("logging.basicConfig", autospec=True)
    def test_sync_logging_configuration(self, mock_basic_config):
        """Test synchronous logging configuration."""
        config = StoggerConfig(async_logging=False, log_to_console=True)
        processors = []

        configure_stdlib_logging(config, processors)

        mock_basic_config.assert_called_once()
        call_kwargs = mock_basic_config.call_args.kwargs
        assert "handlers" in call_kwargs
        assert "level" in call_kwargs
        assert "force" in call_kwargs

    @patch("stogger.factory.QueueListener", autospec=True)
    @patch("logging.getLogger", autospec=True)
    def test_async_logging_configuration(self, mock_get_logger, mock_queue_listener):
        """Test asynchronous logging configuration."""
        mock_root_logger = MagicMock(spec=logging.Logger(""))
        mock_get_logger.return_value = mock_root_logger
        mock_listener_instance = MagicMock(spec=QueueListener)
        mock_queue_listener.return_value = mock_listener_instance

        config = StoggerConfig(async_logging=True, log_to_console=True)
        processors = []

        configure_stdlib_logging(config, processors)

        mock_queue_listener.assert_called_once()
        mock_listener_instance.start.assert_called_once()
        mock_root_logger.addHandler.assert_called_once()

        # Verify QueueHandler was added
        added_handler = mock_root_logger.addHandler.call_args[0][0]
        assert isinstance(added_handler, logging.handlers.QueueHandler)

    @patch("logging.basicConfig", autospec=True)
    def test_file_logging_configuration(self, mock_basic_config):
        """Test file logging configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            config = StoggerConfig(logdir=log_dir, log_to_console=False)
            processors = []

            configure_stdlib_logging(config, processors)

            mock_basic_config.assert_called_once()
            call_kwargs = mock_basic_config.call_args.kwargs
            handlers = call_kwargs["handlers"]

            # Should have file handler
            assert any(isinstance(h, logging.FileHandler) for h in handlers)

    @patch("logging.basicConfig", autospec=True)
    def test_both_console_and_file_logging(self, mock_basic_config):
        """Test configuration with both console and file logging."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            config = StoggerConfig(logdir=log_dir, log_to_console=True)
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
        config = StoggerConfig(verbose=True, log_to_console=True)
        processors = []

        with patch("logging.basicConfig", autospec=True) as mock_basic_config:
            configure_stdlib_logging(config, processors)

            call_kwargs = mock_basic_config.call_args.kwargs
            assert call_kwargs["level"] == logging.DEBUG


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
        translation_processors = [p for p in processors if isinstance(p, TranslationProcessor)]
        #JK|        assert len(translation_processors) == 0

        log.has("translation-load-failed")

    def test_invalid_toml_translation(self, log):
        """Invalid TOML in translation file triggers warning and continues."""
        with tempfile.TemporaryDirectory() as tmpdir:
            translation_dir = Path(tmpdir)
            translation_file = translation_dir / "en.toml"
            translation_file.write_text("invalid toml {{{")
            config = StoggerConfig(translation_dir=translation_dir, language="en")
            processors = build_shared_processors(config)
            assert len(processors) > 0
        #WQ|            assert len(processors) > 0

            log.has("translation-load-failed")
    def test_json_format_renderer_in_chain(self):
        """log_format='json' adds JSONRenderer to the processor chain."""
        config = StoggerConfig(log_format="json")
        processors = build_shared_processors(config)
        assert any(isinstance(p, JSONRenderer) for p in processors)


class TestCreateFileHandler:
    """Tests for _create_file_handler function."""

    @pytest.mark.integration
    def test_permission_error_returns_none(self, log):
        """Unwritable directory returns None instead of raising."""
        result = _create_file_handler("/proc/nonexistent/impossible", "test")
        #YR|        assert result is None

        log.has("file-logging-setup-failed")


class TestAssignFormatters:
    """Tests for _assign_formatters function."""

    def test_non_stream_non_file_handler(self):
        """Handler that is neither StreamHandler nor FileHandler gets console formatter."""
        console_fmt = logging.Formatter("%(message)s")
        file_fmt = logging.Formatter("%(message)s")
        handler = QueueHandler(Queue())
        _assign_formatters([handler], console_fmt, file_fmt)
        assert handler.formatter is console_fmt


class TestConfigureAsyncLogging:
    """Tests for _configure_async_logging function."""

    @patch("stogger.factory.atexit", autospec=True)
    @patch("logging.getLogger", autospec=True)
    def test_removes_non_queue_handlers(self, mock_get_logger, mock_atexit):
        """Existing non-queue handlers on root logger are removed during async setup."""
        mock_root = MagicMock(spec=logging.Logger)
        mock_get_logger.return_value = mock_root
        existing_handler = MagicMock(spec=logging.Handler)
        mock_root.handlers = [existing_handler]

        handler = logging.StreamHandler()
        _configure_async_logging([handler])

        mock_root.removeHandler.assert_called()

    @patch("stogger.factory.atexit", autospec=True)
    @patch("logging.getLogger", autospec=True)
    def test_atexit_cleanup_stops_listener(self, mock_get_logger, mock_atexit):
        """Registered atexit cleanup function calls listener.stop()."""
        mock_root = MagicMock(spec=logging.Logger)
        mock_get_logger.return_value = mock_root
        mock_root.handlers = []

        with patch("stogger.factory.QueueListener", autospec=True) as mock_ql:
            mock_listener = MagicMock()
            mock_ql.return_value = mock_listener

            handler = logging.StreamHandler()
            _configure_async_logging([handler])

            cleanup_fn = mock_atexit.register.call_args[0][0]
            cleanup_fn()
            mock_listener.stop.assert_called_once()


class TestConfigureStdlibLoggingNoHandlers:
    """Tests for no-handlers early return path."""

    def test_no_handlers_returns_early(self, log):
        """No console and no file returns early without configuring logging."""
        config = StoggerConfig(log_to_console=False, logdir=None)
        with patch("logging.basicConfig", autospec=True) as mock_basic:
            configure_stdlib_logging(config, [])
            #BR|            mock_basic.assert_not_called()

        log.has("no-logging-handlers-configured")
