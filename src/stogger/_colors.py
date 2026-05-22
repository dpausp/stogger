"""Color constants for terminal output.

Uses colorama when available with isatty check, falls back to empty strings.
Shared by stogger and stogger-eliot.
"""

import sys

import colorama

if sys.stdout.isatty() and colorama:
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
else:
    RESET_ALL, BRIGHT, DIM, RED, BACKRED, BLUE, CYAN, MAGENTA, YELLOW, GREEN = ("",) * 10
