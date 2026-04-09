# Eliot Integration Module

:::{admonition} Test Coverage: 80.5%
:class: tip

This module has high test coverage and is well-documented.
:::

The `stogger.eliot_integration` module combines Eliot's powerful action tracking with stogger's beautiful output, providing human-readable action traces instead of raw JSON.

## Quick Start

```python
import stogger

# Setup Eliot with beautiful output
stogger.setup_eliot_logging(human_readable=True)

# Use Eliot actions
with stogger_eliot.log_action("user_request", user_id=123):
    # Nested actions
    with stogger_eliot.log_action("database_query", table="users"):
        pass
```

## setup_eliot_logging

Configure Eliot logging with stogger's beautiful formatting.

```python
import stogger

success = stogger.setup_eliot_logging(
    destination=None,       # Write to stdout (default)
    human_readable=True,    # Beautiful colored output
    show_timestamps=True,   # Include timestamps
    show_task_ids=False,    # Show Eliot task IDs
)
```

Returns `True` if Eliot was successfully configured, `False` if not available.

### JSON Mode

For machine-readable output, disable human-readable mode:

```python
stogger.setup_eliot_logging(human_readable=False)
```

## HumanReadableEliotDestination

The main destination class that formats Eliot messages with colors and indentation.

```python
from stogger_eliot import HumanReadableEliotDestination

dest = HumanReadableEliotDestination(
    file=sys.stdout,          # Output stream
    show_timestamps=True,     # Include timestamps
    show_task_ids=False,      # Show task IDs for debugging
    max_width=120,            # Maximum line width
)
```

### Output Format

```
▶ user_request                  user_id=123 endpoint='/api/data'
  ▶ database_query              table='users' query='SELECT * FROM users'
  ✓ database_query
  ▶ cache_lookup                key='user:123'
  ✓ cache_lookup                ttl=300
  • request_received            method='GET'
  • response_sent               status_code=200 size_bytes=1024
✓ user_request
```

### Color Coding

- **Blue arrow** (▶): Action start
- **Green check** (✓): Successful completion
- **Red cross** (✗): Failed action
- **Yellow dot** (•): Regular log message within an action

## Decorators and Context Managers

### log_action

Context manager for logging Eliot actions with stogger formatting.

```python
from stogger_eliot import log_action

with log_action("process_order", order_id=456):
    # Your code here
    # Action is automatically marked as succeeded or failed
    pass
```

### log_call

Decorator to log function calls as Eliot actions.

```python
from stogger_eliot import log_call

@log_call("process_user_data")
def process_user(user_id: int):
    # Result is automatically added as success field
    return {"name": "Alice"}

# Or specify a custom action name
@log_call()
def fetch_data():
    # Uses "module.function_name" as action type
    pass
```

## Graceful Degradation

When Eliot is not installed, all functions degrade gracefully:

- `setup_eliot_logging()` returns `False`
- `log_action()` returns a no-op context manager
- `log_call()` returns the original function unchanged

## Installation

Eliot is an optional dependency:

```bash
pip install stogger[eliot]
```

## API Reference

```{autoapi} stogger.eliot_integration
:members:
```
