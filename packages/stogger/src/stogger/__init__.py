"""Opinionated structured logging built on structlog.

Docs embedded in this package: llms.txt (index, ~50 entries), _sources/ (individual markdown files).
llms-full.txt contains ALL docs in one file but is VERY large (~8000+ lines) — prefer reading
individual files from _sources/ instead.
CLI tools: install stoggertools for ``stoggertools docs`` and ``stoggertools docs-serve``.
"""

__all__ = [
    "JournalLoggerFactory",
    "MultiOptimisticLogger",
    "MultiOptimisticLoggerFactory",
    "StoggerConfig",
    "SystemdJournalRenderer",
    "arsch",
    "create_pii_processor",
    "demo_pii_scrubbing",
    "drop_cmd_output_logfile",
    "get_translator",
    "init_command_logging",
    "init_early_logging",
    "init_i18n",
    "init_logging",
    "leiwand",
    "logging_initialized",
    "oida",
    "t",
]

from pathlib import Path

from .config import StoggerConfig as StoggerConfig
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
from .i18n import arsch as arsch
from .i18n import get_translator as get_translator
from .i18n import init_i18n as init_i18n
from .i18n import leiwand as leiwand
from .i18n import oida as oida
from .i18n import t as t
from .pii_scrubber import create_pii_processor as create_pii_processor
from .pii_scrubber import demo_pii_scrubbing as demo_pii_scrubbing

__docs_path__ = Path(__file__).parent
