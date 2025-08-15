"""
Core logging functionality for nicestlog.
"""

import io
import json
import os
import string
import sys
from typing import Any

import structlog

from .config import NicestLogConfig
# Import moved to avoid circular import

try:
    import colorama
except ImportError:
    colorama = None

_MISSING = "{who} requires the {package} package installed."
_EVENT_WIDTH = 30

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
    RESET_ALL, BRIGHT, DIM, RED, BACKRED, BLUE, CYAN, MAGENTA, YELLOW, GREEN = (
        "",
    ) * 10


class PartialFormatter(string.Formatter):
    def __init__(self, missing="<missing>", bad_format="<bad format>"):
        self.missing = missing
        self.bad_format = bad_format

    def get_field(self, field_name, args, kwargs):
        try:
            return super().get_field(field_name, args, kwargs)
        except (KeyError, AttributeError):
            return None, field_name

    def format_field(self, value, format_spec):
        if value is None:
            return self.missing
        try:
            return super().format_field(value, format_spec)
        except ValueError:
            return self.bad_format


class TranslationProcessor:
    def __init__(self, translations):
        self.translations = translations
        self.formatter = PartialFormatter()

    def __call__(self, _, __, event_dict):
        msg_key = event_dict.pop("_msg_key", None) or event_dict.get("event")
        template = self.translations.get(msg_key)
        if template:
            event_dict["event"] = self.formatter.format(template, **event_dict)
        elif replace_msg := event_dict.pop("_replace_msg", None):
            event_dict["event"] = self.formatter.format(replace_msg, **event_dict)
        return event_dict


def _pad(s, length):
    missing = length - len(s)
    return s + " " * (missing if missing > 0 else 0)


class ConsoleFileRenderer:
    LEVELS = ["critical", "error", "warning", "info", "debug", "trace"]

    def __init__(
        self, min_level="info", show_caller_info=False, pad_event=_EVENT_WIDTH
    ):
        self.min_level_idx = self.LEVELS.index(min_level.lower())
        self.show_caller_info = show_caller_info
        if colorama is None:
            print(_MISSING.format(who=self.__class__.__name__, package="colorama"))
        if sys.stdout.isatty() and colorama:
            colorama.init()
        self._level_to_color = {
            "critical": RED,
            "error": RED,
            "warning": YELLOW,
            "info": GREEN,
            "debug": GREEN,
        }

    def __call__(self, _, __, event_dict):
        if self.LEVELS.index(event_dict["level"]) > self.min_level_idx:
            raise structlog.DropEvent

        # Console output with colors
        console_sio = io.StringIO()
        ts = event_dict.get("timestamp", "notimestamp")
        console_sio.write(f"{DIM}{ts}{RESET_ALL} ")

        level = event_dict.get("level")
        console_sio.write(
            f"{self._level_to_color.get(level, '')}{level[0].upper()}{RESET_ALL} "
        )

        event = event_dict.get("event")
        console_sio.write(f"{BRIGHT}{_pad(event, _EVENT_WIDTH)}{RESET_ALL} ")

        logger_name = event_dict.get("logger", "root")
        console_sio.write(f"[{BLUE}{BRIGHT}{logger_name}{RESET_ALL}] ")

        console_sio.write(
            " ".join(
                f"{CYAN}{k}{RESET_ALL}={MAGENTA}{repr(v)}{RESET_ALL}"
                for k, v in sorted(event_dict.items())
                if k not in ["timestamp", "level", "event", "logger"]
            )
        )

        # File output without colors
        file_sio = io.StringIO()
        file_sio.write(f"{ts} ")
        file_sio.write(f"{level[0].upper()} ")
        file_sio.write(f"{_pad(event, _EVENT_WIDTH)} ")
        file_sio.write(f"[{logger_name}] ")
        file_sio.write(
            " ".join(
                f"{k}={repr(v)}"
                for k, v in sorted(event_dict.items())
                if k not in ["timestamp", "level", "event", "logger"]
            )
        )

        return {"console": console_sio.getvalue(), "file": file_sio.getvalue()}


class JSONRenderer:
    """JSON renderer for structured logging output."""

    def __init__(self, min_level="info"):
        self.min_level_idx = ConsoleFileRenderer.LEVELS.index(min_level.lower())

    def __call__(self, _, __, event_dict):
        if ConsoleFileRenderer.LEVELS.index(event_dict["level"]) > self.min_level_idx:
            raise structlog.DropEvent
        json_output = json.dumps(event_dict, default=str)
        return {"console": json_output, "file": json_output}


def add_pid(_, __, event_dict):
    event_dict["pid"] = os.getpid()
    return event_dict


def add_caller_info(_, __, event_dict):
    frame = sys._getframe(5)
    event_dict.update(
        {
            "code_file": frame.f_code.co_filename,
            "code_func": frame.f_code.co_name,
            "code_lineno": frame.f_lineno,
        }
    )
    return event_dict


def process_exc_info(_, __, event_dict):
    if exc_info := event_dict.get("exc_info"):
        if isinstance(exc_info, BaseException):
            event_dict["exc_info"] = (type(exc_info), exc_info, exc_info.__traceback__)
        elif not isinstance(exc_info, tuple):
            event_dict["exc_info"] = sys.exc_info()
    return event_dict


def format_exc_info(_, __, event_dict):
    if exc_info := event_dict.pop("exc_info", None):
        event_dict["exception"] = "".join(
            structlog.processors._format_exception(exc_info)
        )
    return event_dict


class SelectRenderedString:
    """
    Processor that selects a string from the dict returned by ConsoleFileRenderer.

    This ensures that structlog.stdlib.ProcessorFormatter receives a string
    as required, avoiding RuntimeWarnings.
    """

    def __init__(self, key: str = "console"):
        """
        Initialize the selector.

        Args:
            key: Which key to select from the renderer dict ("console" or "file")
        """
        self.key = key

    def __call__(self, _, __, event_dict):
        """Select the appropriate rendered string from the dict."""
        # If it's already a string, pass it through
        if isinstance(event_dict, str):
            return event_dict

        # If it's a dict (from ConsoleFileRenderer), extract the right key
        if isinstance(event_dict, dict):
            val = event_dict.get(self.key)
            if isinstance(val, str):
                return val

        # Fallback: convert to string
        return str(event_dict)


def init_logging(**kwargs: Any):
    # Import here to avoid circular import
    from .factory import build_shared_processors, configure_stdlib_logging

    config = NicestLogConfig(**kwargs)

    shared_processors = build_shared_processors(config)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    configure_stdlib_logging(config, shared_processors)


def logging_initialized():
    return structlog.is_configured()
