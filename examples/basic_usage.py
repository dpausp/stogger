#!/usr/bin/env python3
"""
Basic usage examples for nicestlog.
This script demonstrates various logging patterns and best practices
using the new nicestlog API.
"""

import sys
import time
import subprocess
from pathlib import Path
import structlog
import tempfile

# Import our logging library
import nicestlog

def demonstrate_logging(log):
    """Runs a series of logging examples."""
    log.info("application-started", version="1.0.0")
    log.debug("Debug information", component="main")
    log.warning("This is a warning", threshold=80, current=85)
    log.error("An error occurred", error_code=404)

    # Structured logging with translated messages
    log.info(
        "user-login",
        username="alice",
        user_id=123,
        ip="192.168.1.1",
    )

    # Example of a multiline message from translation file
    log.error("command-failed")

    # Bound logger for context
    request_log = log.bind(request_id="req-12345", user_id=456)
    request_log.info("request-started", method="POST")
    request_log.info("request-completed", status_code=201)

    # Error handling
    try:
        raise ValueError("Something went wrong!")
    except ValueError as e:
        log.error(
            "operation-failed",
            error=str(e),
            exc_info=True,
        )

def main():
    """Run all demonstration functions."""
    print("Nicestlog Usage Examples")
    print("=" * 50)

    # --- Logging initialized from pyproject.toml ---
    # Create a dummy pyproject.toml for the example
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)
        pyproject_path = config_dir / "pyproject.toml"
        with open(pyproject_path, "w") as f:
            f.write("""
[tool.nicestlog]
verbose = true
logdir = "logs"
syslog_identifier = "demo-config"
translation_dir = "translations"
language = "en"
""")
        # Temporarily change directory to where pyproject.toml is
        import os
        original_dir = os.getcwd()
        # Create dummy translations dir
        (config_dir / "translations").mkdir()
        with open(config_dir / "translations" / "en.toml", "w") as f:
            f.write('user-login = "LOGIN: User {username} logged in from {ip}"\n')
            f.write('command-failed = "The command failed!"\n')

        os.chdir(config_dir)
        print(f"\n=== Logging configured from {pyproject_path} ===")
        nicestlog.init_logging()
        log = structlog.get_logger("config_demo")
        demonstrate_logging(log)
        os.chdir(original_dir)


    print("\n" + "=" * 50)
    print("All examples completed successfully!")


    print("\n" + "=" * 50)
    print("All examples completed successfully!")


if __name__ == "__main__":
    main()