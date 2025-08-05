"""
Nicestlog - A sophisticated multi-target structured logging system built on structlog.

This module provides robust, structured logging that works seamlessly across
development and production environments with support for console, file, and
systemd journal output.
"""

from .config import NicestLogConfig
from .core import init_logging, logging_initialized
from .factory import build_shared_processors, configure_stdlib_logging
from .cli import main
from .linter import main as lint_main
from .eliot_integration import setup_eliot_logging, log_action, log_call

__version__ = "0.1.0"
__all__ = [
    "init_logging",
    "logging_initialized",
    "main",
    "lint_main",
    "NicestLogConfig",
    "build_shared_processors",
    "configure_stdlib_logging",
    "setup_eliot_logging",
    "log_action",
    "log_call",
]