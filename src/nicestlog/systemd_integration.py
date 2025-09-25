"""Advanced systemd integration for nicestlog.

Makes systemd logging actually usable and powerful.
"""

import contextlib
from dataclasses import dataclass
from datetime import datetime
import json
import os
import socket
import subprocess
from typing import Any

import structlog

logger = structlog.get_logger()

try:
    from systemd import journal  # type: ignore[import-not-found]

    SYSTEMD_AVAILABLE = True
except ImportError:
    SYSTEMD_AVAILABLE = False
    journal = None


class SystemdJournalHandler:
    """Advanced systemd journal handler with proper field mapping and priorities."""

    # Map Python log levels to systemd priorities
    PRIORITY_MAP = {
        "critical": journal.LOG_CRIT if SYSTEMD_AVAILABLE else 2,
        "error": journal.LOG_ERR if SYSTEMD_AVAILABLE else 3,
        "warning": journal.LOG_WARNING if SYSTEMD_AVAILABLE else 4,
        "info": journal.LOG_INFO if SYSTEMD_AVAILABLE else 6,
        "debug": journal.LOG_DEBUG if SYSTEMD_AVAILABLE else 7,
        "trace": journal.LOG_DEBUG if SYSTEMD_AVAILABLE else 7,
    }

    def __init__(
        self,
        identifier: str | None = None,
        facility: str | None = None,
    ):
        """Initialize systemd journal handler.

        Args:
            identifier: SYSLOG_IDENTIFIER for journal entries
            facility: SYSLOG_FACILITY (e.g., 'daemon', 'user', 'local0')

        """
        self.identifier = identifier or "nicestlog"
        self.facility = facility
        self.hostname = socket.gethostname()
        self.pid = os.getpid()

        if not SYSTEMD_AVAILABLE:
            pass

    def __call__(self, _, __, event_dict):
        """Process log event and send to systemd journal."""
        if not SYSTEMD_AVAILABLE:
            return event_dict

        # Extract standard fields
        message = event_dict.get("event", "")
        level = event_dict.get("level", "info")
        logger_name = event_dict.get("logger", "root")
        event_dict.get("timestamp")

        # Build journal fields (systemd uses uppercase field names)
        journal_fields = {
            "MESSAGE": str(message),
            "PRIORITY": self.PRIORITY_MAP.get(level, journal.LOG_INFO),
            "SYSLOG_IDENTIFIER": self.identifier,
            "LOGGER_NAME": logger_name,
            "PYTHON_MODULE": logger_name,
            "SYSLOG_PID": str(self.pid),
            "_HOSTNAME": self.hostname,
            "_PID": str(self.pid),
        }

        # Add facility if specified
        if self.facility:
            journal_fields["SYSLOG_FACILITY"] = self.facility

        # Add custom fields from event_dict
        for key, value in event_dict.items():
            if key in ["event", "level", "logger", "timestamp"]:
                continue

            # Convert to systemd field format (uppercase, prefix with app name)
            field_name = f"NICESTLOG_{key.upper()}"

            # Systemd fields must be strings
            if isinstance(value, dict | list):
                journal_fields[field_name] = json.dumps(value, default=str)
            else:
                journal_fields[field_name] = str(value)

        # Send to journal
        with contextlib.suppress(Exception):
            journal.send(**journal_fields)

        return event_dict


def detect_systemd_environment() -> dict[str, Any]:
    """Detect if we're running under systemd and gather environment info."""
    info: dict[str, Any] = {
        "running_under_systemd": False,
        "journal_available": SYSTEMD_AVAILABLE,
        "service_name": None,
        "unit_name": None,
        "invocation_id": None,
        "journal_stream": None,
        "systemd_exec_pid": None,
    }

    # Check if we're running under systemd
    systemd_exec_pid = os.environ.get("SYSTEMD_EXEC_PID")
    if systemd_exec_pid:
        info["running_under_systemd"] = True
        info["systemd_exec_pid"] = systemd_exec_pid

    # Get systemd-specific environment variables
    invocation_id = os.environ.get("INVOCATION_ID")
    journal_stream = os.environ.get("JOURNAL_STREAM")
    info["invocation_id"] = invocation_id
    info["journal_stream"] = journal_stream

    # Try to get unit name from systemd environment
    if SYSTEMD_AVAILABLE:
        # Use systemd library to get unit information if available
        from systemd import daemon

        unit_name = daemon.booted()
        if unit_name:
            info["unit_name"] = unit_name
            if unit_name.endswith(".service"):
                info["service_name"] = unit_name[:-8]  # Remove .service suffix

    return info


def setup_systemd_logging(
    identifier: str | None = None,
    facility: str | None = None,
) -> bool:
    """Setup systemd journal logging integration.

    This function prefers the detected runtime environment to decide whether to
    enable systemd logging. If a systemd environment is detected, it will attach
    a SystemdJournalHandler even when the systemd-python package is not
    available; in that case, the handler acts as a no-op but preserves the
    processor chain shape. If no systemd environment is detected, the function
    returns False.

    Args:
        identifier: SYSLOG_IDENTIFIER for journal entries
        facility: SYSLOG_FACILITY
        structured_fields: Whether to include structured data as journal fields

    Returns:
        True if systemd logging was successfully configured, otherwise False

    """
    env_info = detect_systemd_environment()

    # If we don't appear to be running under systemd and journal isn't available,
    # don't configure anything.
    if not (env_info.get("running_under_systemd") or env_info.get("journal_available")):
        return False

    # If systemd-python isn't available, warn but still install a no-op handler so
    # tests and processor wiring continue to work.
    if not SYSTEMD_AVAILABLE:
        pass

    # Use detected service name if no identifier provided
    if not identifier and env_info.get("service_name"):
        identifier = env_info["service_name"]

    handler = SystemdJournalHandler(identifier=identifier, facility=facility)

    # Add to structlog processors
    current_config = structlog.get_config()
    processors = list(current_config.get("processors", []))

    # Insert before any renderers; if there are no processors, this inserts at 0.
    processors.insert(-1, handler)

    structlog.configure(
        processors=processors,
        logger_factory=current_config.get(
            "logger_factory",
            structlog.stdlib.LoggerFactory(),
        ),
        wrapper_class=current_config.get("wrapper_class", structlog.stdlib.BoundLogger),
        cache_logger_on_first_use=True,
    )

    return True


@dataclass
class ServiceConfig:
    """Configuration for systemd service creation."""
    
    service_name: str
    exec_command: str
    user: str | None = None
    working_directory: str | None = None
    environment: dict[str, str] | None = None
    restart_policy: str = "always"


def create_systemd_service_file(config: ServiceConfig) -> str:
    """Generate a systemd service file with proper logging configuration.

    Args:
        config: Service configuration parameters

    Returns:
        Service file content as string

    """
    user = config.user or os.getenv("USER", "nobody")
    working_directory = config.working_directory or os.getcwd()
    environment = config.environment or {}

    service_content = f"""[Unit]
Description={config.service_name} - Managed by nicestlog
After=network.target
Wants=network.target

[Service]
Type=simple
User={user}
WorkingDirectory={working_directory}
ExecStart={config.exec_command}
Restart={config.restart_policy}
RestartSec=5

# Logging configuration
StandardOutput=journal
StandardError=journal
SyslogIdentifier={config.service_name}

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths={working_directory}

# Environment variables
"""

    for key, value in environment.items():
        service_content += f"Environment={key}={value}\n"

    service_content += """
[Install]
WantedBy=multi-user.target
"""

    return service_content


def query_journal_logs(
    service_name: str | None = None,
    since: str = "1 hour ago",
    level: str | None = None,
    lines: int = 100,
) -> list[dict[str, Any]]:
    """Query systemd journal for logs.

    Args:
        service_name: Filter by service name
        since: Time filter (e.g., "1 hour ago", "today")
        level: Log level filter
        lines: Maximum number of lines

    Returns:
        List of log entries as dictionaries

    """
    if not SYSTEMD_AVAILABLE:
        return []

    try:
        j = journal.Reader()

        # Add filters
        if service_name:
            j.add_match(SYSLOG_IDENTIFIER=service_name)

        if level:
            priority = SystemdJournalHandler.PRIORITY_MAP.get(level.lower())
            if priority:
                j.add_match(PRIORITY=priority)

        # Set time filter
        if since:
            j.seek_realtime(datetime.now().timestamp() - parse_time_delta(since))

        # Get entries
        entries: list[dict[str, Any]] = []
        for entry in j:
            if len(entries) >= lines:
                break

            # Convert journal entry to dict
            log_entry = {
                "timestamp": entry["__REALTIME_TIMESTAMP"].timestamp(),
                "message": entry.get("MESSAGE", ""),
                "priority": entry.get("PRIORITY", 6),
                "identifier": entry.get("SYSLOG_IDENTIFIER", ""),
                "pid": entry.get("_PID", ""),
                "hostname": entry.get("_HOSTNAME", ""),
            }

            # Add custom fields
            for key, value in entry.items():
                if key.startswith("NICESTLOG_"):
                    field_name = key.replace("NICESTLOG_", "").lower()
                    log_entry[field_name] = value

            entries.append(log_entry)

        return list(reversed(entries))  # Most recent first

    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
        logger.warning("Failed to read journal entries", error=str(e))
        return []


def parse_time_delta(time_str: str) -> float:
    """Parse time strings like '1 hour ago' into seconds."""
    # Simple parser for common time formats
    time_str = time_str.lower().strip()

    if "hour" in time_str:
        hours = int(time_str.split()[0])
        return hours * 3600
    elif "minute" in time_str:
        minutes = int(time_str.split()[0])
        return minutes * 60
    elif "day" in time_str:
        days = int(time_str.split()[0])
        return days * 24 * 3600
    elif time_str == "today":
        now = datetime.now()
        today_start = datetime(now.year, now.month, now.day)
        return (now - today_start).total_seconds()
    else:
        return 3600  # Default: 1 hour


def demo_systemd_integration():
    """Demonstrate systemd integration features."""
    # Check environment
    detect_systemd_environment()

    if SYSTEMD_AVAILABLE:
        # Setup systemd logging
        setup_systemd_logging(identifier="nicestlog-demo")

        # Create logger and test
        log = structlog.get_logger("systemd_demo")

        log.info(
            "systemd_integration_test",
            component="demo",
            test_data={"key": "value"},
            user_id=12345,
        )

        log.warning("test_warning", message="This is a test warning for systemd")

        log.error(
            "test_error",
            error_code=500,
            details="Test error for systemd journal",
        )


        # Query recent logs
        recent_logs = query_journal_logs(service_name="nicestlog-demo", lines=5)
        for entry in recent_logs:
            datetime.fromtimestamp(entry["timestamp"]).strftime("%H:%M:%S")

    else:
        pass

    # Generate service file example
    config = ServiceConfig(
        service_name="my-python-app",
        exec_command="/usr/bin/python3 /opt/myapp/main.py",
        user="myapp",
        working_directory="/opt/myapp",
        environment={"PYTHONPATH": "/opt/myapp", "LOG_LEVEL": "info"},
    )
    create_systemd_service_file(config)



if __name__ == "__main__":
    demo_systemd_integration()
