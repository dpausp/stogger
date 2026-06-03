"""Vulture whitelist for stogger project.

This file contains known false positives that vulture incorrectly flags as unused code.

Categories of false positives:
1. Configuration attributes on attrs classes (accessed dynamically via __attrs_init__)
2. Public API functions (used by external consumers)
"""

# This file intentionally references undefined names for vulture whitelisting

# attrs class fields on StoggerConfig — accessed dynamically via __attrs_init__
log_cmd_output = None
systemd_mode = None
systemd_facility = None
ast_respect_gitignore = None
ast_max_parameters = None
ast_logging_focus = None
ast_enabled_patterns = None

# Public API functions
format_exc_info = None
