"""
Configuration handling for nicestlog.
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass

import tomllib


@dataclass
class SimpleFormatSettings:
    """Settings for the simple console format renderer."""
    show_logger_brackets: bool = False
    show_pid: bool = False
    show_code_info: bool = False
    timestamp_format: str = "iso"  # "iso", "iso_no_z", "custom"
    custom_timestamp_format: Optional[str] = None
    pad_event_width: int = 30


class NicestLogConfig:
    """
    Manages nicestlog configuration by merging pyproject.toml settings
    with keyword arguments.
    """

    def __init__(self, **kwargs: Any):
        """
        Initializes the configuration.

        Args:
            **kwargs: Keyword arguments that can override config file settings.
        """
        import logging

        log = logging.getLogger(__name__)

        config = self._load_config()
        log.debug(f"config-loaded-from-file: {len(config)} keys")
        config.update(kwargs)
        log.debug(f"config-merged-with-kwargs: {len(kwargs)} kwargs applied")

        self.verbose: bool = config.get("verbose", False)
        self.logdir: Optional[Path] = (
            Path(config["logdir"]) if config.get("logdir") else None
        )
        self.log_cmd_output: bool = config.get("log_cmd_output", False)
        self.log_to_console: bool = config.get("log_to_console", True)
        self.syslog_identifier: str = config.get("syslog_identifier", "nicestlog")
        self.show_caller_info: bool = config.get("show_caller_info", False)
        self.translation_dir: Optional[Path] = (
            Path(config["translation_dir"]) if config.get("translation_dir") else None
        )
        self.language: str = config.get("language", "en")
        self.log_format: str = config.get("log_format", "simple")
        self.async_logging: bool = config.get("async_logging", False)
        self.enable_pii_scrubbing: bool = config.get("enable_pii_scrubbing", True)
        self.pii_redaction_text: str = config.get("pii_redaction_text", "[REDACTED]")
        self.enable_systemd: bool = config.get("enable_systemd", True)
        self.systemd_facility: str = config.get("systemd_facility", None)
        self.src_dir: str = config.get("src_dir", "src")
        
        # Simple format settings
        simple_settings = config.get("simple_format", {})
        self.simple_format_settings = SimpleFormatSettings(
            show_logger_brackets=simple_settings.get("show_logger_brackets", False),
            show_pid=simple_settings.get("show_pid", False),
            show_code_info=simple_settings.get("show_code_info", False),
            timestamp_format=simple_settings.get("timestamp_format", "iso_no_z"),
            custom_timestamp_format=simple_settings.get("custom_timestamp_format"),
            pad_event_width=simple_settings.get("pad_event_width", 30)
        )

    def _load_config(self) -> Dict[str, Any]:
        """Loads nicestlog config from pyproject.toml."""
        import logging

        log = logging.getLogger(__name__)

        pyproject_path = Path.cwd() / "pyproject.toml"
        log.debug(f"searching-for-config: {pyproject_path} (exists: {pyproject_path.is_file()})")

        if not pyproject_path.is_file():
            log.info(f"no-pyproject-found: {pyproject_path}, using defaults")
            return {}
        try:
            with pyproject_path.open("rb") as f:
                config = tomllib.load(f)
            nicest_config = config.get("tool", {}).get("nicestlog", {})
            log.info(f"config-loaded-successfully: {pyproject_path} with {len(nicest_config)} settings")
            return nicest_config
        except (tomllib.TOMLDecodeError, Exception) as e:
            log.error(f"config-loading-failed: {pyproject_path} - {e}")
            print(f"Error decoding pyproject.toml: {e}", file=sys.stderr)
            return {}
