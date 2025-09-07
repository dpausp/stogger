"""Advanced structured logging for Python applications.

This package provides advanced logging capabilities with structured data,
multiple output formats, and integrations for various logging backends.

Modules:
    core: Core logging functionality and initialization
    factory: Factory functions for building log processors
    config: Configuration management
    assistant: Tools for migrating print statements to structured logging
    log_reviewer: Log quality analysis and review
    systemd_integration: Systemd journal integration
    web_dashboard: Web-based log viewing dashboard
    eliot_integration: Integration with Eliot logging
    pii_scrubber: PII (Personally Identifiable Information) scrubbing
    i18n: Internationalization support
    interactive_transformer: Interactive code transformation tools
    journal_viewer: Systemd journal viewer
    linter: Log statement analysis and linting
    live_editor: Live code editing tools
    log_statement_analyzer: Analysis of log statements
    advanced_assistant: Advanced AST-based transformation assistant
    cli: Command-line interface

Functions:
    init_logging: Initialize the logging system
    logging_initialized: Check if logging is configured
    init_early_logging: Initialize minimal logging early in application startup
    init_command_logging: Set up command output logging
    drop_cmd_output_logfile: Remove command output log file
"""

__version__ = "2.1.0"

from .core import (
    init_logging,
    logging_initialized,
    init_early_logging,
    MultiOptimisticLogger,
    MultiOptimisticLoggerFactory,
    SystemdJournalRenderer,
    JournalLogger,
    JournalLoggerFactory,
    init_command_logging,
    drop_cmd_output_logfile,
)
from .config import NicestLogConfig
from .assistant import migrate_directory
from .eliot_integration import setup_eliot_logging
from .i18n import init_i18n, get_translator, t, oida, leiwand, arsch
from .interactive_transformer import (
    create_interactive_transformer,
    transform_file_interactive,
    transform_directory_interactive,
)
from .journal_viewer import main as journal_viewer_main
from .linter import main as linter_main
from .live_editor import create_live_editor, edit_code_live
from .log_reviewer import review_logs_cli
from .log_statement_analyzer import main as log_statement_analyzer_main
from .advanced_assistant import (
    create_advanced_assistant,
    analyze_python_file,
    transform_python_file,
)
from .cli import main
from .web_dashboard import run_dashboard, setup_web_logging, get_log_stats
from .pii_scrubber import create_pii_processor, demo_pii_scrubbing
from .systemd_integration import (
    setup_systemd_logging,
    demo_systemd_integration,
    create_systemd_service_file,
)
