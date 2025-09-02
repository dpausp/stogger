"""
Beautiful systemd journal viewer - makes journalctl actually usable!

Reads binary journal logs and displays them with nicestlog's beautiful formatting.
"""

import sys
import json
import re
from datetime import datetime, timedelta

from typing import Dict, Any, Iterator, Optional
from dataclasses import dataclass

import structlog

# Get a logger for this module
log = structlog.get_logger(__name__)

# Keep a reference to the real datetime class for type checks when tests patch the module symbol
_REAL_DATETIME = datetime

try:
    from systemd import journal  # type: ignore[import-not-found]

    SYSTEMD_AVAILABLE = True
    log.debug("systemd-journal-available", module="systemd.journal")
except ImportError:
    SYSTEMD_AVAILABLE = False
    journal = None
    log.warning(
        "systemd-journal-unavailable",
        _replace_msg="⚠️  systemd-python not available - journal viewing disabled",
        suggestion="Install with: pip install systemd-python",
    )

try:
    from .core import RESET_ALL, BRIGHT, DIM, RED, BLUE, CYAN, MAGENTA, YELLOW, GREEN
except ImportError:
    # When running as standalone script
    import sys

    if sys.stdout.isatty():
        try:
            import colorama

            colorama.init()
            RESET_ALL = colorama.Style.RESET_ALL
            BRIGHT = colorama.Style.BRIGHT
            DIM = colorama.Style.DIM
            RED = colorama.Fore.RED
            BLUE = colorama.Fore.BLUE
            CYAN = colorama.Fore.CYAN
            MAGENTA = colorama.Fore.MAGENTA
            YELLOW = colorama.Fore.YELLOW
            GREEN = colorama.Fore.GREEN
        except ImportError:
            RESET_ALL = BRIGHT = DIM = RED = BLUE = CYAN = MAGENTA = YELLOW = GREEN = ""
    else:
        RESET_ALL = BRIGHT = DIM = RED = BLUE = CYAN = MAGENTA = YELLOW = GREEN = ""


@dataclass
class JournalEntry:
    """Structured representation of a journal entry."""

    timestamp: datetime
    hostname: str
    service: str
    pid: str
    level: str
    message: str
    fields: Dict[str, Any]
    raw_entry: Dict[str, Any]


class JournalViewer:
    """
    Beautiful viewer for systemd journal logs.

    Converts binary journal entries back into human-readable format
    with the same beautiful styling as nicestlog console output.
    """

    PRIORITY_TO_LEVEL = {
        0: "critical",  # LOG_EMERG
        1: "critical",  # LOG_ALERT
        2: "critical",  # LOG_CRIT
        3: "error",  # LOG_ERR
        4: "warning",  # LOG_WARNING
        5: "info",  # LOG_NOTICE
        6: "info",  # LOG_INFO
        7: "debug",  # LOG_DEBUG
    }

    LEVEL_COLORS = {
        "critical": RED,
        "error": RED,
        "warning": YELLOW,
        "info": GREEN,
        "debug": DIM,
    }

    def __init__(
        self,
        show_hostname: bool = False,
        show_pid: bool = True,
        show_service: bool = True,
        max_width: int = 120,
    ):
        """
        Initialize journal viewer.

        Args:
            show_hostname: Show hostname in output
            show_pid: Show process ID
            show_service: Show service/identifier
            max_width: Maximum line width for formatting
        """
        log.debug(
            "initializing-journal-viewer",
            show_hostname=show_hostname,
            show_pid=show_pid,
            show_service=show_service,
            max_width=max_width,
        )

        self.show_hostname = show_hostname
        self.show_pid = show_pid
        self.show_service = show_service
        self.max_width = max_width

        if not SYSTEMD_AVAILABLE:
            log.error(
                "systemd-unavailable-during-init",
                _replace_msg="❌ Cannot initialize journal viewer - systemd-python not available",
            )
            print(
                "Warning: systemd-python not available. Install with: pip install systemd-python",
                file=sys.stderr,
            )
        else:
            log.debug(
                "journal-viewer-initialized", _replace_msg="✅ Journal viewer ready"
            )

    def parse_journal_entry(self, entry: Dict[str, Any]) -> JournalEntry:
        """Parse a raw journal entry into structured format."""
        log.debug(
            "parsing-journal-entry",
            has_timestamp=bool(entry.get("__REALTIME_TIMESTAMP")),
            entry_keys=list(entry.keys())[:10],
        )  # Limit keys for readability

        # Extract timestamp
        timestamp = entry.get("__REALTIME_TIMESTAMP")
        if timestamp:
            timestamp = datetime.fromtimestamp(timestamp.timestamp())
        else:
            log.warning(
                "missing-timestamp-in-entry",
                _replace_msg="⚠️  Journal entry missing timestamp, using current time",
            )
            timestamp = datetime.now()

        # Extract basic fields
        hostname = entry.get("_HOSTNAME", "unknown")
        service = entry.get("SYSLOG_IDENTIFIER", entry.get("_COMM", "unknown"))
        pid = str(entry.get("_PID", entry.get("SYSLOG_PID", "")))
        message = entry.get("MESSAGE", "")

        # Map priority to level
        priority = entry.get("PRIORITY", 6)
        if isinstance(priority, str):
            priority = int(priority)
        level = self.PRIORITY_TO_LEVEL.get(priority, "info")

        # Extract custom fields (nicestlog fields)
        fields = {}
        for key, value in entry.items():
            if key.startswith("NICESTLOG_"):
                field_name = key.replace("NICESTLOG_", "").lower()
                # Try to parse JSON values
                try:
                    if isinstance(value, str) and (
                        value.startswith("{") or value.startswith("[")
                    ):
                        fields[field_name] = json.loads(value)
                    else:
                        fields[field_name] = value
                except json.JSONDecodeError:
                    log.debug(
                        "json-decode-failed",
                        field_name=field_name,
                        value_preview=str(value)[:100],
                    )
                    fields[field_name] = value

        return JournalEntry(
            timestamp=timestamp,
            hostname=hostname,
            service=service,
            pid=pid,
            level=level,
            message=message,
            fields=fields,
            raw_entry=entry,
        )

    def format_entry(self, entry: JournalEntry) -> str:
        """Format a journal entry with beautiful styling."""
        parts = []

        # Timestamp
        timestamp_str = entry.timestamp.strftime("%H:%M:%S.%f")[:-3]
        parts.append(f"{DIM}{timestamp_str}{RESET_ALL}")

        # Level indicator with color
        level_color = self.LEVEL_COLORS.get(entry.level, "")
        level_char = entry.level[0].upper()
        parts.append(f"{level_color}{level_char}{RESET_ALL}")

        # Service/identifier
        if self.show_service:
            parts.append(f"[{BLUE}{BRIGHT}{entry.service}{RESET_ALL}]")

        # PID
        if self.show_pid and entry.pid:
            parts.append(f"{DIM}({entry.pid}){RESET_ALL}")

        # Hostname
        if self.show_hostname:
            parts.append(f"{DIM}@{entry.hostname}{RESET_ALL}")

        # Message
        parts.append(f"{BRIGHT}{entry.message}{RESET_ALL}")

        # Custom fields
        if entry.fields:
            field_parts = []
            for key, value in entry.fields.items():
                if isinstance(value, (dict, list)):
                    value_str = json.dumps(value, separators=(",", ":"))
                else:
                    value_str = str(value)
                field_parts.append(
                    f"{CYAN}{key}{RESET_ALL}={MAGENTA}{value_str}{RESET_ALL}"
                )

            if field_parts:
                parts.append(" ".join(field_parts))

        return " ".join(parts)

    def query_journal(
        self,
        service: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        level: Optional[str] = None,
        lines: Optional[int] = None,
        follow: bool = False,
    ) -> Iterator[JournalEntry]:
        """
        Query systemd journal and yield formatted entries.

        Args:
            service: Filter by service/identifier
            since: Start time (e.g., "1 hour ago", "2023-01-01 10:00")
            until: End time
            level: Minimum log level
            lines: Maximum number of lines
            follow: Follow new entries (like tail -f)
        """
        log.info(
            "starting-journal-query",
            _replace_msg="🔍 Starting journal query",
            service=service,
            since=since,
            until=until,
            level=level,
            lines=lines,
            follow=follow,
        )

        if not SYSTEMD_AVAILABLE:
            log.error(
                "journal-query-failed-no-systemd",
                _replace_msg="❌ Cannot query journal - systemd-python not available",
            )
            print("systemd-python not available", file=sys.stderr)
            return

        try:
            log.debug("creating-journal-reader")
            j = journal.Reader()

            # Add filters
            if service:
                log.debug("adding-service-filter", service=service)
                j.add_match(SYSLOG_IDENTIFIER=service)

            if level:
                log.debug("adding-level-filter", level=level)
                # Filter by priority level
                level_priorities = {
                    "critical": [0, 1, 2],
                    "error": [0, 1, 2, 3],
                    "warning": [0, 1, 2, 3, 4],
                    "info": [0, 1, 2, 3, 4, 5, 6],
                    "debug": [0, 1, 2, 3, 4, 5, 6, 7],
                }
                priorities = level_priorities.get(
                    level.lower(), [0, 1, 2, 3, 4, 5, 6, 7]
                )
                log.debug(
                    "mapped-level-to-priorities", level=level, priorities=priorities
                )
                for priority in priorities:
                    j.add_match(("PRIORITY", priority))

            # Set time range
            if since:
                since_time = self.parse_time_string(since)
                log.debug("setting-since-time", since=since, parsed_time=since_time)
                j.seek_realtime(since_time)

            if until:
                until_time = self.parse_time_string(until)
                # Note: systemd journal doesn't have direct "until" support
                # We'll filter manually

            # Position cursor
            if not follow:
                if lines:
                    # Get last N entries
                    j.seek_tail()
                    j.get_previous(lines)
                else:
                    j.seek_head()
            else:
                j.seek_tail()

            count = 0
            log.debug("starting-journal-iteration", follow=follow, lines=lines)

            for entry in j:
                if lines and count >= lines and not follow:
                    log.debug("reached-line-limit", count=count, lines=lines)
                    break

                # Manual until filtering
                if until:
                    entry_time = entry.get("__REALTIME_TIMESTAMP")
                    if entry_time and entry_time.timestamp() > until_time.timestamp():
                        log.debug(
                            "entry-after-until-time",
                            entry_time=entry_time,
                            until_time=until_time,
                        )
                        continue

                parsed_entry = self.parse_journal_entry(entry)
                yield parsed_entry
                count += 1

                if count % 100 == 0:  # Log progress every 100 entries
                    log.debug("processed-entries", count=count)

                if follow:
                    # In follow mode, wait for new entries
                    log.debug("waiting-for-new-entries")
                    j.wait()

            log.info(
                "journal-query-completed",
                _replace_msg="✅ Journal query completed",
                total_entries=count,
            )

        except Exception as e:
            log.error(
                "journal-query-error",
                _replace_msg="❌ Error reading journal",
                error=str(e),
                error_type=type(e).__name__,
            )
            print(f"Error reading journal: {e}", file=sys.stderr)

    def parse_time_string(self, time_str: str) -> datetime:
        """Parse various time string formats."""
        log.debug("parsing-time-string", time_str=time_str)
        time_str = time_str.strip().lower()
        # Support monkeypatching datetime in tests by keeping it as module attribute
        now = datetime.now()

        # Relative times
        if "ago" in time_str:
            if "hour" in time_str:
                match = re.search(r"(\d+)", time_str)
                if match:
                    hours = int(match.group(1))
                    return now - timedelta(hours=hours)
            elif "minute" in time_str:
                match = re.search(r"(\d+)", time_str)
                if match:
                    minutes = int(match.group(1))
                    return now - timedelta(minutes=minutes)
            elif "day" in time_str:
                match = re.search(r"(\d+)", time_str)
                if match:
                    days = int(match.group(1))
                    return now - timedelta(days=days)

        # Absolute times
        if time_str == "today":
            # Use replace to avoid issues when datetime is patched in tests
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            if not isinstance(today, _REAL_DATETIME):
                today = _REAL_DATETIME.fromtimestamp(today.timestamp())
            return today
        elif time_str == "yesterday":
            yesterday = now - timedelta(days=1)
            y0 = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            if not isinstance(y0, _REAL_DATETIME):
                y0 = _REAL_DATETIME.fromtimestamp(y0.timestamp())
            return y0

        # Try to parse ISO format
        try:
            parsed = datetime.fromisoformat(time_str.replace("T", " "))
            # If datetime was patched in tests, ensure we return a real datetime instance
            if not isinstance(parsed, _REAL_DATETIME):
                parsed = _REAL_DATETIME.fromisoformat(time_str.replace("T", " "))
            return parsed
        except Exception as e:
            log.warning(
                "time-parse-failed",
                time_str=time_str,
                error=str(e),
                fallback="1 hour ago",
            )
            pass

        # Default to 1 hour ago
        result = now - timedelta(hours=1)
        # Ensure result is a real datetime if datetime is patched
        if not isinstance(result, _REAL_DATETIME):
            result = _REAL_DATETIME.fromtimestamp(result.timestamp())
        log.debug("parsed-time-result", original=time_str, result=result)
        return result


def main():
    """CLI interface for journal viewer."""
    log.info(
        "journal-viewer-main-started", _replace_msg="🚀 Starting journal viewer CLI"
    )
    import argparse

    parser = argparse.ArgumentParser(
        description="Beautiful systemd journal viewer - makes journalctl usable!",
        epilog="Examples:\n"
        "  %(prog)s -u myapp.service -n 50\n"
        "  %(prog)s --since '1 hour ago' --level error\n"
        "  %(prog)s -f -u myapp.service\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-u",
        "--unit",
        "--service",
        dest="service",
        help="Show logs for specific service/unit",
    )
    parser.add_argument(
        "-n",
        "--lines",
        type=int,
        default=50,
        help="Number of lines to show (default: 50)",
    )
    parser.add_argument(
        "-f",
        "--follow",
        action="store_true",
        help="Follow new log entries (like tail -f)",
    )
    parser.add_argument(
        "--since", help='Show logs since time (e.g., "1 hour ago", "today")'
    )
    parser.add_argument("--until", help="Show logs until time")
    parser.add_argument(
        "--level",
        choices=["critical", "error", "warning", "info", "debug"],
        help="Minimum log level to show",
    )
    parser.add_argument(
        "--show-hostname", action="store_true", help="Show hostname in output"
    )
    parser.add_argument(
        "--show-pid",
        action="store_true",
        default=True,
        help="Show process ID (default: true)",
    )
    parser.add_argument(
        "--no-service", action="store_true", help="Hide service/identifier"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output raw JSON instead of formatted text"
    )

    args, _unknown = parser.parse_known_args()

    if not SYSTEMD_AVAILABLE:
        log.error(
            "main-systemd-unavailable",
            _replace_msg="❌ Cannot start journal viewer - systemd-python not available",
        )
        print(
            "Error: systemd-python not available. Install with: pip install systemd-python",
            file=sys.stderr,
        )
        sys.exit(1)
        return

    try:
        # Create viewer
        log.debug(
            "creating-journal-viewer-instance",
            show_hostname=args.show_hostname,
            show_pid=args.show_pid,
            show_service=not args.no_service,
        )
        viewer = JournalViewer(
            show_hostname=args.show_hostname,
            show_pid=args.show_pid,
            show_service=not args.no_service,
        )
        log.info(
            "journal-viewer-created", _replace_msg="✅ Journal viewer instance created"
        )
    except Exception as e:
        log.error(
            "viewer-creation-failed",
            _replace_msg="❌ Failed to create journal viewer",
            error=str(e),
            error_type=type(e).__name__,
        )
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
        return

    try:
        # Query and display entries
        log.info(
            "starting-journal-display",
            _replace_msg="📖 Starting journal display",
            output_format="json" if args.json else "formatted",
        )

        entry_count = 0
        for entry in viewer.query_journal(
            service=args.service,
            since=args.since,
            until=args.until,
            level=args.level,
            lines=args.lines,
            follow=args.follow,
        ):
            if args.json:
                # Output raw JSON
                print(json.dumps(entry.raw_entry, default=str, indent=2))
            else:
                # Beautiful formatted output
                print(viewer.format_entry(entry))

            entry_count += 1

        log.info(
            "journal-display-completed",
            _replace_msg="✅ Journal display completed",
            entries_displayed=entry_count,
        )

    except KeyboardInterrupt:
        log.info("user-interrupted", _replace_msg="👋 User interrupted journal viewer")
        print("\n👋 Goodbye!", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        log.error(
            "main-execution-error",
            _replace_msg="❌ Error during journal viewing",
            error=str(e),
            error_type=type(e).__name__,
        )
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
