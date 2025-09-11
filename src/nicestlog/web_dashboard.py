"""Simple Flask + HTMX web dashboard for live log viewing.

No async bullshit, just good old Flask with HTMX for live updates.
"""

from datetime import datetime
import queue
import threading
import time
from typing import Any

try:
    from flask import Flask, render_template_string, request

    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    # Create dummy classes for type hints when Flask is not available
    Flask = None
    render_template_string = None
    request = None

import structlog

# Simple in-memory log storage
log_buffer: queue.Queue[dict[str, Any]] = queue.Queue(maxsize=1000)
recent_logs: list[dict[str, Any]] = []
log_lock = threading.Lock()


class WebLogHandler:
    """Log handler that feeds logs to the web dashboard."""

    def __init__(self):
        self.session_id = int(time.time())

    def __call__(self, _, __, event_dict):
        """Capture log events for web display."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": event_dict.get("level", "info"),
            "event": event_dict.get("event", ""),
            "logger": event_dict.get("logger", "root"),
            "data": {
                k: v
                for k, v in event_dict.items()
                if k not in ["timestamp", "level", "event", "logger"]
            },
            "session_id": self.session_id,
        }

        with log_lock:
            recent_logs.append(log_entry)
            # Keep only last 500 logs
            if len(recent_logs) > 500:
                recent_logs.pop(0)

        try:
            log_buffer.put_nowait(log_entry)
        except queue.Full:
            pass  # Drop logs if buffer is full

        return event_dict


# HTML Templates (embedded because we're keeping it simple)
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nicestlog Dashboard</title>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <style>
        body {
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            background: #1a1a1a;
            color: #e0e0e0;
            margin: 0;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            color: white;
            font-size: 2em;
        }
        .controls {
            background: #2d2d2d;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
            align-items: center;
        }
        .log-container {
            background: #2d2d2d;
            border-radius: 8px;
            padding: 20px;
            max-height: 70vh;
            overflow-y: auto;
            border: 1px solid #444;
        }
        .log-entry {
            margin-bottom: 10px;
            padding: 10px;
            border-left: 4px solid #666;
            background: #333;
            border-radius: 4px;
            font-size: 14px;
            line-height: 1.4;
        }
        .log-entry.debug { border-left-color: #888; }
        .log-entry.info { border-left-color: #4CAF50; }
        .log-entry.warning { border-left-color: #FF9800; }
        .log-entry.error { border-left-color: #f44336; }
        .log-entry.critical { border-left-color: #9C27B0; }

        .log-timestamp {
            color: #888;
            font-size: 12px;
        }
        .log-level {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: bold;
            font-size: 11px;
            margin-right: 8px;
        }
        .log-level.debug { background: #666; color: white; }
        .log-level.info { background: #4CAF50; color: white; }
        .log-level.warning { background: #FF9800; color: white; }
        .log-level.error { background: #f44336; color: white; }
        .log-level.critical { background: #9C27B0; color: white; }

        .log-event {
            color: #e0e0e0;
            font-weight: bold;
            margin-right: 10px;
        }
        .log-logger {
            color: #64B5F6;
            font-size: 12px;
            margin-right: 10px;
        }
        .log-data {
            color: #A5D6A7;
            font-size: 12px;
            margin-top: 5px;
        }
        .btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        .btn:hover {
            background: #5a67d8;
        }
        .btn.danger {
            background: #f44336;
        }
        .btn.danger:hover {
            background: #d32f2f;
        }
        select {
            background: #444;
            color: white;
            border: 1px solid #666;
            padding: 8px;
            border-radius: 4px;
        }
        .stats {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: #2d2d2d;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            flex: 1;
        }
        .stat-number {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            font-size: 12px;
            color: #888;
            margin-top: 5px;
        }
        .auto-scroll {
            position: sticky;
            bottom: 20px;
            text-align: right;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚽 Nicestlog Dashboard</h1>
        <p>Live log monitoring with style!</p>
    </div>

    <div class="stats" id="stats" hx-get="/api/stats" hx-trigger="every 2s">
        <div class="stat-card">
            <div class="stat-number">{{ stats.total_logs }}</div>
            <div class="stat-label">Total Logs</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{{ stats.error_count }}</div>
            <div class="stat-label">Errors</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{{ stats.warning_count }}</div>
            <div class="stat-label">Warnings</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{{ stats.logs_per_minute }}</div>
            <div class="stat-label">Logs/min</div>
        </div>
    </div>

    <div class="controls">
        <button class="btn" hx-post="/api/clear" hx-target="#logs">Clear Logs</button>
        <select id="level-filter" hx-get="/api/logs" hx-target="#logs" hx-trigger="change">
            <option value="">All Levels</option>
            <option value="debug">Debug</option>
            <option value="info">Info</option>
            <option value="warning">Warning</option>
            <option value="error">Error</option>
            <option value="critical">Critical</option>
        </select>
        <label>
            <input type="checkbox" id="auto-scroll" checked> Auto-scroll
        </label>
        <span style="margin-left: auto; color: #888;">
            Live updates every 1s
        </span>
    </div>

    <div class="log-container">
        <div id="logs" hx-get="/api/logs" hx-trigger="every 1s">
            <!-- Logs will be loaded here -->
        </div>
        <div class="auto-scroll">
            <button class="btn" onclick="scrollToBottom()">📍 Scroll to Bottom</button>
        </div>
    </div>

    <script>
        function scrollToBottom() {
            const container = document.querySelector('.log-container');
            container.scrollTop = container.scrollHeight;
        }

        // Auto-scroll when new logs arrive
        document.body.addEventListener('htmx:afterSwap', function(evt) {
            if (evt.detail.target.id === 'logs' && document.getElementById('auto-scroll').checked) {
                setTimeout(scrollToBottom, 100);
            }
        });

        // Initial scroll to bottom
        setTimeout(scrollToBottom, 500);
    </script>
</body>
</html>
"""

LOG_ENTRY_TEMPLATE = """
<div class="log-entry {{ log.level }}">
    <span class="log-timestamp">{{ log.timestamp[:19] }}</span>
    <span class="log-level {{ log.level }}">{{ log.level.upper() }}</span>
    <span class="log-logger">[{{ log.logger }}]</span>
    <span class="log-event">{{ log.event }}</span>
    {% if log.data %}
    <div class="log-data">
        {% for key, value in log.data.items() %}
            <span style="color: #81C784;">{{ key }}</span>=<span style="color: #F8BBD0;">{{ value }}</span>
        {% endfor %}
    </div>
    {% endif %}
</div>
"""


def create_dashboard_app():
    """Create the Flask dashboard app."""
    if not FLASK_AVAILABLE:
        msg = "Flask is not installed. Install it with: pip install 'nicestlog[web]' or pip install flask>=3.0.3"
        raise ImportError(
            msg,
        )
    app = Flask(__name__)

    @app.route("/")
    def dashboard():
        """Main dashboard page."""
        stats = get_log_stats()
        return render_template_string(DASHBOARD_HTML, stats=stats)

    @app.route("/api/logs")
    def get_logs():
        """Get recent logs as HTML."""
        level_filter = request.args.get("level", "").lower()

        with log_lock:
            logs = recent_logs.copy()

        if level_filter:
            logs = [log for log in logs if log["level"] == level_filter]

        # Render logs as HTML
        html_parts = []
        for log in logs[-100:]:  # Show last 100 logs
            html = render_template_string(LOG_ENTRY_TEMPLATE, log=log)
            html_parts.append(html)

        return "".join(html_parts)

    @app.route("/api/stats")
    def api_stats():
        """Get log statistics."""
        stats = get_log_stats()
        return render_template_string(
            """
        <div class="stat-card">
            <div class="stat-number">{{ stats.total_logs }}</div>
            <div class="stat-label">Total Logs</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{{ stats.error_count }}</div>
            <div class="stat-label">Errors</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{{ stats.warning_count }}</div>
            <div class="stat-label">Warnings</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{{ stats.logs_per_minute }}</div>
            <div class="stat-label">Logs/min</div>
        </div>
        """,
            stats=stats,
        )

    @app.route("/api/clear", methods=["POST"])
    def clear_logs():
        """Clear all logs."""
        with log_lock:
            recent_logs.clear()
        return '<div style="text-align: center; color: #888; padding: 20px;">Logs cleared! 🧹</div>'

    return app


def get_log_stats():
    """Calculate log statistics."""
    with log_lock:
        logs = recent_logs.copy()

    total_logs = len(logs)
    error_count = len(
        [
            log_entry
            for log_entry in logs
            if log_entry["level"] in ["error", "critical"]
        ],
    )
    warning_count = len(
        [log_entry for log_entry in logs if log_entry["level"] == "warning"],
    )

    # Calculate logs per minute (rough estimate)
    if logs:
        recent_logs_1min = [
            log_entry
            for log_entry in logs
            if (
                datetime.now() - datetime.fromisoformat(log_entry["timestamp"])
            ).total_seconds()
            < 60
        ]
        logs_per_minute = len(recent_logs_1min)
    else:
        logs_per_minute = 0

    return {
        "total_logs": total_logs,
        "error_count": error_count,
        "warning_count": warning_count,
        "logs_per_minute": logs_per_minute,
    }


def setup_web_logging():
    """Setup web logging integration."""
    web_handler = WebLogHandler()
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            web_handler,  # Add our web handler
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    return web_handler


def run_dashboard(host="127.0.0.1", port=8080, debug=False):
    """Run the web dashboard."""
    if not FLASK_AVAILABLE:
        msg = (
            "Flask is not installed. To use the web dashboard, install it with:\n"
            "  pip install 'nicestlog[web]'\n"
            "or\n"
            "  pip install flask>=3.0.3"
        )
        raise ImportError(
            msg,
        )


    app = create_dashboard_app()
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == "__main__":
    # Demo mode
    import random
    import threading
    import time

    def generate_demo_logs():
        """Generate demo logs for testing."""
        setup_web_logging()
        log = structlog.get_logger("demo")

        actions = [
            "user_login",
            "api_request",
            "database_query",
            "cache_hit",
            "file_upload",
            "email_sent",
            "payment_processed",
        ]

        while True:
            action = random.choice(actions)
            level = random.choices(
                ["debug", "info", "warning", "error"],
                weights=[20, 60, 15, 5],
            )[0]

            getattr(log, level)(
                action,
                user_id=random.randint(1, 1000),
                duration_ms=random.randint(10, 500),
                status_code=random.choice([200, 201, 400, 404, 500]),
            )

            time.sleep(random.uniform(0.5, 3.0))

    # Start demo log generation in background
    demo_thread = threading.Thread(target=generate_demo_logs, daemon=True)
    demo_thread.start()

    # Run dashboard
    run_dashboard(debug=True)
