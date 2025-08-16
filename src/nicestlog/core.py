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
        log.debug("initializing-partial-formatter", missing=missing, bad_format=bad_format)
        self.missing = missing
        self.bad_format = bad_format

    def get_field(self, field_name, args, kwargs):
        try:
            return super().get_field(field_name, args, kwargs)
        except (KeyError, AttributeError):
            log.debug("field-not-found", field_name=field_name)
            return None, field_name

    def format_field(self, value, format_spec):
        if value is None:
            log.debug("using-missing-placeholder", format_spec=format_spec)
            return self.missing
        try:
            return super().format_field(value, format_spec)
        except ValueError:
            log.warning("bad-format-spec", value=value, format_spec=format_spec)
            return self.bad_format


class TranslationProcessor:
    def __init__(self, translations):
        log.info("initializing-translation-processor", translation_count=len(translations))
        self.translations = translations
        self.formatter = PartialFormatter()

    def __call__(self, _, __, event_dict):
        msg_key = event_dict.pop("_msg_key", None) or event_dict.get("event")
        
        # Store original event name before any translation
        if "_original_event" not in event_dict:
            event_dict["_original_event"] = event_dict.get("event")
        
        template = self.translations.get(msg_key)
        if template:
            log.debug("applying-translation", msg_key=msg_key, template=template)
            translated_msg = self.formatter.format(template, **event_dict)
            event_dict["_translated_msg"] = translated_msg
            event_dict["event"] = translated_msg  # Keep for compatibility
        elif replace_msg := event_dict.pop("_replace_msg", None):
            log.debug("applying-replacement-message", replace_msg=replace_msg)
            translated_msg = self.formatter.format(replace_msg, **event_dict)
            event_dict["_translated_msg"] = translated_msg
            event_dict["event"] = translated_msg  # Keep for compatibility
        else:
            log.debug("no-translation-found", msg_key=msg_key)
        return event_dict


def _pad(s, length):
    missing = length - len(s)
    return s + " " * (missing if missing > 0 else 0)


class ConsoleFileRenderer:
    LEVELS = ["critical", "error", "warning", "info", "debug", "trace"]

    def __init__(
        self, min_level="info", show_caller_info=False, pad_event=_EVENT_WIDTH
    ):
        log.info("initializing-console-renderer", min_level=min_level, 
                   show_caller_info=show_caller_info, pad_event=pad_event)
        self.min_level_idx = self.LEVELS.index(min_level.lower())
        self.show_caller_info = show_caller_info
        self.pad_event = pad_event
        if colorama is None:
            log.warning("colorama-not-available", renderer=self.__class__.__name__)
            print(_MISSING.format(who=self.__class__.__name__, package="colorama"))
        if sys.stdout.isatty() and colorama:
            log.debug("initializing-colorama")
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
            log.debug("dropping-event-below-min-level", level=event_dict["level"], min_level_idx=self.min_level_idx)
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


class SimpleConsoleRenderer:
    """
    Simple console renderer that matches the exact format:
    2025-08-16T01:32:44.804383 I lock-try                       Looks like another management command is running
    2025-08-16T01:33:06.429060 D register-system-profile-command cmd='nix-env'
    """
    LEVELS = ["critical", "error", "warning", "info", "debug", "trace"]

    def __init__(self, min_level="info", settings=None):
        from .config import SimpleFormatSettings
        
        if settings is None:
            settings = SimpleFormatSettings()
        
        log.info("initializing-simple-console-renderer", 
                min_level=min_level, 
                show_logger_brackets=settings.show_logger_brackets,
                show_pid=settings.show_pid,
                show_code_info=settings.show_code_info,
                timestamp_format=settings.timestamp_format,
                pad_event_width=settings.pad_event_width)
        
        self.min_level_idx = self.LEVELS.index(min_level.lower())
        self.settings = settings

    def __call__(self, _, __, event_dict):
        if self.LEVELS.index(event_dict["level"]) > self.min_level_idx:
            log.debug("dropping-event-below-min-level", level=event_dict["level"], min_level_idx=self.min_level_idx)
            raise structlog.DropEvent

        # Format timestamp based on settings
        ts = event_dict.get("timestamp", "notimestamp")
        if self.settings.timestamp_format == "iso_no_z" and ts.endswith('Z'):
            ts = ts[:-1]
        elif self.settings.timestamp_format == "custom" and self.settings.custom_timestamp_format:
            # TODO: Implement custom timestamp formatting
            pass

        # Get level as single uppercase letter
        level = event_dict.get("level")
        level_char = level[0].upper()

        # Get event name (original event, not translated message)
        original_event = event_dict.get("_original_event") or event_dict.get("event")
        
        # Check if we have a translated/replaced message
        translated_msg = None
        if "_translated_msg" in event_dict:
            translated_msg = event_dict["_translated_msg"]
        elif "_replace_msg" in event_dict:
            # This shouldn't happen here as TranslationProcessor should handle it
            # but keeping as fallback
            translated_msg = event_dict["_replace_msg"]

        # Build excluded fields list based on settings
        excluded_fields = ["timestamp", "level", "event", "_original_event", "_translated_msg", "_from_structlog", "_record"]
        
        if not self.settings.show_pid:
            excluded_fields.append("pid")
        if not self.settings.show_code_info:
            excluded_fields.extend(["code_file", "code_func", "code_lineno"])
        if not self.settings.show_logger_brackets:
            excluded_fields.append("logger")

        # Determine what to show after the event name
        if translated_msg:
            # Show translated message
            message_part = translated_msg
        else:
            # Show structured data, excluding fields based on settings
            extra_data = {
                k: v for k, v in event_dict.items()
                if k not in excluded_fields
            }
            if extra_data:
                message_part = " ".join(f"{k}={repr(v)}" for k, v in sorted(extra_data.items()))
            else:
                message_part = ""

        # Build the output line
        output_parts = [ts, level_char, _pad(original_event, self.settings.pad_event_width)]
        
        # Add logger brackets if enabled
        if self.settings.show_logger_brackets:
            logger_name = event_dict.get("logger", "root")
            output_parts.append(f"[{logger_name}]")
        
        if message_part:
            output_parts.append(message_part)
        
        output = " ".join(output_parts)
        
        return output


class JSONRenderer:
    """JSON renderer for structured logging output."""

    def __init__(self, min_level="info"):
        log.info("initializing-json-renderer", min_level=min_level)
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

    log.info("initializing-nicestlog", config_kwargs=list(kwargs.keys()))
    config = NicestLogConfig(**kwargs)

    shared_processors = build_shared_processors(config)
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
    log.debug("configured-structlog")

    configure_stdlib_logging(config, shared_processors)
    log.info("logging-initialization-complete")


def logging_initialized():
    return structlog.is_configured()
