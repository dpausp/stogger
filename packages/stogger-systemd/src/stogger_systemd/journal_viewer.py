"""Beautiful systemd journal viewer - makes journalctl actually usable!

Reads binary journal logs and displays them with stogger's beautiful formatting.
"""

import argparse
import json
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, ClassVar

import structlog

# Get a logger for this module
log = structlog.get_logger(__name__)


@dataclass
class JournalQueryOptions:
    """Options for journal queries."""

    service: str | None = None
    since: str | None = None
    until: str | None = None
    level: str | None = None
    lines: int | None = None
    follow: bool = False


from stogger._colors import BLUE, BRIGHT, CYAN, DIM, GREEN, MAGENTA, RED, RESET_ALL, YELLOW


@dataclass
class JournalEntry:
    """Structured representation of a journal entry."""

    timestamp: datetime
    hostname: str
    service: str
    pid: str
    level: str
    message: str
    fields: dict[str, Any]
    raw_entry: dict[str, Any]


class JournalViewer:
    """Beautiful viewer for systemd journal logs.

    Converts binary journal entries back into human-readable format
    with the same beautiful styling as stogger console output.
    """

    PRIORITY_TO_LEVEL: ClassVar[dict[int, str]] = {
        0: "critical",  # LOG_EMERG
        1: "critical",  # LOG_ALERT
        2: "critical",  # LOG_CRIT
        3: "error",  # LOG_ERR
        4: "warning",  # LOG_WARNING
        5: "info",  # LOG_NOTICE
        6: "info",  # LOG_INFO
        7: "debug",  # LOG_DEBUG
    }

    LEVEL_COLORS: ClassVar[dict[str, str]] = {
        "critical": RED,
        "error": RED,
        "warning": YELLOW,
        "info": GREEN,
        "debug": DIM,
    }

    def __init__(
        self,
        *,
        show_hostname: bool = False,
        show_pid: bool = True,
        show_service: bool = True,
        max_width: int = 120,
    ) -> None:
        """Initialize journal viewer.

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

        log.debug(
            "journal-viewer-initialized",
            _replace_msg="✅ Journal viewer ready",
        )

    def parse_journal_entry(self, entry: dict[str, Any]) -> JournalEntry:
        """Parse a raw journal entry into structured format."""
        log.debug(
            "parsing-journal-entry",
            has_timestamp=bool(entry.get("__REALTIME_TIMESTAMP")),
            entry_keys=list(entry.keys())[:10],
        )  # Limit keys for readability

        # Extract timestamp
        timestamp = entry.get("__REALTIME_TIMESTAMP")
        if timestamp:
            timestamp = datetime.fromtimestamp(timestamp.timestamp(), tz=UTC)
        else:
            log.warning(
                "missing-timestamp-in-entry",
                _replace_msg="⚠️  Journal entry missing timestamp, using current time",
            )
            timestamp = datetime.now(tz=UTC)

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

        # Extract custom fields (stogger fields)
        fields = {}
        for key, value in entry.items():
            if key.startswith("STOGGER_"):
                field_name = key.replace("STOGGER_", "").lower()
                # Try to parse JSON values
                try:
                    if isinstance(value, str) and (value.startswith(("{", "["))):
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
                value_str = json.dumps(value, separators=(",", ":")) if isinstance(value, dict | list) else str(value)
                field_parts.append(
                    f"{CYAN}{key}{RESET_ALL}={MAGENTA}{value_str}{RESET_ALL}",
                )

            if field_parts:
                parts.append(" ".join(field_parts))

        return " ".join(parts)

    def query_journal(self, options: JournalQueryOptions) -> Iterator[JournalEntry]:
        """Query systemd journal and yield formatted entries.

        Args:
            options: JournalQueryOptions with query parameters.

        """
        if not isinstance(options, JournalQueryOptions):
            msg = f"Expected JournalQueryOptions, got {type(options).__name__}"
            raise TypeError(msg)

        log.debug(
            "starting-journal-query",
            service=options.service,
            since=options.since,
            until=options.until,
            level=options.level,
            lines=options.lines,
            follow=options.follow,
        )

        try:
            from systemd import journal  # type: ignore[import-not-found]

            log.debug("creating-journal-reader")
            j = journal.Reader()

            # Add filters
            if options.service:
                log.debug("adding-service-filter", service=options.service)
                j.add_match(SYSLOG_IDENTIFIER=options.service)

            if options.level:
                log.debug("adding-level-filter", level=options.level)
                # Filter by priority level
                level_priorities = {
                    "critical": [0, 1, 2],
                    "error": [0, 1, 2, 3],
                    "warning": [0, 1, 2, 3, 4],
                    "info": [0, 1, 2, 3, 4, 5, 6],
                    "debug": [0, 1, 2, 3, 4, 5, 6, 7],
                }
                priorities = level_priorities.get(
                    options.level.lower(),
                    [0, 1, 2, 3, 4, 5, 6, 7],
                )
                log.debug(
                    "mapped-level-to-priorities",
                    level=options.level,
                    priorities=priorities,
                )
                for priority in priorities:
                    j.add_match(("PRIORITY", priority))

            # Set time range
            if options.since:
                since_time = self.parse_time_string(options.since)
                log.debug("setting-since-time", since=options.since, parsed_time=since_time)
                j.seek_realtime(since_time)

            if options.until:
                until_time = self.parse_time_string(options.until)
                # Note: systemd journal doesn't have direct "until" support
                # We'll filter manually

            # Position cursor
            if not options.follow:
                if options.lines:
                    # Get last N entries
                    j.seek_tail()
                    j.get_previous(options.lines)
                else:
                    j.seek_head()
            else:
                j.seek_tail()

            count = 0
            log.debug("starting-journal-iteration", follow=options.follow, lines=options.lines)

            for entry in j:
                if options.lines and count >= options.lines and not options.follow:
                    log.debug("reached-line-limit", count=count, lines=options.lines)
                    break

                # Manual until filtering
                if options.until:
                    entry_time = entry.get("__REALTIME_TIMESTAMP")
                    if entry_time and entry_time.timestamp() > until_time.timestamp():
                        log.debug(
                            "entry-after-until-time",
                            entry_time=entry_time,
                            until_time=until_time,
                        )
                        continue

                yield self.parse_journal_entry(entry)
                count += 1

                if count % 100 == 0:  # Log progress every 100 entries
                    log.debug("processed-entries", count=count)

                if options.follow:
                    # In follow mode, wait for new entries
                    log.debug("waiting-for-new-entries")
                    j.wait()

            log.info(
                "journal-query-completed",
                _replace_msg="✅ Journal query completed",
                total_entries=count,
            )

        except Exception as e:
            log.exception(
                "journal-query-error",
                _replace_msg="❌ Error reading journal",
                error=str(e),
                error_type=type(e).__name__,
            )

    def parse_time_string(self, time_str: str) -> datetime:
        """Parse various time string formats."""
        log.debug("parsing-time-string", time_str=time_str)
        time_str = time_str.strip().lower()
        # Support monkeypatching datetime in tests by keeping it as module attribute
        now = datetime.now(tz=UTC)

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
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        if time_str == "yesterday":
            yesterday = now - timedelta(days=1)
            return yesterday.replace(hour=0, minute=0, second=0, microsecond=0)

        # Try to parse ISO format
        try:
            parsed = datetime.fromisoformat(time_str.replace("T", " "))
        except (ValueError, TypeError) as e:
            log.warning(
                "time-parse-failed",
                time_str=time_str,
                error=str(e),
                fallback="1 hour ago",
            )
        else:
            return parsed

        # Default to 1 hour ago
        result = now - timedelta(hours=1)
        log.debug("parsed-time-result", original=time_str, result=result)
        return result


def main() -> None:
    """CLI interface for journal viewer."""
    log.info(
        "journal-viewer-main-started",
        _replace_msg="🚀 Starting journal viewer CLI",
    )
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
        "--since",
        help='Show logs since time (e.g., "1 hour ago", "today")',
    )
    parser.add_argument("--until", help="Show logs until time")
    parser.add_argument(
        "--level",
        choices=["critical", "error", "warning", "info", "debug"],
        help="Minimum log level to show",
    )
    parser.add_argument(
        "--show-hostname",
        action="store_true",
        help="Show hostname in output",
    )
    parser.add_argument(
        "--show-pid",
        action="store_true",
        default=True,
        help="Show process ID (default: true)",
    )
    parser.add_argument(
        "--no-service",
        action="store_true",
        help="Hide service/identifier",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON instead of formatted text",
    )

    args, _unknown = parser.parse_known_args()

    try:
        viewer = JournalViewer(
            show_hostname=args.show_hostname,
            show_pid=args.show_pid,
            show_service=not args.no_service,
        )
        log.info(
            "journal-viewer-created",
            _replace_msg="✅ Journal viewer instance created",
        )
    except Exception as e:
        log.exception(
            "viewer-creation-failed",
            _replace_msg="❌ Failed to create journal viewer",
            error=str(e),
            error_type=type(e).__name__,
        )
        sys.exit(1)
        return

    try:
        log.info(
            "starting-journal-display",
            _replace_msg="📖 Starting journal display",
            output_format="json" if args.json else "formatted",
        )

        entry_count = 0
        for _entry in viewer.query_journal(
            JournalQueryOptions(
                service=args.service,
                since=args.since,
                until=args.until,
                level=args.level,
                lines=args.lines,
                follow=args.follow,
            ),
        ):
            if args.json:
                pass

            entry_count += 1

        log.info(
            "journal-display-completed",
            _replace_msg="✅ Journal display completed",
            entries_displayed=entry_count,
        )

    except KeyboardInterrupt:
        log.info("user-interrupted", _replace_msg="👋 User interrupted journal viewer")
        sys.exit(0)
    except Exception as e:
        log.exception(
            "main-execution-error",
            _replace_msg="❌ Error during journal viewing",
            error=str(e),
            error_type=type(e).__name__,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
