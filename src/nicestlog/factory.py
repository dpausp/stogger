"""
Factory functions for building nicestlog components.
"""

import logging
import sys
from typing import Any, List

import structlog
import toml

from .config import NicestLogConfig
from .core import (
    add_caller_info,
    add_pid,
    ConsoleFileRenderer,
    JSONRenderer,
    process_exc_info,
    SelectRenderedString,
    TranslationProcessor,
)


def build_shared_processors(config: NicestLogConfig) -> List[Any]:
    """
    Builds processors that are shared between sync and async modes.
    """
    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        add_pid,
        add_caller_info,
        process_exc_info,
    ]

    # Add PII scrubbing if enabled
    if config.enable_pii_scrubbing:
        from .pii_scrubber import create_pii_processor

        processors.append(
            create_pii_processor(redaction_text=config.pii_redaction_text)
        )
    if config.translation_dir:
        try:
            translation_file = config.translation_dir / f"{config.language}.toml"
            with open(translation_file, "r") as f:
                translations = toml.load(f)
            processors.append(TranslationProcessor(translations))
        except (IOError, toml.TomlDecodeError) as e:
            print(
                f"Warning: failed to load translations from {translation_file}: {e}",
                file=sys.stderr,
            )
    return processors


def build_renderer(config: NicestLogConfig) -> Any:
    """Builds the final renderer based on the log format."""
    if config.log_format == "json":
        renderer = JSONRenderer(min_level="debug" if config.verbose else "info")
    else:
        renderer = ConsoleFileRenderer(
            min_level="debug" if config.verbose else "info",
            show_caller_info=config.show_caller_info,
        )
    return renderer


def configure_stdlib_logging(config: NicestLogConfig, processors: List[Any]):
    """Configures the standard Python logging library."""
    renderer = build_renderer(config)
    
    # Create separate formatters for console and file handlers
    # Each formatter ends with SelectRenderedString to ensure string output
    console_formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=processors,
        processors=[renderer, SelectRenderedString("console")],
    )
    
    file_formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=processors,
        processors=[renderer, SelectRenderedString("file")],
    )

    console_handlers: List[logging.Handler] = []
    file_handlers: List[logging.Handler] = []
    
    if config.logdir:
        try:
            config.logdir.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(
                config.logdir / f"{config.syslog_identifier}.log"
            )
            file_handlers.append(file_handler)
        except (IOError, PermissionError) as e:
            print(f"Warning: failed to set up file logging: {e}", file=sys.stderr)

    if config.log_to_console:
        console_handlers.append(logging.StreamHandler())

    if not console_handlers and not file_handlers:
        return

    if config.async_logging:
        from logging.handlers import QueueHandler, QueueListener
        from queue import Queue

        log_queue: Queue = Queue(-1)
        queue_handler = QueueHandler(log_queue)
        
        # Combine all handlers for the queue listener
        all_handlers = console_handlers + file_handlers
        listener = QueueListener(log_queue, *all_handlers)
        listener.start()
        # TODO: atexit hook to stop listener
        root_logger = logging.getLogger()
        root_logger.addHandler(queue_handler)
        root_logger.setLevel(logging.DEBUG)
        for handler in root_logger.handlers:
            if handler is not queue_handler:
                root_logger.removeHandler(handler)
    else:
        all_handlers = console_handlers + file_handlers
        logging.basicConfig(
            level=logging.DEBUG,
            handlers=all_handlers,
            force=True,  # Override existing config
        )

    # Set appropriate formatters for each handler type
    for handler in logging.root.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
            # Console/stream handler
            handler.setFormatter(console_formatter)
        elif isinstance(handler, logging.FileHandler):
            # File handler
            handler.setFormatter(file_formatter)
        else:
            # Fallback to console formatter for other handler types
            handler.setFormatter(console_formatter)
