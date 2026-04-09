"""Color constants for terminal output.

Uses colorama when available with isatty check, falls back to empty strings.
Shared by stogger, stogger-systemd, and stogger-eliot.
"""

import sys

try:
    import colorama
except ImportError:
    colorama = None  # type: ignore[assignment]

if sys.stdout.isatty() and colorama:
    RESET_ALL = colorama.Style.RESET_ALL
    BRIGHT = colorama.Style.BRIGHT
    DIM = colorama.Style.DIM
    RED = colorama.Fore.RED
    BACKRED = colorama.Back.RED
    BLUE = colorama.Fore.BLUE
    CYAN = colorama.Fore.CYAN
    MAGENTA = colorama.Fore.MAGENTA
    YELLOW = colorama.Fore.YELLOW
    GREEN = colorama.Fore.GREEN
else:
    RESET_ALL, BRIGHT, DIM, RED, BACKRED, BLUE, CYAN, MAGENTA, YELLOW, GREEN = ("",) * 10
