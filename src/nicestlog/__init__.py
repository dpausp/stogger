"""
Nicestlog - A sophisticated multi-target structured logging system built on structlog.

This module provides robust, structured logging that works seamlessly across
development and production environments with support for console, file, and
systemd journal output.
"""

from .config import NicestLogConfig, SimpleFormatSettings
from .core import init_logging, logging_initialized, init_early_logging
from .factory import build_shared_processors, configure_stdlib_logging
from .cli import main

# Initialize early logging format to reduce uninitialized structlog messages
init_early_logging()

# Ensure package data includes markdown docs when installed from source
try:
    import importlib.resources as _resources  # noqa: F401
except Exception:  # pragma: no cover
    pass

from .linter import main as lint_main
from .eliot_integration import setup_eliot_logging, log_action, log_call
from .pii_scrubber import create_pii_processor, PIIScrubber
from .systemd_integration import (
    setup_systemd_logging,
    detect_systemd_environment,
    create_systemd_service_file,
)

__all__ = [
    "init_logging",
    "init_early_logging",
    "logging_initialized",
    "main",
    "lint_main",
    "NicestLogConfig",
    "SimpleFormatSettings",
    "build_shared_processors",
    "configure_stdlib_logging",
    "setup_eliot_logging",
    "log_action",
    "log_call",
    "create_pii_processor",
    "PIIScrubber",
    "setup_systemd_logging",
    "detect_systemd_environment",
    "create_systemd_service_file",
]
