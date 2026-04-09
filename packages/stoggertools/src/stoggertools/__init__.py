"""CLI tooling and convenience entry point for stogger.

Re-exports the full stogger core API plus all stoggertools public symbols.
"""

__all__ = [
    # Re-exported from stogger
    "JournalLogger",
    "JournalLoggerFactory",
    "MultiOptimisticLogger",
    "MultiOptimisticLoggerFactory",
    "StoggerConfig",
    "SystemdJournalRenderer",
    "analyze_python_file",
    "arsch",
    "create_advanced_assistant",
    "create_interactive_transformer",
    "create_live_editor",
    "create_pii_processor",
    "demo_pii_scrubbing",
    "drop_cmd_output_logfile",
    "edit_code_live",
    "get_translator",
    "init_command_logging",
    "init_early_logging",
    "init_i18n",
    "init_logging",
    "leiwand",
    "logging_initialized",
    # Stoggertools own symbols
    "main",
    "migrate_directory",
    "oida",
    "t",
    "transform_directory_interactive",
    "transform_file_interactive",
    "transform_python_file",
]

from stogger import (
    JournalLogger,
    JournalLoggerFactory,
    MultiOptimisticLogger,
    MultiOptimisticLoggerFactory,
    StoggerConfig,
    SystemdJournalRenderer,
    arsch,
    create_pii_processor,
    demo_pii_scrubbing,
    drop_cmd_output_logfile,
    get_translator,
    init_command_logging,
    init_early_logging,
    init_i18n,
    init_logging,
    leiwand,
    logging_initialized,
    oida,
    t,
)

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
from .interactive_transformer import (
    create_interactive_transformer as create_interactive_transformer,
)
from .interactive_transformer import (
    transform_directory_interactive as transform_directory_interactive,
)
from .interactive_transformer import (
    transform_file_interactive as transform_file_interactive,
)
from .live_editor import (
    create_live_editor as create_live_editor,
)
from .live_editor import (
    edit_code_live as edit_code_live,
)
