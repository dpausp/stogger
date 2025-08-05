"""
Nicestlog - A sophisticated multi-target structured logging system built on structlog.

This module provides robust, structured logging that works seamlessly across
development and production environments with support for console, file, and
systemd journal output.
"""

from .config import NicestLogConfig
from .core import init_logging, logging_initialized
from .factory import build_loggers, build_processors
from .cli import main

__version__ = "0.1.0"
__all__ = [
    "init_logging",
    "logging_initialized",
    "main",
    "NicestLogConfig",
    "build_processors",
    "build_loggers",
]