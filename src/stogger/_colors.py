"""Color constants for terminal output.

Uses colorama directly (hard dependency).
"""

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
