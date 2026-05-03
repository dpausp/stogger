"""Processor factory functions."""

import structlog

from .config import StoggerConfig


def build_timestamp_processor(config: StoggerConfig) -> structlog.processors.TimeStamper:
    """Build a TimeStamper processor based on config.format.timestamp_precision.

    Central factory function for timestamp configuration. All TimeStamper
    call sites use this function to ensure consistent utc=True and correct fmt.

    Args:
        config: A config object with a .format attribute containing FormatConfig.

    Returns:
        A TimeStamper processor configured with the appropriate fmt and utc=True.

    """
    precision = config.format.timestamp_precision
    fmt_map = {
        "iso": "iso",
        "iso_seconds": "%Y-%m-%dT%H:%M:%SZ",
        "iso_no_z": "%Y-%m-%dT%H:%M:%S",
        "relative": "iso",
    }
    fmt = fmt_map.get(precision, precision)
    return structlog.processors.TimeStamper(fmt=fmt, utc=True, key="timestamp")
