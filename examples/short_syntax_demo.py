#!/usr/bin/env python3
"""
Demo showing the clean, short logging syntax with log.info() / log.debug()
instead of the longer logger.info() / logger.debug()
"""

import nicestlog
import structlog


def main():
    # Initialize nicestlog
    nicestlog.init_logging(verbose=True, syslog_identifier="short_demo")

    # Get logger with short, clean name
    log = structlog.get_logger("demo")

    # Clean, short syntax examples (good demo patterns)
    log.info("app-starting", version="1.0.0", component="main")
    log.debug("config-loaded", settings_count=42)

    # Processing example
    for i in range(3):
        log.debug("processing-item", item_id=i, status="active")

    log.debug("processing-complete", items_processed=3)

    # Error example
    try:
        pass
    except ZeroDivisionError:
        log.error("division-error", operation="calculate", exc_info=True)

    log.info("app-shutdown", reason="demo-complete")


if __name__ == "__main__":
    main()
