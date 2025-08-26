# 🔌 Integrations

nicestlog provides integrations and examples for common ecosystems. The snippets below reflect the current API.

## Eliot Integration

Use the Eliot helpers to get beautiful, human-readable action traces.

```python
from nicestlog.eliot_integration import setup_eliot_logging, log_action, log_call

# Configure Eliot output (human-readable by default)
setup_eliot_logging(human_readable=True, show_timestamps=True)

# Context-managed action
with log_action("user-registration", user_email="user@example.com"):
    # ... registration logic ...
    pass

# Decorate functions to log calls as actions
@log_call("send-welcome-email")
def send_email(user_id: int) -> bool:
    # ...
    return True
```

## Systemd Integration

Send logs to the systemd journal when running as a service.

```python
import structlog
from nicestlog.systemd_integration import setup_systemd_logging, detect_systemd_environment

# Only enable when systemd is available
if detect_systemd_environment():
    setup_systemd_logging(syslog_identifier="my-app")

log = structlog.get_logger("service")
log.info("service-started", pid=os.getpid())
```

## Web Dashboard

Simple real-time log viewer powered by Flask + HTMX.

**Note:** The web dashboard requires Flask as an optional dependency. Install it with:

```bash
pip install 'nicestlog[web]'
# or
pip install flask>=3.0.3
```

```python
from nicestlog.web_dashboard import run_dashboard, setup_web_logging
import structlog

# Route logs to the in-memory dashboard buffer
setup_web_logging()
log = structlog.get_logger("demo")

# Start the dashboard on http://127.0.0.1:8080
run_dashboard(port=8080, debug=False)
```

## Flask Example

```python
from flask import Flask, request
import structlog
import nicestlog

nicestlog.init_logging(verbose=True)
app = Flask(__name__)
log = structlog.get_logger("web")

@app.before_request
def log_request():
    log.info(
        "request-started",
        method=request.method,
        path=request.path,
        user_agent=request.headers.get("User-Agent"),
    )
```

## FastAPI Example

```python
from fastapi import FastAPI
import structlog
import nicestlog

nicestlog.init_logging(verbose=True)
app = FastAPI()
log = structlog.get_logger("api")

@app.middleware("http")
async def log_requests(request, call_next):
    log.info("request-started", method=request.method, url=str(request.url))
    response = await call_next(request)
    log.info("request-completed", status_code=response.status_code)
    return response
```
