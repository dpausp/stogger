"""
Nicestlog - A sophisticated multi-target structured logging system built on structlog.

This module provides robust, structured logging that works seamlessly across
development and production environments with support for console, file, and
systemd journal output.
"""

from .core import (
    init_logging,
    setup_basic_logging,
    setup_file_logging,
    setup_systemd_logging,
    get_logger,
)

__version__ = "0.1.0"
__all__ = [
    "init_logging",
    "setup_basic_logging",
    "setup_file_logging",
    "setup_systemd_logging",
    "get_logger",
]


def main() -> None:
    """CLI entry point for nicestlog."""
    import sys
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Nicestlog demo and testing")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--logdir", type=Path, help="Directory for file logging")
    parser.add_argument("--demo", action="store_true", help="Run demonstration")

    args = parser.parse_args()

    if args.demo:
        # Run the basic usage examples
        try:
            from examples.basic_usage import main as demo_main
            demo_main()
        except ImportError:
            print("Demo examples not available. Install nicestlog with examples.")
            sys.exit(1)
    else:
        # Setup basic logging and show it works
        log = setup_basic_logging(verbose=args.verbose, app_name="nicestlog-cli")
        log.info("Nicestlog is working!", version=__version__)
        print(f"Nicestlog v{__version__} - Logging system initialized successfully!")
