"""Core logging functionality for stogger."""

import io
import json
import logging
import os
import string
import subprocess
import sys
import syslog
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar

import structlog

try:
    from systemd import journal
except ImportError:
    journal = None

# Import the default settings object
from .config import _default_simple_format_settings

# Get a logger for this module
log = structlog.get_logger(__name__)

from ._colors import BACKRED, BLUE, BRIGHT, CYAN, DIM, GREEN, MAGENTA, RED, RESET_ALL, YELLOW


class PartialFormatter(string.Formatter):
    def __init__(self, missing="<missing>", bad_format="<bad format>") -> None:
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
    def __init__(self, translations) -> None:
        log.debug(
            "initializing-translation-processor",
            translation_count=len(translations),
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
        elif replace_msg := event_dict.pop("_replace_msg", None):
            # Don't log during translation to avoid recursion
            translated_msg = self.formatter.format(replace_msg, **event_dict)
            event_dict["_translated_msg"] = translated_msg
        # No logging for "no translation found" to avoid recursion
        return event_dict


def _pad(s, length):
    missing = length - len(s)
    return s + " " * (max(0, missing))


def prefix(name, s):
    """Add a prefix to each line of a multi-line string."""
    if not s:
        return ""
    lines = s.split("\n")
    prefix_str = f"{name}: " if name else ""
    return "\n".join(prefix_str + line for line in lines)


class ConsoleFileRenderer:
    """Render `event_dict` nicely aligned, in colors, and ordered with
    specific knowledge about fc.agent structures.
    """

    LEVELS: ClassVar[list[str]] = [
        "alert",
        "critical",
        "error",
        "exception",
        "warn",
        "warning",
        "info",
        "debug",
        "trace",
    ]

    def __init__(
        self,
        settings=_default_simple_format_settings,
        min_level=None,
        show_caller_info=None,
    ) -> None:
        """Initialize the ConsoleFileRenderer with settings.

        Args:
            settings: SimpleFormatSettings object with configuration options.
                      Uses default settings if None is provided.
            min_level: Override min_level from settings
            show_caller_info: Override show_code_info from settings

        """
        # Store settings object
        self.settings = settings

        # Override settings with provided parameters
        if min_level is not None:
            self.settings.min_level = min_level
        if show_caller_info is not None:
            self.settings.show_code_info = show_caller_info

        # Initialize instance variables from settings
        self.min_level = self.LEVELS.index(settings.min_level.lower())
        self.show_caller_info = settings.show_code_info
        self.pad_event = settings.pad_event_width
        self.show_logger_brackets = settings.show_logger_brackets
        self.show_pid = settings.show_pid
        self.timestamp_format = settings.timestamp_format

        if sys.stdout.isatty():
            try:
                import colorama

                colorama.init()
            except ImportError:
                pass

        self._level_to_color = {
            "alert": RED,
            "critical": RED,
            "error": RED,
            "exception": RED,
            "warn": YELLOW,
            "warning": YELLOW,
            "info": GREEN,
            "debug": GREEN,
            "trace": GREEN,
            "notset": BACKRED,
        }
        for key in self._level_to_color:
            self._level_to_color[key] += BRIGHT
        self._longest_level = len(
            max(self._level_to_color.keys(), key=len),
        )

    def __call__(self, _, method_name, event_dict):
        log_settings = event_dict.pop("_log_settings", {})
        if log_settings.get("console_ignore", False):
            return None

        # Determine level name for filtering; fall back to event_dict['level'] when method_name is provided
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
                    raise structlog.DropEvent
            except ValueError:
                # Unknown level, do not drop
                pass

        console_io = io.StringIO()
        log_io = io.StringIO()

        def write(line) -> None:
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

        # Handle code information based on settings
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
        event_dict.pop("_log_settings", None)

        # Format timestamp based on settings
        ts = event_dict.pop("timestamp", None)
        if ts is not None:
            # Apply timestamp formatting based on settings
            if self.timestamp_format == "iso_no_z" and str(ts).endswith("Z"):
                ts = str(ts)[:-1]
            write(
                # can be a number if timestamp is UNIXy
                DIM + str(ts) + RESET_ALL + " ",
            )
        else:
            # Indicate missing timestamp explicitly for diagnostics/tests
            write(DIM + "notimestamp" + RESET_ALL + " ")

        # Handle PID based on settings
        pid = event_dict.pop("pid", None)
        if self.show_pid and pid is not None:
            write("[" + DIM + str(pid) + RESET_ALL + "] ")

        level = event_dict.pop("level", None)
        if level is not None:
            write(self._level_to_color[level] + level[0].upper() + RESET_ALL + " ")

        event = event_dict.pop("event")
        write(BRIGHT + _pad(event, self.pad_event) + RESET_ALL + " ")

        # Handle logger brackets based on settings
        logger_name = event_dict.pop("logger", "root")
        if logger_name and self.show_logger_brackets:
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
                    CYAN + key + RESET_ALL + "=" + MAGENTA + repr(event_dict[key]) + RESET_ALL
                    for key in sorted(event_dict.keys())
                ),
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
                    raise structlog.DropEvent
            except ValueError:
                pass

        return {"console": console_io.getvalue(), "file": log_io.getvalue()}


class JSONRenderer:
    """JSON renderer for structured logging output."""

    def __init__(self, min_level="info") -> None:
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
    frame, module_str = structlog._frames._find_first_app_frame_and_name(
        additional_ignores=[__name__],
    )
    event_dict["code_file"] = frame.f_code.co_filename
    event_dict["code_func"] = frame.f_code.co_name
    event_dict["code_lineno"] = frame.f_lineno
    event_dict["code_module"] = module_str
    return event_dict


def process_exc_info(_, __, event_dict):
    if exc_info := event_dict.get("exc_info"):
        if isinstance(exc_info, BaseException):
            event_dict["exc_info"] = (type(exc_info), exc_info, exc_info.__traceback__)
        elif not isinstance(exc_info, tuple):
            event_dict["exc_info"] = sys.exc_info()
    return event_dict


def format_exc_info(_logger, _name, event_dict):
    """Renders exc_info if it's present.
    Expects the tuple format returned by sys.exc_info().
    Compared to structlog's format_exc_info(), this renders the exception
    information separately which is better for structured logging targets.
    """
    exc_info = event_dict.pop("exc_info", None)
    if exc_info is not None:
        exception_class = exc_info[0]
        formatted_traceback = structlog.processors._format_exception(exc_info)
        event_dict["exception_traceback"] = formatted_traceback
        event_dict["exception_msg"] = str(exc_info[1])
        event_dict["exception_class"] = exception_class.__module__ + "." + exception_class.__name__

    return event_dict


class SelectRenderedString:
    """Processor that selects a string from the dict returned by ConsoleFileRenderer.

    This ensures that structlog.stdlib.ProcessorFormatter receives a string
    as required, avoiding RuntimeWarnings.
    """

    def __init__(self, key: str = "console") -> None:
        """Initialize the selector.

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


def log_to_stdlib(_logger, _name, event_dict):
    """Bridge structlog events to Python's standard logging for test capture."""
    # Create a copy of event_dict to avoid modifying the original
    event_dict_copy = event_dict.copy()

    level = event_dict_copy.get("level", "info")
    level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }
    logging_level = level_map.get(level, logging.INFO)
    msg = event_dict_copy.get("_replace_msg", event_dict_copy.get("event", ""))

    # Extract standard logging parameters
    exc_info = event_dict_copy.get("exc_info")

    # Remove non-standard parameters that might cause issues
    for key in list(event_dict_copy.keys()):
        if key not in {"level", "_replace_msg", "event", "exc_info"}:
            event_dict_copy.pop(key, None)

    # Log to standard logging - only pass standard parameters
    if exc_info:
        logging.log(logging_level, msg, exc_info=exc_info)
    else:
        logging.log(logging_level, msg)

    return event_dict


def init_logging(*args, **kwargs) -> None:
    """Initialize logging with the new reference-style signature.

    New signature (reference-style):
        init_logging(verbose, logdir=None, log_cmd_output=False, log_to_console=True,
                     syslog_identifier="stogger", show_caller_info=False)
    """
    # Argument position constants
    ARG_POS_LOGDIR = 1
    ARG_POS_LOG_CMD_OUTPUT = 2
    ARG_POS_LOG_TO_CONSOLE = 3
    ARG_POS_SYSLOG_IDENTIFIER = 4
    ARG_POS_SHOW_CALLER_INFO = 5

    # Handle positional and keyword args
    if len(args) >= 1:
        args[0]
        logdir = args[ARG_POS_LOGDIR] if len(args) > ARG_POS_LOGDIR else kwargs.get("logdir")
        log_cmd_output = (
            args[ARG_POS_LOG_CMD_OUTPUT] if len(args) > ARG_POS_LOG_CMD_OUTPUT else kwargs.get("log_cmd_output", False)
        )
        log_to_console = (
            args[ARG_POS_LOG_TO_CONSOLE] if len(args) > ARG_POS_LOG_TO_CONSOLE else kwargs.get("log_to_console", True)
        )
        syslog_identifier = (
            args[ARG_POS_SYSLOG_IDENTIFIER]
            if len(args) > ARG_POS_SYSLOG_IDENTIFIER
            else kwargs.get("syslog_identifier", "stogger")
        )
        (
            args[ARG_POS_SHOW_CALLER_INFO]
            if len(args) > ARG_POS_SHOW_CALLER_INFO
            else kwargs.get("show_caller_info", False)
        )
    else:
        # All keyword arguments for new style
        kwargs.get("verbose", False)
        logdir = kwargs.get("logdir")
        log_cmd_output = kwargs.get("log_cmd_output", False)
        log_to_console = kwargs.get("log_to_console", True)
        syslog_identifier = kwargs.get("syslog_identifier", "stogger")
        kwargs.get("show_caller_info", False)

    multi_renderer = MultiRenderer(
        journal=SystemdJournalRenderer(syslog_identifier, syslog.LOG_LOCAL1),
        cmd_output_file=CmdOutputFileRenderer(),
        text=ConsoleFileRenderer(),
    )

    processors = [
        add_pid,
        structlog.processors.add_log_level,
        process_exc_info,
        format_exc_info,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.TimeStamper(fmt="iso", utc=False),
        add_caller_info,
        log_to_stdlib,
        multi_renderer,
    ]

    context = {}
    loggers = {}

    if logdir is not None:
        try:
            main_log_file_name = logdir / f"{syslog_identifier}.log"
            main_log_file = main_log_file_name.open("a")
        except PermissionError:
            pass
        else:
            loggers["file"] = structlog.PrintLoggerFactory(main_log_file)
            context["logdir"] = logdir
    if journal:
        loggers["journal"] = JournalLoggerFactory()

    # If the journal module is available and stdout is connected to journal, we
    # shouldn't log to console because output would be duplicated in the journal.
    if log_to_console:
        if journal and os.environ.get("JOURNAL_STREAM"):
            pid = os.getpid()
            # S603/S607: systemctl is a system command, using full path would be better but systemctl is in PATH
            subprocess.run(["systemctl", "status", str(pid)], check=False, capture_output=True, text=True)
        else:
            loggers["console"] = structlog.PrintLoggerFactory(sys.stderr)

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.BoundLogger,
        logger_factory=MultiOptimisticLoggerFactory(context, loggers),
    )

    log = structlog.get_logger()

    if log_cmd_output:
        if not logdir:
            msg = "A logdir is required for command logging."
            raise ValueError(msg)

        init_command_logging(log, logdir)


def init_early_logging() -> None:
    """Initialize minimal logging format early to reduce uninitialized structlog messages.

    This sets up a basic structlog configuration with minimal dependencies
    to avoid the block of uninitialized messages at startup. Falls back
    gracefully if initialization fails.
    """
    if structlog.is_configured():
        return  # Already configured

    with suppress(Exception):
        # Minimal processors for early initialization - avoid logging during setup
        processors = [
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"),
            ConsoleFileRenderer(),
            SelectRenderedString(
                key="console",
            ),  # Convert dict to string for PrintLogger
        ]

        # Configure structlog with minimal setup
        structlog.configure(
            processors=processors,
            logger_factory=structlog.PrintLoggerFactory(),
            wrapper_class=structlog.BoundLogger,
            cache_logger_on_first_use=False,  # Allow reconfiguration
        )

        # Set up basic stdlib logging
        logging.basicConfig(
            level=logging.INFO,  # Allow info messages through
            format="%(message)s",
            force=True,
        )


class DummyJournalLogger:
    """Dummy journal logger when systemd is not available."""

    def msg(self, message) -> None:
        pass


class JournalLogger:
    """Logger that sends messages to systemd journal."""

    def msg(self, message) -> None:
        journal.send(**message)


class JournalLoggerFactory:
    """Factory for creating journal loggers."""

    def __init__(self) -> None:
        if journal is None:
            pass

    def __call__(self, *_args):
        if journal is None:
            return DummyJournalLogger()
        return JournalLogger()


JOURNAL_LEVELS = {
    "alert": syslog.LOG_ALERT,
    "critical": syslog.LOG_CRIT,
    "error": syslog.LOG_ERR,
    "warn": syslog.LOG_WARNING,
    "warning": syslog.LOG_WARNING,
    "info": syslog.LOG_INFO,
    "debug": syslog.LOG_DEBUG,
    "trace": syslog.LOG_DEBUG,
}

KEYS_TO_SKIP_IN_JOURNAL_MESSAGE = [
    "_replace_msg",
    "code_file",
    "code_func",
    "code_lineno",
    "code_module",
    "event",
    "exception_traceback",
    "invocation_id",
    "level",
    "message",
    "output",
    "pid",
    "timestamp",
]


class SystemdJournalRenderer:
    """Renderer for systemd journal output."""

    def __init__(self, syslog_identifier, syslog_facility=syslog.LOG_LOCAL0) -> None:
        self.syslog_identifier = syslog_identifier
        self.syslog_facility = syslog_facility

    def __call__(self, _logger, method_name, event_dict):
        if method_name == "trace":
            return {}

        # Unused
        event_dict.pop("_log_settings", None)

        kv_renderer = structlog.processors.KeyValueRenderer(sort_keys=True)
        event_dict["message"] = event_dict["event"]
        replace_msg = event_dict.pop("_replace_msg", None)

        if replace_msg is not None:
            formatter = PartialFormatter()
            formatted_replace_msg = formatter.format(replace_msg, **event_dict)
            event_dict["message"] += ": " + formatted_replace_msg
        else:
            kv = kv_renderer(
                None,
                None,
                {k: v for k, v in event_dict.items() if k not in KEYS_TO_SKIP_IN_JOURNAL_MESSAGE},
            )

            if kv:
                event_dict["message"] += ": " + kv

        event_dict.pop("timestamp", None)
        event_dict.pop("pid", None)
        code_lineno = event_dict.pop("code_lineno", None)

        event_dict = {k.upper(): self.dump_for_journal(v) for k, v in event_dict.items()}

        event_dict["PRIORITY"] = JOURNAL_LEVELS.get(
            event_dict.get("LEVEL"),
            syslog.LOG_INFO,
        )
        event_dict["SYSLOG_FACILITY"] = self.syslog_facility
        event_dict["SYSLOG_IDENTIFIER"] = self.syslog_identifier
        event_dict["CODE_LINE"] = code_lineno

        return {"journal": event_dict}

    def handle_json_fallback(self, obj):
        """Same as structlog's json fallback.
        Supports obj.__structlog__() for custom object serialization.
        """
        try:
            return obj.__structlog__()
        except AttributeError:
            return repr(obj)

    def dump_for_journal(self, obj):
        """Encode values as JSON, except strings.
        We keep strings unchanged to display line breaks properly in journalctl
        and graylog.
        """
        if isinstance(obj, str):
            return obj
        if isinstance(obj, datetime):
            return datetime.isoformat(obj)
        return json.dumps(obj, default=self.handle_json_fallback)


class CmdOutputFileRenderer:
    """Renderer for command output file logging."""

    def __call__(self, _logger, _method_name, event_dict):
        line = event_dict.pop("cmd_output_line", None)
        if line is not None:
            return {"cmd_output_file": line}
        return {}


class MultiRenderer:
    """Calls multiple renderers with a shallow copy of the event dict and collects
    their messages in a dict with the renderer names as keys and their
    rendered output as values. It doesn't care about the rendered messages
    so different logger types can get different types of messages.
    Normally, this should be placed last in the processors chain.
    Errors in renderers are ignored silently.
    """

    def __init__(self, **renderers) -> None:
        self.renderers = renderers

    def __repr__(self) -> str:
        return f"<MultiRenderer {[repr(logger) for logger in self.renderers]}>"

    def __call__(self, logger, method_name, event_dict):
        merged_messages = {}
        for renderer in self.renderers.values():
            try:
                messages = renderer(logger, method_name, event_dict.copy())
                merged_messages.update(messages)
            except Exception:
                import logging as _stdlib_logging

                _stdlib_logging.getLogger(__name__).exception("Renderer failed, using fallback")

        return merged_messages


class MultiOptimisticLoggerFactory:
    """A logger factory that creates MultiOptimisticLogger instances.
    Stores context and sub-logger factories.
    """

    def __init__(self, context, factories) -> None:
        self.context = context
        self.factories = factories

    def __call__(self, *_args):
        loggers = {k: f() for k, f in self.factories.items()}
        return MultiOptimisticLogger(loggers)


class MultiOptimisticLogger:
    """A logger which distributes messages to multiple loggers.
    It's initialized with a logger dict where the keys are the logger names
    which correspond to the keyword arguments given to the msg method.
    If the logger's name is not present in the arguments, the logger is skipped.
    Errors in sub loggers are ignored silently.
    """

    def __init__(self, loggers) -> None:
        self.loggers = loggers

    def __repr__(self) -> str:
        return f"<MultiOptimisticLogger {[repr(logger) for logger in self.loggers]}>"

    def msg(self, **messages) -> None:
        for name, logger in self.loggers.items():
            try:
                line = messages.get(name)
                if line:
                    logger.msg(line)
            except Exception:
                import logging as _stdlib_logging

                _stdlib_logging.getLogger(__name__).exception("Renderer failed, using fallback")

    def __getattr__(self, name):
        return self.msg


def init_command_logging(log, logdir=None) -> None:
    """Adds a cmd_output_file logger factory to an already configured
    MultiOptimisticLoggerFactory, used for logging Nix command output to a
    separate file.
    Overwrites existing log files. If called from a systemd unit, the file
    name will be made unique by adding the time and systemd invocation ID.

    Other factory types are ignored.
    """
    logger_factory = structlog.get_config()["logger_factory"]

    if not isinstance(logger_factory, MultiOptimisticLoggerFactory):
        return

    if logdir is None:
        logdir = logger_factory.context.get("logdir")

    if logdir is None:
        log.warning(
            "logging-cmd-output-no-logdir",
            _replace_msg=("Cannot set up command logging: No logdir given and factory context has no logdir either."),
        )
        return

    # The invocation ID is normally set by systemd when the script is called
    # from a systemd unit.
    invocation_id = os.environ.get("INVOCATION_ID")
    if invocation_id:
        formatted_dt = datetime.now(UTC).strftime("%Y-%m-%dT%H_%m_%S")
        cmd_log_file_name = logdir / f"fc-agent/{formatted_dt}_build-output_{invocation_id}.log"
    else:
        cmd_log_file_name = logdir / "fc-agent/build-output.log"

    cmd_log_file = cmd_log_file_name.open("w")

    log.info(
        "logging-cmd-output",
        _replace_msg="Nix command output goes to: {cmd_log_file}",
        cmd_log_file=cmd_log_file.name,
    )

    logger_factory.factories["cmd_output_file"] = structlog.PrintLoggerFactory(
        cmd_log_file,
    )


def drop_cmd_output_logfile(log) -> None:
    """Deletes the log file used by the cmd_output_file logger.
    Used to throw away the command log file if nothing interesting has
    happened.
    """
    logger_factory = structlog.get_config()["logger_factory"]

    if not isinstance(logger_factory, MultiOptimisticLoggerFactory):
        return

    try:
        cmd_output_file_factory = logger_factory.factories["cmd_output_file"]
    except KeyError:
        log.exception(
            "logging-cmd-output-file-not-found",
            _replace_msg=(
                "cmd_output_file logger factory not found, there's something "
                "wrong with the logging configuration! Probably "
                "init_command_logging has never been called."
            ),
        )
        raise

    cmd_log_file = cmd_output_file_factory._file

    log.debug(
        "logging-cmd-output-drop",
        _replace_msg="Nothing change; remove command log file at {cmd_log_file}",
        cmd_log_file=cmd_log_file.name,
    )

    cmd_log_file.close()
    Path(cmd_log_file.name).unlink()


def logging_initialized():
    return structlog.is_configured()
