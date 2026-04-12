"""Web dashboard for live log viewing."""

__all__ = [
    "get_log_stats",
    "run_dashboard",
    "setup_web_logging",
]

from .web_dashboard import (
    get_log_stats as get_log_stats,
)
from .web_dashboard import (
    run_dashboard as run_dashboard,
)
from .web_dashboard import (
    setup_web_logging as setup_web_logging,
)
