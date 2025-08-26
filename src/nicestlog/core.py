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

# Get a logger for this module
log = structlog.get_logger(__name__)
# Import moved to avoid circular import

try:
    import colorama
except ImportError:
    colorama = None  # type: ignore[assignment]

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
        # Don't log during initialization to avoid recursion
        self.missing = missing
        self.bad_format = bad_format

    def get_field(self, field_name, args, kwargs):
        try:
            return super().get_field(field_name, args, kwargs)
        except (KeyError, AttributeError):
            # Don't log during formatting to avoid recursion
            return None, field_name

    def format_field(self, value, format_spec):
        if value is None:
            # Don't log during formatting to avoid recursion
            return self.missing
        try:
            return super().format_field(value, format_spec)
        except ValueError:
            # Don't log during formatting to avoid recursion
            return self.bad_format


class TranslationProcessor:
    def __init__(self, translations):
        log.debug(
            "initializing-translation-processor", translation_count=len(translations)
        )
        self.translations = translations
        self.formatter = PartialFormatter()

    def __call__(self, _, __, event_dict):
        msg_key = event_dict.pop("_msg_key", None) or event_dict.get("event")

        # Store original event name before any translation
        if "_original_event" not in event_dict:
            event_dict["_original_event"] = event_dict.get("event")

        template = self.translations.get(msg_key)
        if template:
            # Don't log during translation to avoid recursion
            translated_msg = self.formatter.format(template, **event_dict)
            event_dict["_translated_msg"] = translated_msg
            event_dict["event"] = translated_msg  # Keep for compatibility
        elif replace_msg := event_dict.pop("_replace_msg", None):
            # Don't log during translation to avoid recursion
            translated_msg = self.formatter.format(replace_msg, **event_dict)
            event_dict["_translated_msg"] = translated_msg
            event_dict["event"] = translated_msg  # Keep for compatibility
        # No logging for "no translation found" to avoid recursion
        return event_dict


def _pad(s, length):
    missing = length - len(s)
    return s + " " * (missing if missing > 0 else 0)


def prefix(name, s):
    """Add a prefix to each line of a multi-line string."""
    if not s:
        return ""
    lines = s.split("\n")
    if name:
        prefix_str = f"{name}: "
    else:
        prefix_str = ""
    return "\n".join(prefix_str + line for line in lines)


class ConsoleFileRenderer:
    """
    Render `event_dict` nicely aligned, in colors, and ordered with
    specific knowledge about fc.agent structures.
    """

    LEVELS = [
        "alert",
        "critical",
        "error",
        "warn",
        "warning",
        "info",
        "debug",
        "trace",
    ]

    def __init__(
        self,
        min_level="info",
        show_caller_info=False,
        pad_event=_EVENT_WIDTH,
        safe_drop=False,
    ):
        self.min_level = self.LEVELS.index(min_level.lower())
        self.show_caller_info = show_caller_info
        self.safe_drop = (
            safe_drop  # If True, return empty string instead of raising DropEvent
        )
        if colorama is None:
            print(_MISSING.format(who=self.__class__.__name__, package="colorama"))
        if sys.stdout.isatty():
            colorama.init()

        self._pad_event = pad_event
        self._level_to_color = {
            "alert": RED,
            "critical": RED,
            "error": RED,
            "warn": YELLOW,
            "warning": YELLOW,
            "info": GREEN,
            "debug": GREEN,
            "trace": GREEN,
            "notset": BACKRED,
        }
        for key in self._level_to_color.keys():
            self._level_to_color[key] += BRIGHT
        self._longest_level = len(
            max(self._level_to_color.keys(), key=lambda e: len(e))
        )

    def __call__(self, _, method_name, event_dict):
        log_settings = event_dict.pop("_log_settings", {})
        if log_settings.get("console_ignore", False):
            return

        # Determine level name for filtering; fall back to event_dict['level'] when method_name is not provided
        level_name = None
        if isinstance(method_name, str):
            level_name = method_name.lower()
        else:
            lvl = event_dict.get("level")
            if isinstance(lvl, str):
                level_name = lvl.lower()
        # Apply level filtering early to avoid unnecessary work
        if level_name is not None:
            try:
                if self.LEVELS.index(level_name) > self.min_level:
                    if self.safe_drop:
                        return ""
                    else:
                        raise structlog.DropEvent
            except ValueError:
                # Unknown level, do not drop
                pass

        console_io = io.StringIO()
        log_io = io.StringIO()

        def write(line):
            console_io.write(line)
            if RESET_ALL:
                for SYMB in [
                    RESET_ALL,
                    BRIGHT,
                    DIM,
                    RED,
                    BACKRED,
                    BLUE,
                    CYAN,
                    MAGENTA,
                    YELLOW,
                    GREEN,
                ]:
                    line = line.replace(SYMB, "")
            log_io.write(line)

        replace_msg = event_dict.pop("_replace_msg", None)
        if replace_msg:
            formatter = PartialFormatter()
            formatted_replace_msg = formatter.format(replace_msg, **event_dict)
        else:
            formatted_replace_msg = None

        if not self.show_caller_info:
            event_dict.pop("code_file", None)
            event_dict.pop("code_func", None)
            event_dict.pop("code_lineno", None)
            event_dict.pop("code_module", None)

        # Remove internal structlog fields
        event_dict.pop("_from_structlog", None)
        event_dict.pop("_original_event", None)
        event_dict.pop("_record", None)
        event_dict.pop("_translated_msg", None)

        ts = event_dict.pop("timestamp", None)
        if ts is not None:
            write(
                # can be a number if timestamp is UNIXy
                DIM + str(ts) + RESET_ALL + " "
            )
        else:
            # Indicate missing timestamp explicitly for diagnostics/tests
            write(DIM + "notimestamp" + RESET_ALL + " ")

        event_dict.pop("pid", None)

        level = event_dict.pop("level", None)
        if level is not None:
            write(self._level_to_color[level] + level[0].upper() + RESET_ALL + " ")

        event = event_dict.pop("event")
        write(BRIGHT + _pad(event, self._pad_event) + RESET_ALL + " ")

        logger_name = event_dict.pop("logger", "root")
        if logger_name:
            write("[" + BLUE + BRIGHT + logger_name + RESET_ALL + "] ")

        cmd_output_line = event_dict.pop("cmd_output_line", None)
        output = event_dict.pop("_output", None)
        stdout = event_dict.pop("stdout", None)
        stderr = event_dict.pop("stderr", None)
        stack = event_dict.pop("stack", None)
        exception_traceback = event_dict.pop("exception_traceback", None)

        if formatted_replace_msg:
            write(formatted_replace_msg)
        else:
            write(
                " ".join(
                    CYAN
                    + key
                    + RESET_ALL
                    + "="
                    + MAGENTA
                    + repr(event_dict[key])
                    + RESET_ALL
                    for key in sorted(event_dict.keys())
                )
            )

        if cmd_output_line is not None:
            write(DIM + "> " + cmd_output_line + RESET_ALL)

        if output is not None:
            write("\n" + prefix("", "\n" + output + "\n") + RESET_ALL)

        if stdout is not None:
            write("\n" + DIM + prefix("out", "\n" + stdout + "\n") + RESET_ALL)

        if stderr is not None:
            write("\n" + prefix("err", "\n" + stderr + "\n") + RESET_ALL)

        if stack is not None:
            write("\n" + prefix("stack", stack))
            if exception_traceback is not None:
                write("\n" + "=" * 79 + "\n")

        if exception_traceback is not None:
            write("\n" + prefix("exception", exception_traceback))

        # Filter according to the -v switch when outputting to the console.
        # Level filtering is applied at the start of this function.
        # For safety, if method_name is present and below threshold, drop now.
        if isinstance(method_name, str):
            try:
                if self.LEVELS.index(method_name.lower()) > self.min_level:
                    if self.safe_drop:
                        return ""
                    else:
                        raise structlog.DropEvent
            except ValueError:
                pass

        message = {"console": console_io.getvalue(), "file": log_io.getvalue()}
        return message


class SimpleConsoleRenderer:
    """
    Simple console renderer that produces clean format with colors:
    2025-08-16T02:33:01.617569 D system-build-command           cmd='nix-build...'
    2025-08-16T02:33:01.623929 I system-build-started           Nix build command started with PID: 184437
    """

    LEVELS = [
        "alert",
        "critical",
        "error",
        "warn",
        "warning",
        "info",
        "debug",
        "trace",
    ]

    def __init__(self, min_level="info", settings=None):
        from .config import SimpleFormatSettings

        if settings is None:
            settings = SimpleFormatSettings()

        self.min_level = self.LEVELS.index(min_level.lower())
        self.settings = settings

        if colorama is None:
            print(_MISSING.format(who=self.__class__.__name__, package="colorama"))
        if sys.stdout.isatty():
            colorama.init()

        self._level_to_color = {
            "alert": RED,
            "critical": RED,
            "error": RED,
            "warn": YELLOW,
            "warning": YELLOW,
            "info": GREEN,
            "debug": GREEN,
            "trace": GREEN,
            "notset": BACKRED,
        }
        for key in self._level_to_color.keys():
            self._level_to_color[key] += BRIGHT

    def __call__(self, _, method_name, event_dict):
        # Filter according to the -v switch
        if self.LEVELS.index(method_name.lower()) > self.min_level:
            # For stdlib ProcessorFormatter, raising DropEvent can bubble up via logging handlers.
            # Return empty string to drop quietly in that context.
            return ""

        console_io = io.StringIO()
        log_io = io.StringIO()

        def write(line):
            console_io.write(line)
            if RESET_ALL:
                for SYMB in [
                    RESET_ALL,
                    BRIGHT,
                    DIM,
                    RED,
                    BACKRED,
                    BLUE,
                    CYAN,
                    MAGENTA,
                    YELLOW,
                    GREEN,
                ]:
                    line = line.replace(SYMB, "")
            log_io.write(line)

        # Handle _replace_msg
        replace_msg = event_dict.pop("_replace_msg", None)
        if replace_msg:
            formatter = PartialFormatter()
            formatted_replace_msg = formatter.format(replace_msg, **event_dict)
        else:
            formatted_replace_msg = None

        # Remove internal fields and caller info if not needed
        if not self.settings.show_code_info:
            event_dict.pop("code_file", None)
            event_dict.pop("code_func", None)
            event_dict.pop("code_lineno", None)
            event_dict.pop("code_module", None)

        # Remove internal structlog fields
        event_dict.pop("_from_structlog", None)
        event_dict.pop("_original_event", None)
        event_dict.pop("_record", None)
        event_dict.pop("_translated_msg", None)
        event_dict.pop("_log_settings", None)

        # Format timestamp
        ts = event_dict.pop("timestamp", None)
        if ts is not None:
            if self.settings.timestamp_format == "iso_no_z" and str(ts).endswith("Z"):
                ts = str(ts)[:-1]
            write(DIM + str(ts) + RESET_ALL + " ")

        # Remove PID if not wanted
        if not self.settings.show_pid:
            event_dict.pop("pid", None)

        # Format level
        level = event_dict.pop("level", None)
        if level is not None:
            write(self._level_to_color[level] + level[0].upper() + RESET_ALL + " ")

        # Format event name
        event = event_dict.pop("event")
        write(BRIGHT + _pad(event, self.settings.pad_event_width) + RESET_ALL + " ")

        # Handle logger brackets
        logger_name = event_dict.pop("logger", None)
        if self.settings.show_logger_brackets and logger_name is not None:
            write("[" + BLUE + BRIGHT + logger_name + RESET_ALL + "] ")

        # Show either formatted replace message or structured data
        if formatted_replace_msg:
            write(formatted_replace_msg)
        else:
            write(
                " ".join(
                    CYAN
                    + key
                    + RESET_ALL
                    + "="
                    + MAGENTA
                    + repr(event_dict[key])
                    + RESET_ALL
                    for key in sorted(event_dict.keys())
                )
            )

        # Return only the console output as string (no file output for simple renderer)
        return console_io.getvalue()


class JSONRenderer:
    """JSON renderer for structured logging output."""

    def __init__(self, min_level="info"):
        log.debug("initializing-json-renderer", min_level=min_level)
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


def init_logging(simple_format_settings=None, **kwargs: Any):
    """
    Initialize nicestlog with optional simple format settings.

    Args:
        simple_format_settings: SimpleFormatSettings instance or dict with settings
        **kwargs: Other configuration options
    """
    # Import here to avoid circular import
    from .factory import build_shared_processors, configure_stdlib_logging
    from .config import SimpleFormatSettings

    # Handle simple_format_settings parameter
    if simple_format_settings is not None:
        if isinstance(simple_format_settings, dict):
            kwargs["simple_format"] = simple_format_settings
        elif isinstance(simple_format_settings, SimpleFormatSettings):
            # Convert to dict for config
            kwargs["simple_format"] = {
                "show_logger_brackets": simple_format_settings.show_logger_brackets,
                "show_pid": simple_format_settings.show_pid,
                "show_code_info": simple_format_settings.show_code_info,
                "timestamp_format": simple_format_settings.timestamp_format,
                "custom_timestamp_format": simple_format_settings.custom_timestamp_format,
                "pad_event_width": simple_format_settings.pad_event_width,
            }

    # Clear any early initialization to allow full reconfiguration
    if structlog.is_configured():
        structlog.reset_defaults()

    config = NicestLogConfig(**kwargs)

    # Only log debug messages if verbose mode is enabled
    if config.verbose:
        log.debug("initializing-nicestlog", config_kwargs=list(kwargs.keys()))

    shared_processors = build_shared_processors(config)
    if config.verbose:
        log.debug("built-shared-processors", processor_count=len(shared_processors))

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    if config.verbose:
        log.debug("configured-structlog")

    configure_stdlib_logging(config, shared_processors)
    if config.verbose:
        log.debug("logging-initialization-complete")


def init_early_logging():
    """
    Initialize minimal logging format early to reduce uninitialized structlog messages.

    This sets up a basic structlog configuration with minimal dependencies
    to avoid the block of uninitialized messages at startup. Falls back
    gracefully if initialization fails.
    """
    if structlog.is_configured():
        return  # Already configured

    try:
        # Minimal processors for early initialization - avoid logging during setup
        processors = [
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"),
            SimpleConsoleRenderer(min_level="info"),
        ]

        # Configure structlog with minimal setup
        structlog.configure(
            processors=processors,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=False,  # Allow reconfiguration
        )

        # Set up basic stdlib logging
        import logging

        logging.basicConfig(
            level=logging.INFO,  # Allow info messages through
            format="%(message)s",
            force=True,
        )

    except Exception:
        # Graceful fallback - let structlog use its defaults
        # Don't log the error to avoid recursion
        pass


def logging_initialized():
    return structlog.is_configured()
