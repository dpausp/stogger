"""Opinionated structured logging built on structlog.

Embedded docs (``stogger._docs/``): ``llms.txt`` is the index,
``_sources/`` has individual markdown files, ``agent_skill.md``
is the primary agent entry point.

Discover via ``__docs_path__ / '_docs' / 'llms.txt'``.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("stogger")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "LogScope",
    "MultiOptimisticLogger",
    "MultiOptimisticLoggerFactory",
    "StoggerConfig",
    "SystemdJournalRenderer",
    "SystemdMode",
    "build_logger_factories",
    "configure_structlog",
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
from .config import SystemdMode as SystemdMode
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
    build_logger_factories as build_logger_factories,
)
from .core import (
    configure_structlog as configure_structlog,
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
