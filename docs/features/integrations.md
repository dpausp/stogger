# 🔌 Integrations

nicestlog provides seamless integration with popular Python logging frameworks and systems.

## Eliot Integration

nicestlog integrates beautifully with Eliot for action-based structured logging:

```python
from nicestlog.eliot_integration import EliotLogger
from eliot import start_action

# Use nicestlog with Eliot actions
logger = EliotLogger()

with start_action(action_type="user-registration"):
    logger.info("registration-started", user_email="user@example.com")
    # ... registration logic ...
    logger.info("registration-completed", user_id=123)
```

## Systemd Integration

Perfect integration with systemd journal for system services:

```python
from nicestlog.systemd_integration import SystemdLogger

# Automatic systemd journal integration
logger = SystemdLogger()
logger.info("service-started", service_name="my-app", pid=os.getpid())
```

## Web Dashboard

Real-time log monitoring with the built-in web dashboard:

```python
from nicestlog.web_dashboard import start_dashboard

# Start web dashboard on port 8080
start_dashboard(port=8080, log_level="INFO")
```

## Flask Integration

```python
from flask import Flask
from nicestlog import get_logger

app = Flask(__name__)
log = get_logger()

@app.before_request
def log_request():
    log.info("request-started", 
             method=request.method, 
             path=request.path)
```

## Django Integration

```python
# settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'nicestlog': {
            'class': 'nicestlog.DjangoHandler',
            'level': 'INFO',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['nicestlog'],
            'level': 'INFO',
        },
    },
}
```

## FastAPI Integration

```python
from fastapi import FastAPI
from nicestlog import get_logger

app = FastAPI()
log = get_logger()

@app.middleware("http")
async def log_requests(request, call_next):
    log.info("request-started", method=request.method, url=str(request.url))
    response = await call_next(request)
    log.info("request-completed", status_code=response.status_code)
    return response
```