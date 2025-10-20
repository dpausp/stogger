"""Advanced structured logging for Python applications.

from __future__ import annotations

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

__version__ = "0.3.4"

__all__ = [
    "JournalLogger",
    "JournalLoggerFactory",
    "MultiOptimisticLogger",
    "MultiOptimisticLoggerFactory",
    "NicestLogConfig",
    "SystemdJournalRenderer",
    "analyze_python_file",
    "arsch",
    "create_advanced_assistant",
    "create_interactive_transformer",
    "create_live_editor",
    "create_pii_processor",
    "create_systemd_service_file",
    "demo_pii_scrubbing",
    "demo_systemd_integration",
    "drop_cmd_output_logfile",
    "edit_code_live",
    "get_log_stats",
    "get_translator",
    "init_command_logging",
    "init_early_logging",
    "init_i18n",
    "init_logging",
    "leiwand",
    "linter_main",
    "log_statement_analyzer_main",
    "logging_initialized",
    "main",
    "migrate_directory",
    "oida",
    "review_logs_cli",
    "run_dashboard",
    "setup_eliot_logging",
    "setup_systemd_logging",
    "setup_web_logging",
    "t",
    "transform_directory_interactive",
    "transform_file_interactive",
    "transform_python_file",
]

from .advanced_assistant import (
    analyze_python_file as analyze_python_file,
)
from .advanced_assistant import (
    create_advanced_assistant as create_advanced_assistant,
)
from .advanced_assistant import (
    transform_python_file as transform_python_file,
)
from .assistant import migrate_directory as migrate_directory
from .cli import main as main
from .config import NicestLogConfig as NicestLogConfig
from .core import (
    JournalLogger as JournalLogger,
)
from .core import (
    JournalLoggerFactory as JournalLoggerFactory,
)
from .core import (
    MultiOptimisticLogger as MultiOptimisticLogger,
)
from .core import (
    MultiOptimisticLoggerFactory as MultiOptimisticLoggerFactory,
)
from .core import (
    SystemdJournalRenderer as SystemdJournalRenderer,
)
from .core import (
    drop_cmd_output_logfile as drop_cmd_output_logfile,
)
from .core import (
    init_command_logging as init_command_logging,
)
from .core import (
    init_early_logging as init_early_logging,
)
from .core import (
    init_logging as init_logging,
)
from .core import (
    logging_initialized as logging_initialized,
)
from .eliot_integration import setup_eliot_logging as setup_eliot_logging
from .i18n import arsch as arsch
from .i18n import get_translator as get_translator
from .i18n import init_i18n as init_i18n
from .i18n import leiwand as leiwand
from .i18n import oida as oida
from .i18n import t as t
from .interactive_transformer import (
    create_interactive_transformer,
    transform_directory_interactive,
    transform_file_interactive,
)
from .linter import main as linter_main
from .live_editor import create_live_editor, edit_code_live
from .log_reviewer import review_logs_cli
from .log_statement_analyzer import main as log_statement_analyzer_main
from .pii_scrubber import create_pii_processor, demo_pii_scrubbing
from .systemd_integration import (
    create_systemd_service_file,
    demo_systemd_integration,
    setup_systemd_logging,
)
from .web_dashboard import get_log_stats, run_dashboard, setup_web_logging
