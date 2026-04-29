# stogger

Multi-target structured logging built on [structlog](https://www.structlog.org/).

## Quick start

```python
import stogger
import structlog

stogger.init_logging(verbose=True)
log = structlog.get_logger()
log.info("user-login", _replace_msg="User {user_id} logged in", user_id=123)
```

## Testing

Use [pytest-stogger](https://github.com/stogger/pytest-stogger) for structured log assertions in tests:

```python
def test_login_logs_user(log):
    do_login(user_id=123)
    log.has("info", "user-login", user_id=123)
```

See `docs/user_guide/testing.md` for details.

## Documentation

Full docs at `docs/` — build with:

    uv run sphinx-build -b html docs docs/_build/html

Then open `docs/_build/html/index.html`.

LLM-friendly: `docs/_build/html/llms-full.txt`

## License

AGPL-3.0
