"""Vulture whitelist for nicestlog project.

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

# ruff: noqa: F821
# This file intentionally references undefined names for vulture whitelisting

# CLI Commands (Typer framework integration)
tools_generate_service
tools_review
tools_journal
tools_dashboard
i18n_check
docs
init_config_cmd
check
migrate
tools_demo

# CLI helper functions
_display_check_directory_analysis
_analyze_single_file
_analyze_directory
_transform_single_file
_transform_directory
_transform_interactive
_display_patterns
_configure_logging_focused_patterns

# Configuration attributes
log_cmd_output
enable_systemd
systemd_facility
ast_respect_gitignore
ast_max_parameters
ast_logging_focus
ast_enabled_patterns

# Advanced Assistant Public API
add_pattern
transform_directory
analyze_python_file
transform_python_file

# Core Library Variables
warnings_generated
files_transformed
_longest_level

# Utility Functions
format_exc_info
init_i18n
t
find_required_translation_keys
run_i18n_check_cli
analyze_cli_outputs_in_file
edit_code_live

# Interactive Transformer Variables
PREVIEW
user_edited
total_proposals

# Log Analysis Variables
event_patterns
field_patterns
analyze_log_content
verdict_msg

# AST Analysis Variables
arguments
keyword_args
severity

# Project Analyzer Variables
code_snippet
average_complexity
analysis_timestamp

# Web Dashboard Functions
dashboard
get_logs
api_stats
clear_logs

# Dodo/PyDoit Task Functions
task_install
task_format
task_validate_pyproject
task_python_syntax
task_typecheck
task_lint
task_complexity
task_security
task_dead_code
task_test
task_test_cov
task_all_checks
task_check
task_cleanup
task_build
task_pre_commit_install
task_pre_commit_run
task_dev_setup
task_nix_update
task_nix_build
task_nix_shell
task_nix_env_info
task_update
task_update_all
task_loc
DODOFILE_ENCODING

# Sphinx Documentation Configuration
project
copyright
author
release
extensions
templates_path
exclude_patterns
html_theme
html_static_path
html_css_files
myst_enable_extensions
html_theme_options
copybutton_prompt_text
copybutton_prompt_is_regexp
copybutton_only_copy_prompt_lines
copybutton_remove_prompts
intersphinx_mapping
autodoc_default_options
napoleon_google_docstring
napoleon_numpy_docstring
napoleon_include_init_with_doc
napoleon_include_private_with_doc
napoleon_include_special_with_doc
napoleon_use_admonition_for_examples
napoleon_use_admonition_for_notes
napoleon_use_admonition_for_references
napoleon_use_ivar
napoleon_use_param
napoleon_use_rtype
napoleon_preprocess_types
napoleon_type_aliases
napoleon_attr_annotations

# Test Infrastructure (Pytest patterns)
create_pyproject_toml
mock_init_logging
mock_eliot_unavailable
mock_is_dir
mock_is_file
side_effect
nonexistent
__iter__
created
