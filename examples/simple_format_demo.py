#!/usr/bin/env python3
"""Demo showing the enhanced ConsoleFileRenderer with SimpleFormatSettings."""

import structlog

import nicestlog


def main():
    print("=== Enhanced ConsoleFileRenderer Examples ===\n")

    # Example 1: Default console format
    print("1. Default console format (clean):")
    print("   nicestlog.init_logging()")
    print(
        "   Output: 2025-08-16T00:18:57.672408 I lock-try Looks like another management command is running",
    )
    print()

    # Example 2: With logger brackets and PID using SimpleFormatSettings
    print("2. With additional info:")
    settings = nicestlog.SimpleFormatSettings(
        show_logger_brackets=True,
        show_pid=True,
        show_code_info=False,
        pad_event_width=35,
    )

    nicestlog.init_logging(
        verbose=False,
        syslog_identifier="demo",
        simple_format_settings=settings,
    )

    log = structlog.get_logger("demo")

    print("   settings = nicestlog.SimpleFormatSettings(")
    print("       show_logger_brackets=True,")
    print("       show_pid=True,")
    print("       pad_event_width=35")
    print("   )")
    print("   nicestlog.init_logging(simple_format_settings=settings)")
    print("   Output:")

    log.info(
        "lock-try",
        _replace_msg="Looks like another management command is running",
    )
    log.info("register-system-profile-command", cmd="nix-env")
    log.info("app-starting", version="1.0.0", component="main")

    print()
    print("Available SimpleFormatSettings options:")
    print("- show_logger_brackets: bool = False")
    print("- show_pid: bool = False")
    print("- show_code_info: bool = False")
    print("- timestamp_format: str = 'iso_no_z'  # 'iso', 'iso_no_z', 'custom'")
    print("- custom_timestamp_format: Optional[str] = None")
    print("- pad_event_width: int = 30")


if __name__ == "__main__":
    main()
