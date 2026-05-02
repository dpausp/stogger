"""Factory functions for building stogger components."""

import atexit
import logging
import tomllib
from logging.handlers import QueueHandler, QueueListener
from pathlib import Path
from queue import Queue
from typing import Any

import structlog

from .config import StoggerConfig
from .core import (
    ConsoleFileRenderer,
    JSONRenderer,
    SelectRenderedString,
    TranslationProcessor,
    add_caller_info,
    add_pid,
    process_exc_info,
)

# Get a logger for this module
log = structlog.get_logger(__name__)


def build_timestamp_processor(config):
    """Build a TimeStamper processor based on config.format.timestamp_precision.

    Central factory function for timestamp configuration. All TimeStamper
    call sites use this function to ensure consistent utc=True and correct fmt.

    Args:
        config: A config object with a .format attribute containing FormatConfig.

    Returns:
        A TimeStamper processor configured with the appropriate fmt and utc=True.

    """
    precision = config.format.timestamp_precision
    fmt_map = {
        "iso": "iso",
        "iso_seconds": "%Y-%m-%dT%H:%M:%SZ",
        "iso_no_z": "%Y-%m-%dT%H:%M:%S",
        "relative": "iso",
    }
    fmt = fmt_map.get(precision, precision)
    return structlog.processors.TimeStamper(fmt=fmt, utc=True, key="timestamp")


def build_shared_processors(config: StoggerConfig) -> list[Any]:
    """Builds processors that are shared between sync and async modes."""
    if config.verbose:
        log.debug(
            "building-shared-processors",
            pii_scrubbing=config.enable_pii_scrubbing,
            translation_dir=str(config.translation_dir) if config.translation_dir else None,
        )

    processors = [
        structlog.stdlib.add_log_level,
        # Timestamp processor via central factory function
        build_timestamp_processor(config),
        add_pid,
        add_caller_info,
        process_exc_info,
    ]
    if config.translation_dir:
        try:
            translation_file = config.translation_dir / f"{config.language}.toml"
            if config.verbose:
                log.debug(
                    "loading-translations",
                    file=str(translation_file),
                    language=config.language,
                )
            with translation_file.open("rb") as f:
                translations = tomllib.load(f)
            if config.verbose:
                log.debug(
                    "translations-loaded",
                    translation_count=len(translations),
                    language=config.language,
                )
            processors.append(TranslationProcessor(translations))
        except (OSError, tomllib.TOMLDecodeError):
            log.warning(
                "translation-load-failed",
                file=str(translation_file),
                _replace_msg="Failed to load translations from {file}",
            )
    # Add the final renderer
    if config.log_format == "json":
        processors.append(JSONRenderer())
    else:
        processors.append(
            ConsoleFileRenderer(
                format_config=config.format,
                min_level="debug" if config.verbose else "info",
                show_caller_info=config.show_caller_info,
            ),
        )
        # Add SelectRenderedString to convert dict output to string for PrintLogger
        processors.append(SelectRenderedString(key="console"))

    if config.verbose:
        log.debug("shared-processors-built", processor_count=len(processors))
    return processors


def build_renderer(config: StoggerConfig) -> Any:
    """Builds the final renderer based on the log format."""
    log.debug(
        "building-renderer",
        format=config.log_format,
        verbose=config.verbose,
        show_caller_info=config.show_caller_info,
    )

    if config.log_format == "json":
        renderer = JSONRenderer()
        log.debug(
            "json-renderer-created",
            min_level="debug" if config.verbose else "info",
        )
    else:
        # Use ConsoleFileRenderer with direct parameters
        renderer = ConsoleFileRenderer(format_config=config.format)
        log.debug(
            "console-renderer-created",
            min_level="debug" if config.verbose else "info",
        )
    return renderer


def _create_file_handler(logdir: str | Path, syslog_identifier: str) -> logging.FileHandler | None:
    """Attempts to create log directory and file handler. Returns None on failure."""
    try:
        logdir = Path(logdir)
        logdir.mkdir(parents=True, exist_ok=True)
        log_file = logdir / f"{syslog_identifier}.log"
        log.debug("creating-file-handler", log_file=str(log_file))
        file_handler = logging.FileHandler(log_file)
        log.debug("file-logging-enabled", log_file=str(log_file))
        return file_handler
    except (OSError, PermissionError):
        log.exception("file-logging-setup-failed", logdir=str(logdir))
        return None


def _assign_formatters(
    handlers: list[logging.Handler],
    console_formatter: logging.Formatter,
    file_formatter: logging.Formatter | None,
) -> None:
    """Assigns the correct formatter to each handler based on handler type."""
    log.debug("assigning-formatters", handler_count=len(handlers))
    for handler in handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(
            handler,
            logging.FileHandler,
        ):
            handler.setFormatter(console_formatter)
        elif isinstance(handler, logging.FileHandler):
            handler.setFormatter(file_formatter)
        else:
            handler.setFormatter(console_formatter)


def _configure_async_logging(handlers: list[logging.Handler]) -> None:
    """Sets up QueueHandler/QueueListener with atexit cleanup."""
    log.debug("enabling-async-logging", handler_count=len(handlers))
    log_queue: Queue = Queue(-1)
    queue_handler = QueueHandler(log_queue)

    log.debug("starting-queue-listener", handler_count=len(handlers))
    listener = QueueListener(log_queue, *handlers)
    listener.start()

    # Register cleanup handler to stop listener on exit
    def cleanup_listener() -> None:
        log.debug("stopping-queue-listener", reason="atexit")
        listener.stop()

    atexit.register(cleanup_listener)
    root_logger = logging.getLogger()
    root_logger.addHandler(queue_handler)
    root_logger.setLevel(logging.DEBUG)
    for handler in list(root_logger.handlers):
        if handler is not queue_handler:
            root_logger.removeHandler(handler)
    log.debug("async-logging-configured", handler_count=len(handlers))


def _configure_sync_logging(handlers: list[logging.Handler]) -> None:
    """Configures synchronous logging via basicConfig."""
    log.debug("configuring-sync-logging", handler_count=len(handlers))
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=handlers,
        force=True,  # Override existing config
    )
    log.debug("sync-logging-configured", handler_count=len(handlers))


def configure_stdlib_logging(config: StoggerConfig, processors: list[Any]) -> None:
    """Configures the standard Python logging library."""
    log.debug(
        "configuring-stdlib-logging",
        logdir=str(config.logdir) if config.logdir else None,
        log_to_console=config.log_to_console,
        async_logging=config.async_logging,
    )

    renderer = build_renderer(config)

    # Create separate formatters for console and file handlers
    # ConsoleFileRenderer always returns a dict, so we always need SelectRenderedString
    console_formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=processors,
        processors=[renderer, SelectRenderedString("console")],
    )

    file_formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=processors,
        processors=[renderer, SelectRenderedString("file")],
    )

    handlers: list[logging.Handler] = []

    if config.log_to_console:
        log.debug("creating-console-handler", handler_type="console")
        handlers.append(logging.StreamHandler())
        log.debug("console-logging-enabled", handler_type="console")

    if config.logdir:
        file_handler = _create_file_handler(config.logdir, config.syslog_identifier)
        if file_handler is not None:
            handlers.append(file_handler)

    if not handlers:
        log.warning(
            "no-logging-handlers-configured",
            reason="no-console-no-file",
            _replace_msg="No logging handlers configured ({reason})",
        )
        return

    _assign_formatters(handlers, console_formatter, file_formatter)

    if config.async_logging:
        _configure_async_logging(handlers)
    else:
        _configure_sync_logging(handlers)

    log.debug("stdlib-logging-configuration-complete", status="complete")
