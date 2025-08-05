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
        config = self._load_config()
        config.update(kwargs)

        self.verbose: bool = config.get("verbose", False)
        self.logdir: Optional[Path] = Path(config["logdir"]) if config.get("logdir") else None
        self.log_cmd_output: bool = config.get("log_cmd_output", False)
        self.log_to_console: bool = config.get("log_to_console", True)
        self.syslog_identifier: str = config.get("syslog_identifier", "nicestlog")
        self.show_caller_info: bool = config.get("show_caller_info", False)
        self.translation_dir: Optional[Path] = Path(config["translation_dir"]) if config.get("translation_dir") else None
        self.language: str = config.get("language", "en")

    def _load_config(self) -> Dict[str, Any]:
        """Loads nicestlog config from pyproject.toml."""
        pyproject_path = Path("pyproject.toml")
        if not pyproject_path.is_file():
            return {}
        try:
            config = toml.load(pyproject_path)
            return config.get("tool", {}).get("nicestlog", {})
        except toml.TomlDecodeError as e:
            print(f"Error decoding pyproject.toml: {e}", file=sys.stderr)
            return {}
