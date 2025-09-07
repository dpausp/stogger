#!/usr/bin/env python3
"""Demo: Advanced systemd integration with nicestlog

Shows how to properly integrate with systemd for production deployments.
"""

import os
import time

import structlog

import nicestlog
from nicestlog import detect_systemd_environment


def demo_systemd_features():
    """Demonstrate systemd integration features."""
    print("🔧 Systemd Integration Demo")
    print("=" * 60)

    # Check systemd environment
    env_info = detect_systemd_environment()
    print("🔍 Environment Detection:")
    print(f"   Running under systemd: {env_info['running_under_systemd']}")
    print(f"   Journal available: {env_info['journal_available']}")
    print(f"   Service name: {env_info['service_name'] or 'Not detected'}")
    print(f"   Unit name: {env_info['unit_name'] or 'Not detected'}")
    print(f"   Invocation ID: {env_info['invocation_id'] or 'Not set'}")

    # Initialize logging with systemd support
    print("\n📝 Setting up logging...")
    nicestlog.init_logging(
        verbose=True,
        syslog_identifier="systemd-demo",
        enable_systemd=True,
        log_to_console=True,  # Also log to console for demo
    )

    log = structlog.get_logger("systemd_demo")

    print("\n🚀 Generating test logs for systemd...")

    # Application startup logs
    log.info(
        "application_startup",
        version="1.0.0",
        config_file="/etc/myapp/config.yaml",
        pid=os.getpid(),
    )

    # Simulate some application activity
    for i in range(3):
        log.info(
            "processing_request",
            request_id=f"req-{1000 + i}",
            user_id=42,
            endpoint="/api/data",
            duration_ms=150 + i * 50,
        )

        if i == 1:
            log.warning(
                "rate_limit_warning",
                user_id=42,
                requests_per_minute=95,
                limit=100,
            )

        time.sleep(0.5)

    # Database operations
    log.info(
        "database_operation",
        operation="SELECT",
        table="users",
        rows_affected=1,
        execution_time_ms=23,
    )

    # Error simulation
    log.error(
        "database_connection_failed",
        error="Connection timeout",
        host="db.example.com",
        port=5432,
        retry_count=3,
    )

    # Recovery
    log.info(
        "database_connection_restored",
        host="db-backup.example.com",
        failover_time_ms=2500,
    )

    print("\n✅ Logs sent to systemd journal!")
    print("💡 View with: journalctl -f SYSLOG_IDENTIFIER=systemd-demo")
    print("💡 Filter errors: journalctl SYSLOG_IDENTIFIER=systemd-demo PRIORITY=3")
    print("💡 Follow live: journalctl -f -u your-service-name")


def show_systemd_commands():
    """Show useful systemd commands for log management."""
    print("\n📚 Useful systemd/journalctl commands:")
    print("=" * 60)

    commands = [
        ("View all logs for a service", "journalctl -u myapp.service"),
        ("Follow logs in real-time", "journalctl -f -u myapp.service"),
        ("Show only errors", "journalctl -u myapp.service -p err"),
        ("Show logs since boot", "journalctl -u myapp.service -b"),
        (
            "Show logs from last hour",
            "journalctl -u myapp.service --since '1 hour ago'",
        ),
        ("Show logs with specific identifier", "journalctl SYSLOG_IDENTIFIER=myapp"),
        ("Export logs as JSON", "journalctl -u myapp.service -o json"),
        ("Show disk usage", "journalctl --disk-usage"),
        ("Vacuum old logs", "journalctl --vacuum-time=30d"),
        ("Show structured fields", "journalctl -u myapp.service -o json-pretty"),
    ]

    for description, command in commands:
        print(f"📋 {description}:")
        print(f"   {command}")
        print()


def generate_example_service():
    """Generate an example systemd service file."""
    print("\n📄 Example systemd service file generation:")
    print("=" * 60)

    from nicestlog.systemd_integration import create_systemd_service_file

    # Example Python web app
    service_content = create_systemd_service_file(
        service_name="my-web-app",
        exec_command="/opt/myapp/venv/bin/python /opt/myapp/app.py",
        user="myapp",
        working_directory="/opt/myapp",
        environment={
            "PYTHONPATH": "/opt/myapp",
            "LOG_LEVEL": "info",
            "DATABASE_URL": "postgresql://localhost/myapp",
        },
        restart_policy="always",
    )

    print(service_content)

    print("💾 Save this as: /etc/systemd/system/my-web-app.service")
    print("🔄 Then run:")
    print("   sudo systemctl daemon-reload")
    print("   sudo systemctl enable my-web-app")
    print("   sudo systemctl start my-web-app")
    print("   sudo systemctl status my-web-app")


def show_production_tips():
    """Show production deployment tips."""
    print("\n🏭 Production Deployment Tips:")
    print("=" * 60)

    tips = [
        "🔒 Use dedicated user accounts for services (not root!)",
        "📁 Set proper working directories and file permissions",
        "🔄 Configure appropriate restart policies (always, on-failure)",
        "📊 Use structured logging with consistent field names",
        "⚡ Enable log rotation: journalctl --vacuum-time=30d",
        "🔍 Monitor logs with: journalctl -f -u your-service",
        "📈 Set up log forwarding to centralized systems",
        "🚨 Configure systemd notifications for failures",
        "💾 Backup important logs before rotation",
        "🔧 Test service files with: systemd-analyze verify",
    ]

    for tip in tips:
        print(f"   {tip}")

    print("\n🎯 nicestlog makes all of this easier with:")
    print("   ✅ Automatic systemd detection and integration")
    print("   ✅ Proper structured logging with systemd fields")
    print("   ✅ Service file generation with best practices")
    print("   ✅ PII scrubbing for compliance")
    print("   ✅ Web dashboard for real-time monitoring")


if __name__ == "__main__":
    demo_systemd_features()
    show_systemd_commands()
    generate_example_service()
    show_production_tips()

    print("\n🎉 Systemd integration demo complete!")
    print("💡 Try: uv run python -m nicestlog generate-service my-app 'python app.py'")
