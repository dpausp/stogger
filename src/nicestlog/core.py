
Core logging functionality for nicestlog.

This module contains the main structlog-based multi-target logging implementation,
as well as the high-level `init_logging` function.
"""
import io
import json
import os
import string
import sys
import syslog
from datetime import datetime
from typing import Any

import structlog

from .config import NicestLogConfig
from .factory import build_loggers, build_processors

try:
    import colorama
except ImportError:
    colorama = None

try:
    from systemd import journal
except ImportError:
    journal = None

_MISSING = "{who} requires the {package} package installed."
_EVENT_WIDTH = 30  # pad the event name to so many characters

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
    RESET_ALL = ""
    BRIGHT = ""
    DIM = ""
    RED = ""
    BACKRED = ""
    BLUE = ""
    CYAN = ""
    MAGENTA = ""
    YELLOW = ""
    GREEN = ""


class PartialFormatter(string.Formatter):
    """
    A string formatter that doesn't break if values are missing or formats are wrong.
    """
    def __init__(self, missing="<missing>", bad_format="<bad format>"):
        self.missing = missing
        self.bad_format = bad_format

    def get_field(self, field_name, args, kwargs):
        try:
            val = super().get_field(field_name, args, kwargs)
        except (KeyError, AttributeError):
            val = (None, field_name)
        return val

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

    def __call__(self, logger, method_name, event_dict):
        msg_key = event_dict.pop("_msg_key", None) or event_dict.get("event")
        template = self.translations.get(msg_key)

        if template:
            event_dict["formatted_message"] = self.formatter.format(template, **event_dict)
        elif replace_msg := event_dict.pop("_replace_msg", None):
            event_dict["formatted_message"] = self.formatter.format(replace_msg, **event_dict)

        return event_dict


class MultiOptimisticLoggerFactory:
    def __init__(self, context, factories):
        self.context = context
        self.factories = factories

    def __call__(self, *args):
        loggers = {k: f() for k, f in self.factories.items()}
        return MultiOptimisticLogger(loggers)


class MultiOptimisticLogger:
    """A logger which distributes messages to multiple loggers."""
    def __init__(self, loggers):
        self.loggers = loggers

    def __repr__(self):
        return f"<MultiOptimisticLogger {[repr(logger) for logger in self.loggers]}>"

    def msg(self, **messages):
        for name, logger in self.loggers.items():
            try:
                line = messages.get(name)
                if line:
                    logger.msg(line)
            except Exception:
                pass  # Be optimistic

    def __getattr__(self, name):
        return self.msg


class DummyJournalLogger:
    def msg(self, message):
        pass


class JournalLogger:
    def msg(self, message):
        if journal:
            journal.send(**message)


class JournalLoggerFactory:
    def __init__(self):
        if journal is None:
            print(_MISSING.format(who=self.__class__.__name__, package="systemd"))

    def __call__(self, *args):
        return DummyJournalLogger() if journal is None else JournalLogger()


class CmdOutputFileRenderer:
    def __call__(self, logger, method_name, event_dict):
        line = event_dict.pop("cmd_output_line", None)
        if line is not None:
            return {"cmd_output_file": line}
        return {}


def prefix(p, line):
    return f"{p}>\t" + line.replace("\n", f"\n{p}>\t")


def _pad(s, length):
    missing = length - len(s)
    return s + " " * (missing if missing > 0 else 0)


class ConsoleFileRenderer:
    """Render `event_dict` nicely aligned, in colors."""
    LEVELS = ["alert", "critical", "error", "warn", "warning", "info", "debug", "trace"]

    def __init__(self, min_level, show_caller_info=False, pad_event=_EVENT_WIDTH):
        self.min_level = self.LEVELS.index(min_level.lower())
        self.show_caller_info = show_caller_info
        if colorama is None:
            print(_MISSING.format(who=self.__class__.__name__, package="colorama"))
        if sys.stdout.isatty() and colorama:
            colorama.init()

        self._pad_event = pad_event
        self._level_to_color = {
            "alert": RED, "critical": RED, "error": RED, "warn": YELLOW,
            "warning": YELLOW, "info": GREEN, "debug": GREEN, "trace": GREEN,
            "notset": BACKRED,
        }
        for key in self._level_to_color:
            self._level_to_color[key] += BRIGHT

    def __call__(self, logger, method_name, event_dict):
        log_settings = event_dict.pop("_log_settings", {})
        if log_settings.get("console_ignore", False):
            return {}

        console_io = io.StringIO()
        log_io = io.StringIO()

        def write(line):
            console_io.write(line)
            clean_line = line
            if RESET_ALL:
                for symb in [RESET_ALL, BRIGHT, DIM, RED, BACKRED, BLUE, CYAN, MAGENTA, YELLOW, GREEN]:
                    clean_line = clean_line.replace(symb, "")
            log_io.write(clean_line)

        formatted_message = event_dict.pop("formatted_message", None)

        if not self.show_caller_info:
            for key in ["code_file", "code_func", "code_lineno", "code_module"]:
                event_dict.pop(key, None)

        if ts := event_dict.pop("timestamp", None):
            write(f"{DIM}{ts}{RESET_ALL} ")

        event_dict.pop("pid", None)

        if level := event_dict.pop("level", None):
            write(f"{self._level_to_color.get(level, '')}{level[0].upper()}{RESET_ALL} ")

        event = event_dict.pop("event")
        write(f"{BRIGHT}{_pad(event, self._pad_event)}{RESET_ALL} ")

        if logger_name := event_dict.pop("logger", None):
            write(f"[{BLUE}{BRIGHT}{logger_name}{RESET_ALL}] ")

        if formatted_message:
            write(formatted_message)
        else:
            write(" ".join(f"{CYAN}{k}{RESET_ALL}={MAGENTA}{repr(v)}{RESET_ALL}"
                for k, v in sorted(event_dict.items())))

        for key in ["cmd_output_line", "_output", "stdout", "stderr", "stack", "exception_traceback"]:
             if value := event_dict.pop(key, None):
                write(f"\n{prefix(key, str(value))}{RESET_ALL}")

        if self.LEVELS.index(method_name.lower()) > self.min_level:
            console_io.seek(0)
            console_io.truncate()

        return {"console": console_io.getvalue(), "file": log_io.getvalue()}


class MultiRenderer:
    def __init__(self, **renderers):
        self.renderers = renderers

    def __call__(self, logger, method_name, event_dict):
        merged_messages = {}
        for renderer in self.renderers.values():
            try:
                if messages := renderer(logger, method_name, event_dict.copy()):
                    merged_messages.update(messages)
            except Exception:
                pass
        return merged_messages


class JSONRenderer:
    """Render `event_dict` as a JSON string."""
    def __call__(self, logger, method_name, event_dict):
        return {"console": json.dumps(event_dict, default=str), "file": json.dumps(event_dict, default=str)}


def add_pid(logger, method_name, event_dict):
    event_dict["pid"] = os.getpid()
    return event_dict


def add_caller_info(logger, method_name, event_dict):
    frame, module_str = structlog._frames._find_first_app_frame_and_name(additional_ignores=[__name__])
    event_dict.update({
        "code_file": frame.f_code.co_filename,
        "code_func": frame.f_code.co_name,
        "code_lineno": frame.f_lineno,
        "code_module": module_str,
    })
    return event_dict


JOURNAL_LEVELS = {
    "alert": syslog.LOG_ALERT, "critical": syslog.LOG_CRIT, "error": syslog.LOG_ERR,
    "warn": syslog.LOG_WARNING, "warning": syslog.LOG_WARNING, "info": syslog.LOG_INFO,
    "debug": syslog.LOG_DEBUG, "trace": syslog.LOG_DEBUG,
}

KEYS_TO_SKIP_IN_JOURNAL_MESSAGE = [
    "_msg_key", "_replace_msg", "code_file", "code_func", "code_lineno",
    "code_module", "event", "exception_traceback", "formatted_message",
    "invocation_id", "level", "message", "output", "pid", "timestamp",
]


class SystemdJournalRenderer:
    def __init__(self, syslog_identifier, syslog_facility=syslog.LOG_LOCAL0):
        self.syslog_identifier = syslog_identifier
        self.syslog_facility = syslog_facility

    def __call__(self, logger, method_name, event_dict):
        if method_name == "trace":
            return {}

        event_dict.pop("_log_settings", None)
        kv_renderer = structlog.processors.KeyValueRenderer(sort_keys=True)
        event_dict["message"] = event_dict["event"]

        if formatted_message := event_dict.pop("formatted_message", None):
            event_dict["message"] += f": {formatted_message}"
        else:
            if kv := kv_renderer(None, None, {k: v for k, v in event_dict.items() if k not in KEYS_TO_SKIP_IN_JOURNAL_MESSAGE}):
                event_dict["message"] += f": {kv}"

        event_dict.pop("timestamp", None)
        event_dict.pop("pid", None)
        code_lineno = event_dict.pop("code_lineno", None)

        event_dict = {k.upper(): self.dump_for_journal(v) for k, v in event_dict.items()}
        event_dict.update({
            "PRIORITY": JOURNAL_LEVELS.get(event_dict.get("LEVEL"), syslog.LOG_INFO),
            "SYSLOG_FACILITY": self.syslog_facility,
            "SYSLOG_IDENTIFIER": self.syslog_identifier,
            "CODE_LINE": code_lineno,
        })
        return {"journal": event_dict}

    def handle_json_fallback(self, obj):
        try:
            return obj.__structlog__()
        except AttributeError:
            return repr(obj)

    def dump_for_journal(self, obj):
        if isinstance(obj, (str, int, float, bool)) or obj is None:
            return obj
        if isinstance(obj, datetime):
            return obj.isoformat()
        return json.dumps(obj, default=self.handle_json_fallback)


def process_exc_info(logger, name, event_dict):
    if exc_info := event_dict.get("exc_info"):
        if isinstance(exc_info, BaseException):
            event_dict["exc_info"] = (type(exc_info), exc_info, exc_info.__traceback__)
        elif not isinstance(exc_info, tuple):
            event_dict["exc_info"] = sys.exc_info()
    return event_dict


def format_exc_info(logger, name, event_dict):
    if exc_info := event_dict.pop("exc_info", None):
        exc_class = exc_info[0]
        event_dict.update({
            "exception_traceback": "".join(structlog.processors._format_exception(exc_info)),
            "exception_msg": str(exc_info[1]),
            "exception_class": f"{exc_class.__module__}.{exc_class.__name__}",
        })
    return event_dict


def init_command_logging(log, logdir=None):
    logger_factory = structlog.get_config()["logger_factory"]
    if not isinstance(logger_factory, MultiOptimisticLoggerFactory):
        return

    logdir = logdir or logger_factory.context.get("logdir")
    if not logdir:
        log.warn("logging-cmd-output-no-logdir", _replace_msg="Cannot set up command logging: No logdir given.")
        return

    if invocation_id := os.environ.get("INVOCATION_ID"):
        formatted_dt = datetime.now().strftime("%Y-%m-%dT%H_%m_%S")
        cmd_log_file_name = logdir / f"{formatted_dt}_build-output_{invocation_id}.log"
    else:
        cmd_log_file_name = logdir / "build-output.log"

    cmd_log_file = open(cmd_log_file_name, "w")
    log.info("logging-cmd-output", _replace_msg=f"External command output goes to: {cmd_log_file.name}")
    logger_factory.factories["cmd_output_file"] = structlog.PrintLoggerFactory(cmd_log_file)


def drop_cmd_output_logfile(log):
    logger_factory = structlog.get_config()["logger_factory"]
    if not isinstance(logger_factory, MultiOptimisticLoggerFactory):
        return

    try:
        cmd_output_file_factory = logger_factory.factories["cmd_output_file"]
        cmd_log_file = cmd_output_file_factory._file
        log.debug("logging-cmd-output-drop", _replace_msg=f"Removing command log file at {cmd_log_file.name}")
        cmd_log_file.close()
        os.unlink(cmd_log_file.name)
    except KeyError:
        log.error("logging-cmd-output-file-not-found", _replace_msg="cmd_output_file logger factory not found.")
        raise


def init_logging(**kwargs: Any):
    """
    Initializes the logging system.

    This is the main entry point for configuring and activating nicestlog.
    It can be configured via a `pyproject.toml` file or by passing
    keyword arguments to this function.

    Keyword arguments will override any settings in the config file.
    """
    config = NicestLogConfig(**kwargs)
    processors = build_processors(config)
    loggers = build_loggers(config)

    context = {}
    if config.logdir:
        context["logdir"] = config.logdir

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.BoundLogger,
        logger_factory=MultiOptimisticLoggerFactory(context, loggers),
        cache_logger_on_first_use=True,
    )

    if config.log_cmd_output:
        if not config.logdir:
            raise ValueError("A logdir is required for command logging.")
        init_command_logging(structlog.get_logger(), config.logdir)


def logging_initialized():
    logger_factory = structlog.get_config().get("logger_factory")
    return isinstance(logger_factory, MultiOptimisticLoggerFactory)
