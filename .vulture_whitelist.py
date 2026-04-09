"""Vulture whitelist for stogger project.

This file contains known false positives that vulture incorrectly flags as unused code.
These are legitimate code patterns that vulture doesn't understand due to framework
integration, dynamic discovery, or other Python patterns.

Categories of false positives:
1. Typer CLI commands (discovered by decorators)
2. Pytest fixtures and test infrastructure
3. Sphinx documentation configuration
4. Dodo/PyDoit task functions (discovered by naming convention)
5. Configuration attributes (used by users in pyproject.toml)
6. Public API methods (may be used by external tools)
7. Mock objects and side effects in tests
"""

# This file intentionally references undefined names for vulture whitelisting

# CLI Commands (Typer framework integration)
tools_generate_service = None
tools_review = None
tools_journal = None
tools_dashboard = None
i18n_check = None
docs = None
init_config_cmd = None
check = None
migrate = None
tools_demo = None

# CLI helper functions
_display_check_directory_analysis = None
_analyze_single_file = None
_analyze_directory = None
_transform_single_file = None
_transform_directory = None
_transform_interactive = None
_display_patterns = None
_configure_logging_focused_patterns = None

# Configuration attributes
log_cmd_output = None
enable_systemd = None
systemd_facility = None
ast_respect_gitignore = None
ast_max_parameters = None
ast_logging_focus = None
ast_enabled_patterns = None

# Advanced Assistant Public API
add_pattern = None
transform_directory = None
analyze_python_file = None
transform_python_file = None

# Core Library Variables
warnings_generated = None
files_transformed = None
_longest_level = None

# Utility Functions
format_exc_info = None
init_i18n = None
t = None
find_required_translation_keys = None
run_i18n_check_cli = None
analyze_cli_outputs_in_file = None
edit_code_live = None

# Interactive Transformer Variables
PREVIEW = None
user_edited = None
total_proposals = None

# Log Analysis Variables
event_patterns = None
field_patterns = None
analyze_log_content = None
verdict_msg = None

# AST Analysis Variables
arguments = None
keyword_args = None
severity = None

# Project Analyzer Variables
code_snippet = None
average_complexity = None
analysis_timestamp = None

# Web Dashboard Functions
dashboard = None
get_logs = None
api_stats = None
clear_logs = None

# Dodo/PyDoit Task Functions
task_install = None
task_format = None
task_validate_pyproject = None
task_python_syntax = None
task_typecheck = None
task_lint = None
task_complexity = None
task_security = None
task_dead_code = None
task_test = None
task_test_cov = None
task_all_checks = None
task_check = None
task_cleanup = None
task_build = None
task_pre_commit_install = None
task_pre_commit_run = None
task_dev_setup = None
task_nix_update = None
task_nix_build = None
task_nix_shell = None
task_nix_env_info = None
task_update = None
task_update_all = None
task_loc = None
DODOFILE_ENCODING = None

# Sphinx Documentation Configuration
project = None
doc_copyright = None
author = None
release = None
extensions = None
templates_path = None
exclude_patterns = None
html_theme = None
html_static_path = None
html_css_files = None
myst_enable_extensions = None
html_theme_options = None
copybutton_prompt_text = None
copybutton_prompt_is_regexp = None
copybutton_only_copy_prompt_lines = None
copybutton_remove_prompts = None
intersphinx_mapping = None
autodoc_default_options = None
napoleon_google_docstring = None
napoleon_numpy_docstring = None
napoleon_include_init_with_doc = None
napoleon_include_private_with_doc = None
napoleon_include_special_with_doc = None
napoleon_use_admonition_for_examples = None
napoleon_use_admonition_for_notes = None
napoleon_use_admonition_for_references = None
napoleon_use_ivar = None
napoleon_use_param = None
napoleon_use_rtype = None
napoleon_preprocess_types = None
napoleon_type_aliases = None
napoleon_attr_annotations = None

# Test Infrastructure (Pytest patterns)
create_pyproject_toml = None
mock_init_logging = None
mock_eliot_unavailable = None
mock_is_dir = None
mock_is_file = None
side_effect = None
nonexistent = None
__iter__ = None
created = None
