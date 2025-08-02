"""
Core logging functionality for nicestlog.

This module contains the main structlog-based multi-target logging implementation.
Originally developed for the Flying Circus platform.
"""

import logging
import logging.handlers
import os
import sys
import time
from pathlib import Path
from typing import Any, Optional, Union, MutableMapping

import structlog


# Global state for logging configuration
_logging_initialized = False
_current_config = {}


def is_systemd_context() -> bool:
    """
    Detect if we're running under systemd.
    
    Returns:
        True if running under systemd, False otherwise.
    """
    return (
        os.environ.get('INVOCATION_ID') is not None or
        os.environ.get('JOURNAL_STREAM') is not None
    )


def has_systemd_support() -> bool:
    """
    Check if systemd-python is available.
    
    Returns:
        True if systemd journal logging is available, False otherwise.
    """
    try:
        import importlib.util
        return importlib.util.find_spec("systemd.journal") is not None
    except ImportError:
        return False


class OptimisticHandler(logging.Handler):
    """
    A logging handler that never raises exceptions.
    
    This handler wraps other handlers and catches any exceptions they might
    raise, preventing logging failures from crashing the application.
    """
    
    def __init__(self, wrapped_handler: logging.Handler):
        super().__init__()
        self.wrapped_handler = wrapped_handler
        self.setLevel(wrapped_handler.level)
        if wrapped_handler.formatter:
            self.setFormatter(wrapped_handler.formatter)
    
    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record, catching any exceptions."""
        try:
            self.wrapped_handler.emit(record)
        except Exception:
            # Silently ignore logging errors to prevent application crashes
            pass
    
    def setLevel(self, level: Union[int, str]) -> None:
        """Set the logging level for both this handler and the wrapped handler."""
        super().setLevel(level)
        self.wrapped_handler.setLevel(level)
    
    def setFormatter(self, formatter: Optional[logging.Formatter]) -> None:
        """Set the formatter for both this handler and the wrapped handler."""
        super().setFormatter(formatter)
        self.wrapped_handler.setFormatter(formatter)


class ConsoleRenderer:
    """
    Rich console renderer for structured logs.
    
    Provides colored, human-readable output with structured data display.
    """
    
    def __init__(self, colors: bool = True):
        self.colors = colors and self._supports_color()
        self._color_codes = {
            'TRACE': '\033[90m',     # Dark gray
            'DEBUG': '\033[36m',     # Cyan
            'INFO': '\033[32m',      # Green
            'WARNING': '\033[33m',   # Yellow
            'ERROR': '\033[31m',     # Red
            'CRITICAL': '\033[35m',  # Magenta
            'RESET': '\033[0m',      # Reset
            'BOLD': '\033[1m',       # Bold
            'DIM': '\033[2m',        # Dim
        }
    
    def _supports_color(self) -> bool:
        """Check if the terminal supports color output."""
        try:
            import colorama  # type: ignore[import-untyped]
            colorama.init()
            return True
        except ImportError:
            pass
        
        # Check if we're in a terminal that supports color
        return (
            hasattr(sys.stdout, 'isatty') and 
            sys.stdout.isatty() and 
            os.environ.get('TERM') != 'dumb'
        )
    
    def _colorize(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled."""
        if not self.colors:
            return text
        return f"{self._color_codes.get(color, '')}{text}{self._color_codes['RESET']}"
    
    def __call__(self, logger: Any, method_name: str, event_dict: MutableMapping[str, Any]) -> str:
        """Render a log event as a colored console string."""
        # Extract standard fields
        timestamp = event_dict.pop('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
        level = event_dict.pop('level', method_name.upper())
        event = event_dict.pop('event', '')
        
        # Handle template message replacement
        replace_msg = event_dict.pop('_replace_msg', None)
        if replace_msg:
            try:
                message = replace_msg.format(**event_dict)
            except (KeyError, ValueError):
                message = f"{event} (template error: {replace_msg})"
        else:
            message = event
        
        # Extract logger name
        logger_name = event_dict.pop('logger', '')
        if logger_name:
            logger_name = f"[{logger_name}] "
        
        # Color the level
        colored_level = self._colorize(f"{level:8}", level)
        
        # Build the main message line
        main_line = f"{timestamp} {colored_level} {logger_name}{message}"
        
        # Add structured data if present
        if event_dict:
            # Remove internal structlog fields
            clean_dict = {k: v for k, v in event_dict.items() 
                         if not k.startswith('_') and k not in ('exc_info',)}
            
            if clean_dict:
                data_str = " ".join(f"{k}={v}" for k, v in clean_dict.items())
                data_line = self._colorize(f"    {data_str}", 'DIM')
                main_line += f"\n{data_line}"
        
        # Handle exception info
        if 'exc_info' in event_dict and event_dict['exc_info']:
            import traceback
            exc_text = ''.join(traceback.format_exception(*event_dict['exc_info']))
            exc_lines = [self._colorize(f"    {line.rstrip()}", 'DIM') 
                        for line in exc_text.splitlines()]
            main_line += "\n" + "\n".join(exc_lines)
        
        return main_line


class JSONRenderer:
    """
    JSON renderer for structured logs.
    
    Produces machine-parseable JSON output suitable for log aggregation systems.
    """
    
    def __call__(self, logger: Any, method_name: str, event_dict: MutableMapping[str, Any]) -> str:
        """Render a log event as a JSON string."""
        import json
        
        # Ensure we have standard fields
        if 'timestamp' not in event_dict:
            event_dict['timestamp'] = time.time()
        if 'level' not in event_dict:
            event_dict['level'] = method_name.upper()
        
        # Handle exception info
        if 'exc_info' in event_dict and event_dict['exc_info']:
            import traceback
            event_dict['exception'] = ''.join(
                traceback.format_exception(*event_dict['exc_info'])
            )
            del event_dict['exc_info']
        
        return json.dumps(event_dict, default=str, ensure_ascii=False)


def create_console_handler(verbose: bool = False, colors: bool = True) -> logging.Handler:
    """
    Create a console handler with rich formatting.
    
    Args:
        verbose: If True, set level to DEBUG, otherwise INFO
        colors: If True, enable colored output
        
    Returns:
        Configured console logging handler
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    
    # Use our custom console renderer
    renderer = ConsoleRenderer(colors=colors)
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
        ],
    )
    handler.setFormatter(formatter)
    
    return OptimisticHandler(handler)


def create_file_handler(
    logdir: Path, 
    filename: str = "application.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Handler:
    """
    Create a rotating file handler with JSON formatting.
    
    Args:
        logdir: Directory for log files
        filename: Name of the log file
        max_bytes: Maximum size before rotation
        backup_count: Number of backup files to keep
        
    Returns:
        Configured file logging handler
    """
    logdir.mkdir(parents=True, exist_ok=True)
    log_file = logdir / filename
    
    handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    handler.setLevel(logging.DEBUG)
    
    # Use JSON formatting for files
    renderer = JSONRenderer()
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
        ],
    )
    handler.setFormatter(formatter)
    
    return OptimisticHandler(handler)


def create_systemd_handler() -> Optional[logging.Handler]:
    """
    Create a systemd journal handler if available.
    
    Returns:
        Configured systemd journal handler, or None if not available
    """
    if not has_systemd_support():
        return None
    
    try:
        from systemd.journal import JournalHandler  # type: ignore[import-not-found]
        
        handler = JournalHandler()
        handler.setLevel(logging.DEBUG)
        
        # Use JSON formatting for systemd journal
        renderer = JSONRenderer()
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=renderer,
            foreign_pre_chain=[
                structlog.stdlib.add_log_level,
                structlog.stdlib.add_logger_name,
                structlog.processors.TimeStamper(fmt="iso"),
            ],
        )
        handler.setFormatter(formatter)
        
        return OptimisticHandler(handler)
    except Exception:
        return None


def init_logging(
    verbose: bool = False,
    logdir: Optional[Path] = None,
    log_cmd_output: bool = False,
    log_to_console: Optional[bool] = None,
    syslog_identifier: Optional[str] = None,
    show_caller_info: bool = False,
    colors: bool = True,
) -> None:
    """
    Initialize the structured logging system.
    
    Args:
        verbose: Enable verbose (DEBUG) logging to console
        logdir: Directory for file logging (enables file logging if provided)
        log_cmd_output: Enable separate command output logging (requires logdir)
        log_to_console: Force console logging on/off (auto-detects if None)
        syslog_identifier: Identifier for systemd journal entries
        show_caller_info: Include caller information in logs
        colors: Enable colored console output
    """
    global _logging_initialized, _current_config
    
    # Store configuration
    _current_config = {
        'verbose': verbose,
        'logdir': logdir,
        'log_cmd_output': log_cmd_output,
        'log_to_console': log_to_console,
        'syslog_identifier': syslog_identifier,
        'show_caller_info': show_caller_info,
        'colors': colors,
    }
    
    # Determine if we should log to console
    if log_to_console is None:
        log_to_console = not is_systemd_context()
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.DEBUG)
    
    # Collect handlers
    handlers = []
    
    # Console handler
    if log_to_console:
        console_handler = create_console_handler(verbose=verbose, colors=colors)
        handlers.append(console_handler)
    
    # File handler
    if logdir:
        file_handler = create_file_handler(logdir, "application.log")
        handlers.append(file_handler)
        
        # Command output handler
        if log_cmd_output:
            cmd_handler = create_file_handler(logdir, "commands.log")
            handlers.append(cmd_handler)
    
    # Systemd journal handler
    if has_systemd_support():
        systemd_handler = create_systemd_handler()
        if systemd_handler:
            handlers.append(systemd_handler)
    
    # Add all handlers to root logger
    for handler in handlers:
        root_logger.addHandler(handler)
    
    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]
    
    if show_caller_info:
        processors.append(structlog.processors.CallsiteParameterAdder())
    
    processors.extend([
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ])
    
    structlog.configure(
        processors=processors,  # type: ignore[arg-type]
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    _logging_initialized = True


def setup_basic_logging(verbose: bool = False, app_name: Optional[str] = None, colors: bool = True):
    """
    Quick setup for basic console logging.
    
    Args:
        verbose: Enable verbose (DEBUG) logging
        app_name: Application name for log identification
        colors: Enable colored console output
        
    Returns:
        Configured structlog logger
    """
    init_logging(
        verbose=verbose,
        log_to_console=True,
        syslog_identifier=app_name,
        colors=colors,
    )
    
    logger = structlog.get_logger()
    if app_name:
        logger = logger.bind(app=app_name)
    
    return logger


def setup_file_logging(
    logdir: Path,
    verbose: bool = False,
    app_name: Optional[str] = None,
    log_cmd_output: bool = False,
    colors: bool = True,
):
    """
    Setup logging with both file and console output.
    
    Args:
        logdir: Directory for log files
        verbose: Enable verbose (DEBUG) logging to console
        app_name: Application name for log identification
        log_cmd_output: Enable separate command output logging
        colors: Enable colored console output
        
    Returns:
        Configured structlog logger
    """
    init_logging(
        verbose=verbose,
        logdir=logdir,
        log_cmd_output=log_cmd_output,
        log_to_console=True,
        syslog_identifier=app_name,
        colors=colors,
    )
    
    logger = structlog.get_logger()
    if app_name:
        logger = logger.bind(app=app_name)
    
    return logger


def setup_systemd_logging(
    verbose: bool = False,
    app_name: Optional[str] = None,
    logdir: Optional[Path] = None,
):
    """
    Setup logging optimized for systemd environments.
    
    Args:
        verbose: Enable verbose (DEBUG) logging
        app_name: Application name for journal identification
        logdir: Optional directory for additional file logging
        
    Returns:
        Configured structlog logger
    """
    init_logging(
        verbose=verbose,
        logdir=logdir,
        log_to_console=False,  # Systemd handles console output
        syslog_identifier=app_name,
        colors=False,  # No colors for systemd
    )
    
    logger = structlog.get_logger()
    if app_name:
        logger = logger.bind(app=app_name)
    
    return logger


def get_logger(name: Optional[str] = None):
    """
    Get a structlog logger instance.
    
    Args:
        name: Optional logger name for identification
        
    Returns:
        Configured structlog logger
    """
    if not _logging_initialized:
        # Auto-initialize with basic settings
        setup_basic_logging()
    
    logger = structlog.get_logger(name)
    return logger