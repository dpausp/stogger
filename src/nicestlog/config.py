"""
Configuration handling for nicestlog.
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

import tomllib


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
        log.debug("config-loaded-from-file", config_keys=list(config.keys()), config_size=len(config))
        config.update(kwargs)
        log.debug("config-merged-with-kwargs", final_config_keys=list(config.keys()), kwargs_applied=list(kwargs.keys()))

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
        self.log_format: str = config.get("log_format", "console")
        self.async_logging: bool = config.get("async_logging", False)
        self.enable_pii_scrubbing: bool = config.get("enable_pii_scrubbing", True)
        self.pii_redaction_text: str = config.get("pii_redaction_text", "[REDACTED]")
        self.enable_systemd: bool = config.get("enable_systemd", True)
        self.systemd_facility: str = config.get("systemd_facility", None)
        self.src_dir: str = config.get("src_dir", "src")

    def _load_config(self) -> Dict[str, Any]:
        """Loads nicestlog config from pyproject.toml."""
        import logging

        log = logging.getLogger(__name__)

        pyproject_path = Path.cwd() / "pyproject.toml"
        log.debug("searching-for-config", path=str(pyproject_path), exists=pyproject_path.is_file())

        if not pyproject_path.is_file():
            log.info("no-pyproject-found", path=str(pyproject_path), fallback="defaults")
            return {}
        try:
            with pyproject_path.open("rb") as f:
                config = tomllib.load(f)
            nicest_config = config.get("tool", {}).get("nicestlog", {})
            log.info("config-loaded-successfully", 
                    file=str(pyproject_path), 
                    settings_count=len(nicest_config),
                    settings=list(nicest_config.keys()))
            return nicest_config
        except (tomllib.TOMLDecodeError, Exception) as e:
            log.error("config-loading-failed", 
                     file=str(pyproject_path), 
                     error=str(e), 
                     error_type=type(e).__name__)
            print(f"Error decoding pyproject.toml: {e}", file=sys.stderr)
            return {}
