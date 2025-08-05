"""
Factory functions for building nicestlog components.

These functions provide a "building block" API for advanced users who
want to construct their own logging configuration.
"""
import os
import sys
from typing import Any, Dict, List

import structlog
import toml

from .config import NicestLogConfig
from .core import (
    add_caller_info,
    add_pid,
    CmdOutputFileRenderer,
    ConsoleFileRenderer,
    format_exc_info,
    JournalLoggerFactory,
    MultiRenderer,
    process_exc_info,
    SystemdJournalRenderer,
    TranslationProcessor,
)

try:
    from systemd import journal
except ImportError:
    journal = None


def build_processors(config: NicestLogConfig) -> List[Any]:
    """
    Builds a list of structlog processors based on the provided configuration.
    """
    processors = [
        add_pid,
        structlog.processors.add_log_level,
        process_exc_info,
        format_exc_info,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.TimeStamper(fmt="iso", utc=False),
        add_caller_info,
    ]

    if config.translation_dir:
        try:
            translation_file = config.translation_dir / f"{config.language}.toml"
            with open(translation_file, "r") as f:
                translations = toml.load(f)
            processors.append(TranslationProcessor(translations))
        except (IOError, toml.TomlDecodeError) as e:
            print(f"Warning: failed to load translations from {translation_file}: {e}", file=sys.stderr)

    multi_renderer = MultiRenderer(
        journal=SystemdJournalRenderer(config.syslog_identifier),
        cmd_output_file=CmdOutputFileRenderer(),
        text=ConsoleFileRenderer(
            min_level="trace" if config.verbose else "info",
            show_caller_info=config.show_caller_info,
        ),
    )
    processors.append(multi_renderer)

    return processors


def build_loggers(config: NicestLogConfig) -> Dict[str, Any]:
    """
    Builds a dictionary of logger factories based on the provided configuration.
    """
    loggers: Dict[str, Any] = {}

    if config.logdir:
        try:
            config.logdir.mkdir(parents=True, exist_ok=True)
            main_log_file_name = config.logdir / f"{config.syslog_identifier}.log"
            main_log_file = open(main_log_file_name, "a")
            loggers["file"] = structlog.PrintLoggerFactory(main_log_file)
        except (IOError, PermissionError) as e:
            print(f"Warning: failed to set up logging to {main_log_file_name}: {e}", file=sys.stderr)

    if journal:
        loggers["journal"] = JournalLoggerFactory()

    if config.log_to_console:
        if journal and sys.stdout.isatty() and "JOURNAL_STREAM" in os.environ:
            print("Detected systemd journal context. Disabling console output.", file=sys.stderr)
        else:
            loggers["console"] = structlog.PrintLoggerFactory(sys.stderr)

    return loggers
