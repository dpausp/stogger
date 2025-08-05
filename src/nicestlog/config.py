"""
Configuration handling for nicestlog.
"""
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import toml


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
        log.debug(f"Loaded config from file: {config}")
        config.update(kwargs)
        log.debug(f"Final config after kwargs: {config}")

        self.verbose: bool = config.get("verbose", False)
        self.logdir: Optional[Path] = Path(config["logdir"]) if config.get("logdir") else None
        self.log_cmd_output: bool = config.get("log_cmd_output", False)
        self.log_to_console: bool = config.get("log_to_console", True)
        self.syslog_identifier: str = config.get("syslog_identifier", "nicestlog")
        self.show_caller_info: bool = config.get("show_caller_info", False)
        self.translation_dir: Optional[Path] = Path(config["translation_dir"]) if config.get("translation_dir") else None
        self.language: str = config.get("language", "en")
        self.log_format: str = config.get("log_format", "console")
        self.async_logging: bool = config.get("async_logging", False)

    def _load_config(self) -> Dict[str, Any]:
        """Loads nicestlog config from pyproject.toml."""
        import logging
        log = logging.getLogger(__name__)
        
        pyproject_path = Path.cwd() / "pyproject.toml"
        log.debug(f"Looking for config in: {pyproject_path}")
        
        if not pyproject_path.is_file():
            log.info("No pyproject.toml found, using defaults")
            return {}
        try:
            config = toml.load(pyproject_path)
            nicest_config = config.get("tool", {}).get("nicestlog", {})
            log.info(f"Loaded nicestlog config with {len(nicest_config)} settings")
            return nicest_config
        except toml.TomlDecodeError as e:
            log.error(f"Error decoding pyproject.toml: {e}")
            print(f"Error decoding pyproject.toml: {e}", file=sys.stderr)
            return {}
