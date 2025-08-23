"""
Factory functions for building nicestlog components.
"""

import logging
import sys
from typing import Any, List

import structlog
import toml

from .config import NicestLogConfig

# Get a logger for this module
log = structlog.get_logger(__name__)
from .core import (
    add_caller_info,
    add_pid,
    ConsoleFileRenderer,
    JSONRenderer,
    process_exc_info,
    SelectRenderedString,
    SimpleConsoleRenderer,
    TranslationProcessor,
)


def build_shared_processors(config: NicestLogConfig) -> List[Any]:
    """
    Builds processors that are shared between sync and async modes.
    """
    log.debug(
        "building-shared-processors",
        pii_scrubbing=config.enable_pii_scrubbing,
        translation_dir=str(config.translation_dir) if config.translation_dir else None,
    )

    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        # Always add a timestamp to events so renderers have it available
        structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"),
        add_pid,
        add_caller_info,
        process_exc_info,
    ]

    # Add PII scrubbing if enabled
    if config.enable_pii_scrubbing:
        log.debug("enabling-pii-scrubbing", redaction_text=config.pii_redaction_text)
        from .pii_scrubber import create_pii_processor

        processors.append(
            create_pii_processor(redaction_text=config.pii_redaction_text)
        )
    if config.translation_dir:
        try:
            translation_file = config.translation_dir / f"{config.language}.toml"
            log.debug(
                "loading-translations",
                file=str(translation_file),
                language=config.language,
            )
            with open(translation_file, "r") as f:
                translations = toml.load(f)
            log.info(
                "translations-loaded",
                translation_count=len(translations),
                language=config.language,
            )
            processors.append(TranslationProcessor(translations))
        except (IOError, toml.TomlDecodeError) as e:
            log.warning(
                "translation-load-failed", file=str(translation_file), error=str(e)
            )
            print(
                f"Warning: failed to load translations from {translation_file}: {e}",
                file=sys.stderr,
            )
    log.debug("shared-processors-built", processor_count=len(processors))
    return processors


def build_renderer(config: NicestLogConfig) -> Any:
    """Builds the final renderer based on the log format."""
    log.debug(
        "building-renderer",
        format=config.log_format,
        verbose=config.verbose,
        show_caller_info=config.show_caller_info,
    )

    if config.log_format == "json":
        renderer = JSONRenderer(min_level="debug" if config.verbose else "info")
        log.debug(
            "json-renderer-created", min_level="debug" if config.verbose else "info"
        )
    elif config.log_format == "simple":
        renderer = SimpleConsoleRenderer(
            min_level="debug" if config.verbose else "info",
            settings=config.simple_format_settings,
        )
        log.debug(
            "simple-console-renderer-created",
            min_level="debug" if config.verbose else "info",
        )
    else:
        renderer = ConsoleFileRenderer(
            min_level="debug" if config.verbose else "info",
            show_caller_info=config.show_caller_info,
        )
        log.debug(
            "console-renderer-created", min_level="debug" if config.verbose else "info"
        )
    return renderer


def configure_stdlib_logging(config: NicestLogConfig, processors: List[Any]):
    """Configures the standard Python logging library."""
    log.debug(
        "configuring-stdlib-logging",
        logdir=str(config.logdir) if config.logdir else None,
        log_to_console=config.log_to_console,
        async_logging=config.async_logging,
    )

    renderer = build_renderer(config)

    # Create separate formatters for console and file handlers
    # For SimpleConsoleRenderer, we don't need SelectRenderedString since it returns a string directly
    if config.log_format == "simple":
        console_formatter = structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=processors,
            processors=[renderer],
        )
        file_formatter = structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=processors,
            processors=[renderer],
        )
    else:
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
            log_file = config.logdir / f"{config.syslog_identifier}.log"
            log.debug("creating-file-handler", log_file=str(log_file))
            file_handler = logging.FileHandler(log_file)
            file_handlers.append(file_handler)
            log.debug("file-logging-enabled", log_file=str(log_file))
        except (IOError, PermissionError) as e:
            log.error(
                "file-logging-setup-failed", logdir=str(config.logdir), error=str(e)
            )
            print(f"Warning: failed to set up file logging: {e}", file=sys.stderr)

    if config.log_to_console:
        log.debug("creating-console-handler")
        console_handlers.append(logging.StreamHandler())
        log.debug("console-logging-enabled")

    if not console_handlers and not file_handlers:
        log.warning("no-logging-handlers-configured")
        return

    # Prepare combined handler list and assign formatters before activation
    all_handlers = console_handlers + file_handlers
    for handler in all_handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(
            handler, logging.FileHandler
        ):
            handler.setFormatter(console_formatter)
        elif isinstance(handler, logging.FileHandler):
            handler.setFormatter(file_formatter)
        else:
            handler.setFormatter(console_formatter)

    if config.async_logging:
        log.debug("enabling-async-logging", handler_count=len(all_handlers))
        from logging.handlers import QueueHandler, QueueListener
        from queue import Queue

        log_queue: Queue = Queue(-1)
        queue_handler = QueueHandler(log_queue)

        log.debug("starting-queue-listener", handler_count=len(all_handlers))
        listener = QueueListener(log_queue, *all_handlers)
        listener.start()
        # TODO: atexit hook to stop listener
        root_logger = logging.getLogger()
        root_logger.addHandler(queue_handler)
        root_logger.setLevel(logging.DEBUG)
        for handler in list(root_logger.handlers):
            if handler is not queue_handler:
                root_logger.removeHandler(handler)
        log.debug("async-logging-configured")
    else:
        log.debug("configuring-sync-logging", handler_count=len(all_handlers))
        logging.basicConfig(
            level=logging.DEBUG,
            handlers=all_handlers,
            force=True,  # Override existing config
        )
        log.debug("sync-logging-configured")

    log.debug("stdlib-logging-configuration-complete")
