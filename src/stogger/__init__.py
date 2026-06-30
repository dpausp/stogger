"""Opinionated structured logging built on structlog.

Docs embedded in this package: llms.txt (index, ~50 entries), _sources/ (individual markdown files).
llms-full.txt contains ALL docs in one file but is VERY large (~8000+ lines) — prefer reading
individual files from _sources/ instead.
CLI tools: install stoggertools for ``stoggertools docs`` and ``stoggertools docs-serve``.
"""

__all__ = [
    "JournalLoggerFactory",
    "LogScope",
    "MultiOptimisticLogger",
    "MultiOptimisticLoggerFactory",
    "StoggerConfig",
    "SystemdJournalRenderer",
    "drop_cmd_output_logfile",
    "init_command_logging",
    "init_early_logging",
    "init_logging",
    "log_call",
    "log_operation",
    "log_result",
    "log_scope",
    "logging_initialized",
]

from pathlib import Path

from .config import StoggerConfig as StoggerConfig
from .core import (
    JournalLoggerFactory as JournalLoggerFactory,
)
from .core import (
    LogScope as LogScope,
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
    log_call as log_call,
)
from .core import (
    log_operation as log_operation,
)
from .core import (
    log_result as log_result,
)
from .core import (
    log_scope as log_scope,
)
from .core import (
    logging_initialized as logging_initialized,
)

__docs_path__ = Path(__file__).parent
