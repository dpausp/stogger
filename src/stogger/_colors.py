"""Color constants and detection for terminal output.

Follows the NO_COLOR standard (https://no-color.org/):
- ``NO_COLOR`` env var present (any value) → never emit colors
- ``CLICOLOR_FORCE`` env var present → force colors even on non-TTY
- Otherwise: colors iff stderr is a TTY
"""

import os
import sys

import colorama

RESET_ALL = str(colorama.Style.RESET_ALL)
BRIGHT = str(colorama.Style.BRIGHT)
DIM = str(colorama.Style.DIM)
RED = str(colorama.Fore.RED)
BACKRED = str(colorama.Back.RED)
BLUE = str(colorama.Fore.BLUE)
CYAN = str(colorama.Fore.CYAN)
MAGENTA = str(colorama.Fore.MAGENTA)
YELLOW = str(colorama.Fore.YELLOW)
GREEN = str(colorama.Fore.GREEN)


def should_emit_colors(force: bool | None = None) -> bool:
    """Decide whether to emit ANSI color codes.

    Args:
        force: Explicit override. ``True`` = always colors, ``False`` = never,
            ``None`` = auto-detect via env vars and TTY status.

    Resolution order:
        1. Explicit ``force`` parameter (highest priority)
        2. ``NO_COLOR`` env var (https://no-color.org/) → disable
        3. ``CLICOLOR_FORCE`` env var → enable
        4. ``sys.stderr.isatty()`` → enable on TTY, disable otherwise

    """
    if force is not None:
        return force
    if os.environ.get("NO_COLOR") is not None:
        return False
    if os.environ.get("CLICOLOR_FORCE") is not None:
        return True
    return sys.stderr.isatty()
