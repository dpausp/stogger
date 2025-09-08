#!/usr/bin/env python3
"""Demo: Beautiful systemd journal viewer

Shows how to read and beautifully format systemd journal logs.
"""

import time

import structlog

import nicestlog
from nicestlog.journal_viewer import SYSTEMD_AVAILABLE, JournalViewer


def generate_test_logs():
    """Generate some test logs to demonstrate the viewer."""
    print("📝 Generating test logs for journal viewer demo...")

    # Setup nicestlog with systemd integration
    nicestlog.init_logging(
        verbose=True,
        syslog_identifier="journal-viewer-demo",
        enable_systemd=True,
    )

    log = structlog.get_logger("demo")

    # Generate various types of logs
    log.info(
        "demo_started",
        demo_version="1.0",
        timestamp=time.time(),
        user="demo-user",
    )

    log.debug(
        "configuration_loaded",
        config_file="/etc/demo/config.yaml",
        settings_count=42,
    )

    log.warning(
        "memory_usage_high",
        memory_percent=85.5,
        threshold=80,
        process="demo-app",
    )

    log.error(
        "database_connection_failed",
        host="db.example.com",
        port=5432,
        error="Connection timeout",
        retry_count=3,
    )

    log.info(
        "user_action",
        action="login",
        user_id=12345,
        ip_address="[REDACTED]",  # PII scrubbing in action!
        user_agent="Mozilla/5.0...",
    )

    log.critical(
        "system_overload",
        cpu_percent=98.7,
        memory_percent=95.2,
        disk_percent=89.1,
        action="emergency_shutdown",
    )

    print("✅ Test logs generated!")


def demo_journal_viewer():
    """Demonstrate the journal viewer capabilities."""
    if not SYSTEMD_AVAILABLE:
        print("⚠️  systemd-python not available - showing mock demo")
        show_mock_output()
        return

    print("\n🔍 Journal Viewer Demo")
    print("=" * 60)

    # Create viewer
    viewer = JournalViewer(show_hostname=False, show_pid=True, show_service=True)

    print("📖 Recent logs from journal (last 10 entries):")
    print("-" * 60)

    try:
        count = 0
        for entry in viewer.query_journal(
            service="journal-viewer-demo",
            lines=10,
            since="5 minutes ago",
        ):
            print(viewer.format_entry(entry))
            count += 1

        if count == 0:
            print("   (No recent logs found - run generate_test_logs() first)")

    except Exception as e:
        print(f"   Error reading journal: {e}")

    print("\n💡 Usage examples:")
    print("   uv run python -m nicestlog journal -u myapp.service -n 50")
    print("   uv run python -m nicestlog journal --since '1 hour ago' --level error")
    print("   uv run python -m nicestlog journal -f -u myapp.service  # Follow live")


def show_mock_output():
    """Show what the journal viewer output would look like."""
    print("\n🎭 Mock Journal Viewer Output:")
    print("=" * 60)

    # Simulate beautiful journal output
    from nicestlog.core import (
        BLUE,
        BRIGHT,
        CYAN,
        DIM,
        GREEN,
        MAGENTA,
        RED,
        RESET_ALL,
        YELLOW,
    )

    mock_entries = [
        (
            "14:23:45.123",
            "I",
            "journal-viewer-demo",
            "1234",
            "demo_started",
            {"demo_version": "1.0", "user": "demo-user"},
        ),
        (
            "14:23:45.156",
            "D",
            "journal-viewer-demo",
            "1234",
            "configuration_loaded",
            {"config_file": "/etc/demo/config.yaml", "settings_count": 42},
        ),
        (
            "14:23:45.189",
            "W",
            "journal-viewer-demo",
            "1234",
            "memory_usage_high",
            {"memory_percent": 85.5, "threshold": 80},
        ),
        (
            "14:23:45.234",
            "E",
            "journal-viewer-demo",
            "1234",
            "database_connection_failed",
            {"host": "db.example.com", "error": "Connection timeout"},
        ),
        (
            "14:23:45.267",
            "C",
            "journal-viewer-demo",
            "1234",
            "system_overload",
            {"cpu_percent": 98.7, "action": "emergency_shutdown"},
        ),
    ]

    level_colors = {"I": GREEN, "D": DIM, "W": YELLOW, "E": RED, "C": RED}

    for timestamp, level, service, pid, message, fields in mock_entries:
        color = level_colors.get(level, "")

        # Format like the real viewer
        parts = [
            f"{DIM}{timestamp}{RESET_ALL}",
            f"{color}{level}{RESET_ALL}",
            f"[{BLUE}{BRIGHT}{service}{RESET_ALL}]",
            f"{DIM}({pid}){RESET_ALL}",
            f"{BRIGHT}{message}{RESET_ALL}",
        ]

        # Add fields
        if fields:
            field_parts = []
            for key, value in fields.items():
                field_parts.append(
                    f"{CYAN}{key}{RESET_ALL}={MAGENTA}{value}{RESET_ALL}",
                )
            parts.append(" ".join(field_parts))

        print(" ".join(parts))

    print("\n✨ This is how your systemd journal logs would look!")
    print("💡 Much better than raw journalctl output, right?")


def show_comparison():
    """Show comparison between journalctl and nicestlog journal viewer."""
    print("\n📊 Comparison: journalctl vs nicestlog journal")
    print("=" * 60)

    print("🤮 Traditional journalctl output:")
    print(
        "Dec 07 14:23:45 hostname myapp[1234]: {'level': 'info', 'event': 'user_login', 'user_id': 12345, 'timestamp': '2023-12-07T14:23:45.123456'}",
    )
    print(
        "Dec 07 14:23:46 hostname myapp[1234]: {'level': 'error', 'event': 'db_error', 'error': 'connection failed', 'host': 'db.example.com'}",
    )

    print("\n😍 Beautiful nicestlog journal output:")
    print("14:23:45.123 I [myapp] (1234) user_login user_id=12345")
    print(
        "14:23:46.789 E [myapp] (1234) db_error error='connection failed' host=db.example.com",
    )

    print("\n🎯 Benefits:")
    print("   ✅ Colored output for easy scanning")
    print("   ✅ Compact, readable format")
    print("   ✅ Structured data clearly displayed")
    print("   ✅ Same beautiful style as console logs")
    print("   ✅ Easy filtering and following")
    print("   ✅ Works with existing systemd infrastructure")


def show_cli_examples():
    """Show CLI usage examples."""
    print("\n🛠️  CLI Usage Examples:")
    print("=" * 60)

    examples = [
        ("View recent logs", "uv run python -m nicestlog journal -u myapp.service"),
        ("Follow live logs", "uv run python -m nicestlog journal -f -u myapp.service"),
        ("Show only errors", "uv run python -m nicestlog journal --level error"),
        ("Last hour's logs", "uv run python -m nicestlog journal --since '1 hour ago'"),
        ("Last 100 entries", "uv run python -m nicestlog journal -n 100"),
        ("Specific service", "uv run python -m nicestlog journal -u nginx.service"),
        ("Debug level logs", "uv run python -m nicestlog journal --level debug -n 20"),
    ]

    for description, command in examples:
        print(f"📋 {description}:")
        print(f"   {command}")
        print()

    print("💡 This replaces the need for complex journalctl commands!")
    print("💡 No more piping through jq or struggling with JSON output!")


if __name__ == "__main__":
    print("🎭 Journal Viewer Demo - Making systemd logs beautiful!")
    print("=" * 60)

    # Generate test logs first
    generate_test_logs()

    # Wait a moment for logs to be written
    time.sleep(1)

    # Demo the viewer
    demo_journal_viewer()

    # Show comparisons and examples
    show_comparison()
    show_cli_examples()

    print("\n🎉 Journal viewer demo complete!")
    print("💡 This is the missing piece that makes systemd logging actually usable!")
    print("🚀 Logging Nirvana achieved! 🧘‍♂️✨")
