# Testing with stogger

How to test log output in projects that use stogger.

## Setup

Add `pytest-structlog` as a dev dependency:

```bash
uv add --dev pytest-structlog
```

No configuration needed — `pytest-structlog` auto-discovers structlog and
provides a `log` fixture that captures all structlog events.

## Unit Tests

Use the `log` fixture (type: `StructuredLogCapture`) to assert on captured events:

```python
from pytest_structlog import StructuredLogCapture

import stogger
import structlog

stogger.init_logging()
log_module = structlog.get_logger()


def process_order(order_id: int):
    log_module.info("order-processed", _replace_msg="Order {order_id} done", order_id=order_id)
    log_module.debug("order-details", items=3, total_cents=9900)


def test_process_order(log: StructuredLogCapture):
    process_order(42)

    # Assert specific event exists
    assert log.has("order-processed", order_id=42, level="info")

    # Assert debug context
    assert log.has("order-details", items=3)

    # Assert full event list
    assert log.events == [
        log.info("order-processed", order_id=42),
        log.debug("order-details", items=3, total_cents=9900),
    ]

    # Count occurrences
    assert log.count("order-processed") == 1
```

### Assertion Patterns

- **`log.has(event_name, **context)`** — check a single event with optional context
- **`log.events`** — full list of captured event dicts for exact matching
- **`log.count(event_name)`** — number of times an event was logged
- **`log.events >= [expected]`** — ordered subset match (checks subset, preserves order)

```python
# Subset match: only check the events you care about
assert log.events >= [
    {"event": "order-processed", "level": "info"},
    {"event": "order-shipped", "level": "info"},
]

# Negation: event was NOT logged with this context
assert not log.has("order-processed", order_id=999)
```

## CLI / Integration Tests with Typer CliRunner

The `log` fixture captures events directly from the structlog pipeline.
This works regardless of where stogger renders output (stderr, file,
journal). No special configuration needed.

```python
from typer.testing import CliRunner
from pytest_structlog import StructuredLogCapture

from myapp.cli import app

runner = CliRunner()


def test_deploy_command(log: StructuredLogCapture):
    result = runner.invoke(app, ["deploy", "myapp", "--env", "staging"])

    assert result.exit_code == 0
    assert log.has("deployment-started", package="myapp", env="staging")
    assert log.has("deployment-completed")
```

Two kinds of assertions, two tools:

- **Structured assertions**: `log.has("event-id")` — verify the right events
  were emitted with the right context
- **User-visible output**: `result.output` — check rendered text that the
  user would see (CliRunner captures stderr too)

## _replace_msg Assertions

`_replace_msg` is a processor concern — it transforms the event dict for
display. In tests, assert on the raw structured data, not the rendered string:

```python
def test_user_greeting(log: StructuredLogCapture):
    log_module.info("welcome", _replace_msg="Welcome {username}!", username="alice")

    # Assert on the event name and structured data
    assert log.has("welcome", username="alice")

    # _replace_msg appears in the event dict if you need it
    assert log.has("welcome", _replace_msg="Welcome {username}!", username="alice")
```

## When to Use log_to_stdlib

The `log_to_stdlib` processor bridges structlog events to Python's `logging`
module. This is useful **only** for:

- Legacy code that reads from stdlib `logging` handlers
- Ad-hoc debugging with `logging.basicConfig()`

Do **not** add `log_to_stdlib` to your pipeline just to use `pytest caplog`.
Instead, use `pytest-structlog` which captures events directly — no bridge
needed, no duplicate output.

```{note}
`log_to_stdlib` is documented in the API reference for `stogger.core`. It is
intentionally not part of the default pipeline. Adding it causes every event
to appear twice.
```

## Anti-Patterns

- **Don't reconfigure structlog in test conftests.** Replacing stogger's
  pipeline with a custom processor defeats the purpose of a shared logging
  library. The `log` fixture captures events without touching the pipeline.
- **Don't import `PartialFormatter` or other internals from `stogger.core`.**
  If you need `_replace_msg` formatting in tests, assert on the raw event
  data with `log.has()` instead of re-rendering templates yourself.
- **Don't build custom capture processors.** `pytest-structlog` already
  provides event capture. Adding a second capture mechanism creates
  maintenance burden and diverges from the project's logging conventions.
- **Don't use `caplog` or `log_to_stdlib`** — `pytest-structlog` is the
  right tool for structlog-based projects.


