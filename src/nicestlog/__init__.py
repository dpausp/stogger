"""
Nicestlog - A sophisticated multi-target structured logging system built on structlog.

This module provides robust, structured logging that works seamlessly across
development and production environments with support for console, file, and
systemd journal output.
"""

from .core import (
    init_logging,
    logging_initialized,
    # The following are for convenience but the API is not stable.
    # Consider them deprecated.
    # setup_basic_logging,
    # setup_file_logging,
    # setup_systemd_logging,
    # get_logger,
)

from .cli import main

__version__ = "0.1.0"
__all__ = [
    "init_logging",
    "logging_initialized",
    "main",
]
