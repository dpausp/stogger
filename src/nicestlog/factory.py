"""
Factory functions for building nicestlog components.
"""
import logging
import sys
from logging.handlers import QueueHandler, QueueListener
from queue import Queue
from typing import Any, Dict, List

import structlog
import toml

from .config import NicestLogConfig
from .core import (
    add_caller_info,
    add_pid,
    ConsoleFileRenderer,
    JSONRenderer,
    format_exc_info,
    process_exc_info,
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
    if config.translation_dir:
        try:
            translation_file = config.translation_dir / f"{config.language}.toml"
            with open(translation_file, "r") as f:
                translations = toml.load(f)
            processors.append(TranslationProcessor(translations))
        except (IOError, toml.TomlDecodeError) as e:
            print(f"Warning: failed to load translations from {translation_file}: {e}", file=sys.stderr)
    return processors

def build_renderer(config: NicestLogConfig) -> Any:
    """Builds the final renderer based on the log format."""
    if config.log_format == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = ConsoleFileRenderer(
            min_level="trace" if config.verbose else "info",
            show_caller_info=config.show_caller_info,
        )
    return renderer

def configure_stdlib_logging(config: NicestLogConfig, processors: List[Any]):
    """Configures the standard Python logging library."""
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=processors,
        processor=build_renderer(config),
    )

    handlers: List[logging.Handler] = []
    if config.logdir:
        try:
            config.logdir.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(config.logdir / f"{config.syslog_identifier}.log")
            handlers.append(file_handler)
        except (IOError, PermissionError) as e:
            print(f"Warning: failed to set up file logging: {e}", file=sys.stderr)

    if config.log_to_console:
        handlers.append(logging.StreamHandler())

    if not handlers:
        return

    if config.async_logging:
        log_queue: Queue = Queue(-1)
        queue_handler = QueueHandler(log_queue)
        listener = QueueListener(log_queue, *handlers)
        listener.start()
        # TODO: atexit hook to stop listener
        root_logger = logging.getLogger()
        root_logger.addHandler(queue_handler)
        root_logger.setLevel(logging.DEBUG)
        for handler in root_logger.handlers:
            if handler is not queue_handler:
                root_logger.removeHandler(handler)
    else:
        logging.basicConfig(
            level=logging.DEBUG,
            handlers=handlers,
            force=True, # Override existing config
        )
    
    for handler in logging.root.handlers:
        handler.setFormatter(formatter)