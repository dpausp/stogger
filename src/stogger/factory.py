"""Factory functions for building stogger components."""

import tomllib
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
from .processors import build_timestamp_processor

# Get a logger for this module
log = structlog.get_logger(__name__)


def build_shared_processors(config: StoggerConfig) -> list[Any]:
    """Builds processors that are shared between sync and async modes."""
    if config.verbose:
        log.debug(
            "building-shared-processors",
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
            ),  # ty: ignore[invalid-argument-type]
        )
        # Add SelectRenderedString to convert dict output to string for PrintLogger
        processors.append(SelectRenderedString(key="console"))  # ty: ignore[invalid-argument-type]

    if config.verbose:
        log.debug("shared-processors-built", processor_count=len(processors))
    return processors


def build_renderer(config: StoggerConfig) -> ConsoleFileRenderer | JSONRenderer:
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
