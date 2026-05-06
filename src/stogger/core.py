"""Core logging functionality for stogger."""

import io
import json
import logging
import os
import string
import sys
import syslog
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar

import structlog

from ._types import EventDict
from .config import FormatConfig, StoggerConfig
from .processors import build_timestamp_processor

# Get a logger for this module
log = structlog.get_logger(__name__)

from ._colors import BACKRED, BLUE, BRIGHT, CYAN, DIM, GREEN, MAGENTA, RED, RESET_ALL, YELLOW
from ._decorators import LogScope, log_call, log_operation, log_result, log_scope  # noqa: F401


class PartialFormatter(string.Formatter):
    def __init__(self, missing="<missing>", bad_format="<bad format>") -> None:
        # Don't log during initialization to avoid recursion
        self.missing = missing
        self.bad_format = bad_format

    def get_field(self, field_name, args, kwargs):
        try:
            return super().get_field(field_name, args, kwargs)
        except (KeyError, AttributeError):
            log.debug("format-field-missing", field_name=field_name)
            return None, field_name

    def format_field(self, value, format_spec):
        if value is None:
            # Don't log during formatting to avoid recursion
            return self.missing
        try:
            return super().format_field(value, format_spec)
        except (ValueError, TypeError):  # TypeError: format spec on None returns "None{spec}" which is misleading
            log.debug("format-field-bad-format", value=value, format_spec=format_spec)
            return self.bad_format


class TranslationProcessor:
    def __init__(self, translations) -> None:
        log.debug(
            "initializing-translation-processor",
            translation_count=len(translations),
        )
        self.translations = translations
        self.formatter = PartialFormatter()

    def __call__(self, _logger: object, _method_name: str, event_dict: EventDict) -> EventDict:  # stogger: ignore
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


def prefix(name, s):  # stogger: ignore complexity-needs-log
    """Add a prefix to each line of a multi-line string."""
    if not s:
        return ""
    lines = s.split("\n")
    prefix_str = f"{name}: " if name else ""
    return "\n".join(prefix_str + line for line in lines)


class ConsoleFileRenderer:
    """Render `event_dict` nicely aligned, in colors, and ordered with
    specific knowledge about stogger structures.
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

    def __init__(  # stogger: ignore complexity-needs-log
        self,
        format_config=None,
        min_level=None,
        show_caller_info=None,
    ) -> None:
        """Initialize the ConsoleFileRenderer with format_config.

        Args:
            format_config: FormatConfig object with format settings.
                      Uses default FormatConfig() if None is provided.
            min_level: Override min_level from format_config
            show_caller_info: Override show_code_info from format_config

        """
        # Use provided FormatConfig or create default
        if format_config is None:
            format_config = FormatConfig()
        self.format_config = format_config

        # Derive effective values from format_config + overrides
        effective_min_level = min_level if min_level is not None else format_config.min_level
        effective_show_code_info = show_caller_info if show_caller_info is not None else format_config.show_code_info

        # Initialize instance variables
        self.min_level = self.LEVELS.index(effective_min_level.lower())
        self.show_caller_info = effective_show_code_info
        self.pad_event = format_config.pad_event_width
        self.show_logger_brackets = False
        self.show_pid = False
        self.timestamp_format = format_config.timestamp_precision

        sys.stdout.isatty()

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

    def _resolve_level_name(self, method_name, event_dict):  # stogger: ignore complexity-needs-log
        """Resolve log level from method_name or fall back to event_dict['level']."""
        if isinstance(method_name, str):
            return method_name.lower()
        lvl = event_dict.get("level")
        if isinstance(lvl, str):
            return lvl.lower()
        return None

    def _should_drop_by_level(self, level_name, _log_settings):  # stogger: ignore
        """Check if event should be dropped based on level filtering."""
        if level_name is None:
            return False
        try:
            return self.LEVELS.index(level_name) > self.min_level
        except ValueError:
            return False

    def _strip_internal_fields(self, event_dict):  # stogger: ignore complexity-needs-log
        """Pop known internal keys from event_dict (mutates in place)."""
        if not self.show_caller_info:
            event_dict.pop("code_file", None)
            event_dict.pop("code_func", None)
            event_dict.pop("code_lineno", None)
            event_dict.pop("code_module", None)
        event_dict.pop("_from_structlog", None)
        event_dict.pop("_original_event", None)
        event_dict.pop("_record", None)
        event_dict.pop("_translated_msg", None)
        event_dict.pop("_log_settings", None)

    def _format_timestamp(self, ts, _log_settings):  # stogger: ignore complexity-needs-log
        """Format timestamp with format variant handling."""
        if ts is not None:
            if self.timestamp_format == "relative":
                elapsed = time.time() - self.format_config._process_start  # noqa: SLF001
                ts = f"+{elapsed:.3f}s"
            elif self.timestamp_format == "iso_no_z" and str(ts).endswith("Z"):
                ts = str(ts)[:-1]
            return DIM + str(ts) + RESET_ALL + " "
        return DIM + "notimestamp" + RESET_ALL + " "

    def _render_output_sections(self, event_dict, write_fn):  # stogger: ignore complexity-needs-log
        """Render output sections: cmd_output, output, stdout, stderr, stack, traceback."""
        cmd_output_line = event_dict.pop("cmd_output_line", None)
        output = event_dict.pop("_output", None)
        raw_output = event_dict.pop("_raw_output", None)
        raw_output_prefix = event_dict.pop("_raw_output_prefix", None)
        stdout = event_dict.pop("stdout", None)
        stderr = event_dict.pop("stderr", None)
        stack = event_dict.pop("stack", None)
        exception_traceback = event_dict.pop("exception_traceback", None)

        if cmd_output_line is not None:
            write_fn(DIM + "> " + cmd_output_line + RESET_ALL)

        if output is not None:
            write_fn("\n" + prefix("", "\n" + output + "\n") + RESET_ALL)

        if raw_output is not None:
            if raw_output_prefix:
                write_fn("\n" + prefix(raw_output_prefix, raw_output) + "\n")
            else:
                write_fn("\n" + raw_output + "\n")

        if stdout is not None:
            write_fn("\n" + DIM + prefix("out", "\n" + stdout + "\n") + RESET_ALL)

        if stderr is not None:
            write_fn("\n" + prefix("err", "\n" + stderr + "\n") + RESET_ALL)

        if stack is not None:
            write_fn("\n" + prefix("stack", stack))
            if exception_traceback is not None:
                write_fn("\n" + "=" * 79 + "\n")

        if exception_traceback is not None:
            write_fn("\n" + prefix("exception", exception_traceback))

    def __call__(self, _logger: object, method_name: str, event_dict: EventDict) -> EventDict | None:  # stogger: ignore
        log_settings = event_dict.pop("_log_settings", {})
        if log_settings.get("console_ignore", False):
            return None

        level_name = self._resolve_level_name(method_name, event_dict)
        if self._should_drop_by_level(level_name, log_settings):
            raise structlog.DropEvent

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

        self._strip_internal_fields(event_dict)

        ts = event_dict.pop("timestamp", None)
        write(self._format_timestamp(ts, log_settings))

        pid = event_dict.pop("pid", None)
        if self.show_pid and pid is not None:
            write("[" + DIM + str(pid) + RESET_ALL + "] ")

        level = event_dict.pop("level", None)
        if level is not None:
            write(self._level_to_color[level] + level[0].upper() + RESET_ALL + " ")

        event = event_dict.pop("event")
        write(BRIGHT + _pad(event, self.pad_event) + RESET_ALL + " ")

        logger_name = event_dict.pop("logger", "root")
        if logger_name and self.show_logger_brackets:
            write("[" + BLUE + BRIGHT + logger_name + RESET_ALL + "] ")

        if formatted_replace_msg:
            write(formatted_replace_msg)
        else:
            write(
                " ".join(
                    CYAN + key + RESET_ALL + "=" + MAGENTA + repr(event_dict[key]) + RESET_ALL
                    for key in sorted(event_dict.keys())
                ),
            )

        self._render_output_sections(event_dict, write)

        return {"console": console_io.getvalue(), "file": log_io.getvalue()}


class JSONRenderer:
    """JSON renderer for structured logging output."""

    def __init__(self, min_level="info") -> None:
        log.debug("initializing-json-renderer", min_level=min_level)
        self.min_level_idx = ConsoleFileRenderer.LEVELS.index(min_level.lower())

    def __call__(self, _, __, event_dict):  # stogger: ignore complexity-needs-log
        if ConsoleFileRenderer.LEVELS.index(event_dict["level"]) > self.min_level_idx:
            raise structlog.DropEvent
        json_output = json.dumps(event_dict, default=str)
        return {"console": json_output, "file": json_output}


def add_pid(_, __, event_dict):
    event_dict["pid"] = os.getpid()
    return event_dict


def add_caller_info(_, __, event_dict):
    frame, module_str = structlog._frames._find_first_app_frame_and_name(  # ty: ignore[unresolved-attribute]  # noqa: SLF001
        additional_ignores=[__name__],
    )
    event_dict["code_file"] = frame.f_code.co_filename
    event_dict["code_func"] = frame.f_code.co_name
    event_dict["code_lineno"] = frame.f_lineno
    event_dict["code_module"] = module_str
    return event_dict


def process_exc_info(_, __, event_dict):  # stogger: ignore complexity-needs-log
    if exc_info := event_dict.get("exc_info"):
        if isinstance(exc_info, BaseException):
            event_dict["exc_info"] = (type(exc_info), exc_info, exc_info.__traceback__)
        elif not isinstance(exc_info, tuple):
            event_dict["exc_info"] = sys.exc_info()
    return event_dict


def format_exc_info(_logger, _name, event_dict):  # stogger: ignore complexity-needs-log
    """Renders exc_info if it's present.
    Expects the tuple format returned by sys.exc_info().
    Compared to structlog's format_exc_info(), this renders the exception
    information separately which is better for structured logging targets.
    """
    exc_info = event_dict.pop("exc_info", None)
    if exc_info is not None:
        exception_class = exc_info[0]
        formatted_traceback = structlog.processors._format_exception(exc_info)  # noqa: SLF001
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

    def __call__(self, _, __, event_dict):  # stogger: ignore complexity-needs-log
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


def log_to_stdlib(_logger, _name, event_dict):  # stogger: ignore complexity-needs-log
    """Bridge structlog events to Python's standard library logging module.

    This processor forwards every structlog event to ``logging.log()`` so that
    tools relying on stdlib handlers (e.g. ``pytest caplog``) can capture them.

    **Do NOT add this to the default processor pipeline.** Stogger configures
    its own renderers and file handlers. Adding this processor causes every
    event to appear twice — once via stogger's ``MultiRenderer`` and once via
    the stdlib root logger.

    Use cases where this *is* useful:

    - Legacy code that reads from stdlib ``logging`` handlers
    - Ad-hoc debugging with ``logging.basicConfig()``

    For test assertions, prefer ``pytest-structlog`` which captures events
    directly from the structlog pipeline without needing a stdlib bridge.

    Args:
        _logger: The structlog logger (unused).
        _name: The log method name (unused).
        event_dict: The structured event dictionary.

    Returns:
        The unmodified ``event_dict`` (pass-through processor).

    """
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
        logging.log(logging_level, msg, exc_info=exc_info)  # noqa: LOG015
    else:
        logging.log(logging_level, msg)  # noqa: LOG015

    return event_dict


def _build_console_renderer_kwargs(verbose, show_caller_info):  # stogger: ignore complexity-needs-log
    """Build ConsoleFileRenderer keyword overrides for init_logging."""
    kwargs = {}
    if verbose:
        kwargs["min_level"] = "debug"
    if show_caller_info is not None:
        kwargs["show_caller_info"] = show_caller_info
    return kwargs


def _build_logger_factories(logdir, log_to_console, syslog_identifier, cfg):  # stogger: ignore
    """Build file, console, and journal logger factories for init_logging."""
    context = {}
    loggers = {}

    if logdir is not None:
        try:
            main_log_file_name = logdir / f"{syslog_identifier}.log"
            main_log_file = main_log_file_name.open("a")
        except PermissionError:
            log.warning(
                "file-open-permission-denied",
                _replace_msg="Cannot open log file: {path}",
                path=str(main_log_file_name),
            )
        else:
            loggers["file"] = structlog.PrintLoggerFactory(main_log_file)
            context["logdir"] = logdir

    if log_to_console:
        if os.environ.get("JOURNAL_STREAM"):
            print("stogger: JOURNAL_STREAM set, switching to systemd journal logging", file=sys.stderr)  # noqa: T201
        else:
            loggers["console"] = structlog.PrintLoggerFactory(sys.stderr)

    # SPEC: stogger-systemd::journal-registration-flow — dynamic import
    # for journal logger factory, independent of console suppression.
    if cfg.enable_systemd:
        try:
            from stogger_systemd import get_journal_logger_factory  # noqa: PLC0415  # ty: ignore[unresolved-import]

            factory = get_journal_logger_factory()
            loggers["journal"] = factory
        except ImportError:
            if os.environ.get("JOURNAL_STREAM"):
                print(  # noqa: T201
                    "systemd journal detected but stogger-systemd not available."
                    " Install stogger-systemd package for journal integration.",
                    file=sys.stderr,
                )

    # SPEC: postgres-target::package-placement — dynamic import
    # for postgres logger factory, mirrors journal pattern.
    if cfg.enable_postgres:
        try:
            from stogger_postgres import get_postgres_logger_factory  # noqa: PLC0415  # ty: ignore[unresolved-import]

            factory = get_postgres_logger_factory(
                dsn=cfg.postgres_dsn,
                table=cfg.postgres_table,
            )
            loggers["postgres"] = factory
        except ImportError:
            log.debug("stogger-postgres-not-installed", import_error=True)

    return loggers, context


def _configure_structlog(processors, context, loggers):
    """Configure structlog with processors and MultiOptimisticLoggerFactory."""
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.BoundLogger,
        logger_factory=MultiOptimisticLoggerFactory(context, loggers),
    )


def _ensure_stderr_logging() -> None:  # stogger: ignore complexity-needs-log
    """Pre-configure structlog to write to stderr if not yet configured.

    Ensures that any logging during bootstrap (e.g. config loading) goes to
    stderr instead of structlog's default stdout. Uses ``cache_logger_on_first_use=False``
    so the full ``init_logging()`` configuration can overwrite it later.
    """
    if not structlog.is_configured():
        structlog.configure(
            processors=[
                structlog.processors.add_log_level,
                structlog.dev.ConsoleRenderer(),
            ],
            logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
            wrapper_class=structlog.BoundLogger,
            cache_logger_on_first_use=False,
        )


def init_logging(  # noqa: PLR0913 — stable public API, signature frozen  # stogger: ignore complexity-needs-log
    *,
    logdir: str | Path | None = None,
    log_cmd_output: bool = False,
    log_to_console: bool = True,
    syslog_identifier: str = "stogger",
    verbose: bool | None = None,
    show_caller_info: bool | None = None,
) -> None:
    """Initialize full structured logging with console, file, and journal targets.

    Configures structlog with a multi-target rendering pipeline: systemd journal,
    optional command output file, and a colorized console/file renderer. Sets up
    processors for PID, log level, exception formatting, timestamps, and caller info.

    Args:
        logdir: Directory for log files. A ``{syslog_identifier}.log`` file is created
            here when writable. Required if ``log_cmd_output`` is True.
        log_cmd_output: Enable separate command output logging to a dedicated file
            in ``logdir``. Requires ``logdir`` to be set.
        log_to_console: Log to stderr. Disabled automatically when running under
            systemd journal (detected via ``JOURNAL_STREAM`` env var).
        syslog_identifier: Identifier string for syslog/journal entries. Also used
            as the main log file name (``{syslog_identifier}.log``).
        verbose: When True, sets the console log level to ``"debug"``.
            When None (default), uses the level from settings (typically ``"info"``).
        show_caller_info: Whether to display code location (file, function, line)
            in console output. When None (default), uses the setting from
            ``FormatConfig.show_code_info``.

    Raises:
        ValueError: If ``log_cmd_output`` is True but ``logdir`` is not set.

    """
    logdir = Path(logdir) if logdir else None

    # Ensure structlog never writes to stdout during bootstrap
    _ensure_stderr_logging()

    cfg = StoggerConfig(verbose=bool(verbose))
    config_facility = cfg.systemd_facility if cfg.systemd_facility is not None else syslog.LOG_LOCAL0

    console_renderer_kwargs = _build_console_renderer_kwargs(verbose, show_caller_info)
    multi_renderer = MultiRenderer(
        journal=SystemdJournalRenderer(syslog_identifier, config_facility),
        postgres=PostgresRenderer(),
        cmd_output_file=CmdOutputFileRenderer(),
        text=ConsoleFileRenderer(
            format_config=cfg.format if isinstance(cfg.format, FormatConfig) else None,
            **console_renderer_kwargs,
        ),
    )

    processors = [
        add_pid,
        structlog.processors.add_log_level,
        process_exc_info,
        format_exc_info,
        structlog.processors.StackInfoRenderer(),
        build_timestamp_processor(cfg),
        add_caller_info,
        multi_renderer,
    ]

    loggers, context = _build_logger_factories(logdir, log_to_console, syslog_identifier, cfg)
    _configure_structlog(processors, context, loggers)

    log = structlog.get_logger()

    if log_cmd_output:
        if not logdir:
            msg = "A logdir is required for command logging."
            raise ValueError(msg)

        init_command_logging(log, logdir)


def init_early_logging(*, verbose: bool = False) -> None:
    """Initialize minimal structured logging before full setup.

    Configures a lightweight structlog pipeline (timestamp, level, console renderer)
    so that early startup messages are properly formatted instead of appearing as
    raw dicts. No-op if structlog is already configured. Errors during setup are
    suppressed to avoid crashing during early initialization, but logged at debug level.

    Args:
        verbose: When ``True``, emit debug messages showing the caller that invoked
            this function. Also enabled when the ``STOGGER_DEBUG`` environment variable
            is set.

    """
    if verbose or os.environ.get("STOGGER_DEBUG"):
        import inspect  # noqa: PLC0415 — imported at function level; init_early_logging runs before all modules load, inspect only needed for debug caller info

        frame = inspect.stack()[1]
        caller_info = f"{frame.filename}:{frame.lineno} in {frame.function}"
        log.debug("init-early-logging-called", caller=caller_info)
        logging.debug("[stogger-early] init_early_logging called from %s", caller_info)  # noqa: LOG015 — intentional bridge to stdlib logging for early-init messages before structlog pipeline is available

    if structlog.is_configured():
        return  # Already configured

    try:
        # Minimal processors for early initialization
        processors = [
            structlog.stdlib.add_log_level,
            build_timestamp_processor(StoggerConfig()),
            ConsoleFileRenderer(),
            SelectRenderedString(
                key="console",
            ),  # Convert dict to string for PrintLogger
        ]

        # Configure structlog with minimal setup
        structlog.configure(
            processors=processors,  # ty: ignore[invalid-argument-type]
            logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
            wrapper_class=structlog.BoundLogger,
            cache_logger_on_first_use=False,  # Allow reconfiguration
        )

        # Set up basic stdlib logging
        logging.basicConfig(
            level=logging.INFO,  # Allow info messages through
            format="%(message)s",
            force=True,
        )
    except Exception as e:  # noqa: BLE001
        log.debug("early-init-failed", exc=str(e))


class JournalLoggerFactory:
    """Stub factory for systemd journal logger integration.

    Returns ``None`` by default. Actual systemd journal support is provided by
    the ``stogger-systemd`` package, which replaces this factory with a real
    journal writer. Use this as a placeholder so logging pipelines work without
    the systemd extra installed.
    """

    def __call__(self, *_args):
        # systemd journal integration belongs in stogger-systemd package
        return None


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
    "_output",
    "_raw_output",
    "_raw_output_prefix",
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
    "stderr",
    "stdout",
    "timestamp",
]


class SystemdJournalRenderer:
    """Render structlog events as systemd journal fields.

    Transforms event dicts into journal-compatible key-value pairs with
    uppercased field names, syslog priority/facility, and a human-readable
    message string. Strings are kept un-JSON-encoded to preserve line breaks
    in ``journalctl`` output.

    Args:
        syslog_identifier: Identifier string for SYSLOG_IDENTIFIER field.
        syslog_facility: Syslog facility code (default: ``syslog.LOG_LOCAL0``).

    """

    def __init__(self, syslog_identifier, syslog_facility=syslog.LOG_LOCAL0) -> None:
        self.syslog_identifier = syslog_identifier
        self.syslog_facility = syslog_facility

    def __call__(self, _logger: object, method_name: str, event_dict: EventDict) -> EventDict:  # stogger: ignore
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
                None,  # ty: ignore[invalid-argument-type]
                {k: v for k, v in event_dict.items() if k not in KEYS_TO_SKIP_IN_JOURNAL_MESSAGE},
            )

            if kv:
                event_dict["message"] += ": " + kv

        event_dict.pop("timestamp", None)
        event_dict.pop("pid", None)
        code_lineno = event_dict.pop("code_lineno", None)

        event_dict = {k.upper(): self.dump_for_journal(v) for k, v in event_dict.items()}

        event_dict["PRIORITY"] = JOURNAL_LEVELS.get(  # ty: ignore[no-matching-overload]
            event_dict.get("LEVEL"),
            syslog.LOG_INFO,
        )
        event_dict["SYSLOG_FACILITY"] = self.syslog_facility
        event_dict["SYSLOG_IDENTIFIER"] = self.syslog_identifier
        event_dict["CODE_LINE"] = code_lineno

        return {"journal": event_dict}

    def handle_json_fallback(self, obj):  # stogger: ignore
        """Same as structlog's json fallback.
        Supports obj.__structlog__() for custom object serialization.
        """
        try:
            return obj.__structlog__()
        except AttributeError:
            return repr(obj)

    def dump_for_journal(self, obj):  # stogger: ignore complexity-needs-log
        """Encode values as JSON, except strings.
        We keep strings unchanged to display line breaks properly in journalctl
        and graylog.
        """
        if isinstance(obj, str):
            return obj
        if isinstance(obj, datetime):
            return datetime.isoformat(obj)
        return json.dumps(obj, default=self.handle_json_fallback)


class PostgresRenderer:
    """Render event_dict into a column dict for PostgreSQL INSERT.

    Extracts known columns (timestamp, level, event, func, scope) and
    packs remaining fields into JSONB data.
    """

    KNOWN_FIELDS = frozenset({"timestamp", "level", "event", "func", "scope"})

    def __call__(self, _logger, _method_name, event_dict):  # stogger: ignore complexity-needs-log
        column_dict = {}
        data = {}
        for key, value in event_dict.items():
            if key in self.KNOWN_FIELDS:
                column_dict[key] = value
            else:
                data[key] = value
        column_dict["data"] = data
        return {"postgres": column_dict}


class CmdOutputFileRenderer:
    """Renderer for command output file logging."""

    def __call__(self, _logger: object, _method_name: str, event_dict: EventDict) -> EventDict:  # stogger: ignore
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

    def __call__(self, logger: object, method_name: str, event_dict: EventDict) -> EventDict:  # stogger: ignore
        merged_messages = {}
        for renderer in self.renderers.values():
            try:
                messages = renderer(logger, method_name, dict(event_dict))
                merged_messages.update(messages)
            except Exception:  # stogger: ignore except-must-log
                logging.getLogger(__name__).exception("Renderer failed, using fallback")

        return merged_messages


class MultiOptimisticLoggerFactory:
    """Factory that creates ``MultiOptimisticLogger`` instances.

    Holds shared context (e.g. ``logdir``) and a dict of sub-logger factories
    (e.g. ``"console"`` → ``PrintLoggerFactory``, ``"file"`` → ``PrintLoggerFactory``).
    Each factory is called once per ``MultiOptimisticLogger`` instantiation.

    Args:
        context: Shared context dict available to all created loggers.
        factories: Dict mapping target names to structlog logger factory callables.

    """

    def __init__(self, context, factories) -> None:
        self.context = context
        self.factories = factories

    def __call__(self, *_args):
        loggers = {k: f() for k, f in self.factories.items()}
        return MultiOptimisticLogger(loggers)


class MultiOptimisticLogger:
    """Distribute log messages to multiple sub-loggers by target name.

    Receives a dict of rendered outputs keyed by target name (e.g. ``"console"``,
    ``"file"``, ``"journal"``) and dispatches each to the corresponding
    sub-logger. Targets not present in the message are skipped. Errors in
    individual sub-loggers are caught and reported to stdlib logging to prevent
    one failing target from affecting others.

    Args:
        loggers: Dict mapping target names to structlog logger instances.

    """

    def __init__(self, loggers) -> None:
        self.loggers = loggers

    def __repr__(self) -> str:
        return f"<MultiOptimisticLogger {[repr(logger) for logger in self.loggers]}>"

    def msg(self, **messages) -> None:  # stogger: ignore
        for name, logger in self.loggers.items():
            try:
                line = messages.get(name)
                if line:
                    logger.msg(line)
            except Exception:
                logging.getLogger(__name__).exception("Renderer failed, using fallback")

    def __getattr__(self, name):
        return self.msg


def init_command_logging(log, logdir=None) -> None:
    """Add a command output file logger to the active multi-logger factory.

    Opens (or overwrites) a dedicated log file for capturing subprocess command
    output separately from the main log. When running under systemd (detected
    via ``INVOCATION_ID`` env var), the filename includes a timestamp and
    invocation ID for uniqueness.

    Args:
        log: A structlog BoundLogger instance (typically from ``structlog.get_logger()``).
        logdir: Directory for the command output file. Falls back to the
            ``logdir`` stored in the current ``MultiOptimisticLoggerFactory`` context.

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
        cmd_log_file_name = logdir / f"{formatted_dt}_build-output_{invocation_id}.log"
    else:
        cmd_log_file_name = logdir / "build-output.log"

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
    """Close and delete the command output log file.

    Removes the file created by ``init_command_logging``. Use this when no
    meaningful command output was produced to avoid leaving empty log files.

    Args:
        log: A structlog BoundLogger instance for diagnostic messages.

    Raises:
        KeyError: If the ``cmd_output_file`` factory is not present in the
            active ``MultiOptimisticLoggerFactory`` (i.e. ``init_command_logging``
            was never called).

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

    cmd_log_file = cmd_output_file_factory._file  # noqa: SLF001

    log.debug(
        "logging-cmd-output-drop",
        cmd_log_file=cmd_log_file.name,
    )

    cmd_log_file.close()
    Path(cmd_log_file.name).unlink()


def logging_initialized():
    """Check whether structured logging has been configured.

    Returns:
        True if ``init_logging`` or ``init_early_logging`` has been called
        successfully, False otherwise.

    """
    return structlog.is_configured()
