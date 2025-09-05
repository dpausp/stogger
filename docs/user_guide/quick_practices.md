# TL;DR: Logging Cheatsheet

Short attention span edition. Do these things and your logs will be useful, consistent, and easy to analyze.

## The 80/20 Rules

- Use event-style messages (kebab-case) as the primary message
  - Examples: `"user-login"`, `"cache-miss"`, `"payment-failed"`
- Always log structured fields (no f-strings in the message)
  - Put data in fields; optionally add `_replace_msg` for a human sentence
- Pick the right level:
  - `debug` — internal operations, noisy details
  - `info` — business events and major milestones
  - `warning` — unusual but non-failing conditions
  - `error` — failures and handled exceptions
  - `critical` — system unusable or operator action required
- Include stable context fields:
  - Common: `user_id`, `request_id` or `correlation_id`, `operation`, `component`, `status_code`
- Measure time:
  - Prefer `duration_ms` for operations, or log `*-started` / `*-finished` pairs
- Never log secrets/PII:
  - Mask tokens, passwords, and personal data; enable PII scrubbing if available
- Keep the cardinality low (avoid unbounded label values)

## Exceptions — do this

- Inside `except`, prefer `log.exception(...)` — it automatically includes `exc_info=True` and adds the full traceback to the `exception` field. Kein `error=str(e)` nötig:

```python
try:
    do_work()
except Exception:
    log = structlog.get_logger()
    log.exception(
        "work-failed",
        operation="do_work",
    )
    # optionally: raise
```

- Alternative (wenn du aus bestimmten Gründen `log.error` verwenden willst):

```python
try:
    do_work()
except Exception as e:
    log.error(
        "work-failed",
        operation="do_work",
        exc_info=True,    # oder: exc_info=e
    )
```

- Warum wichtig: nicestlog verarbeitet `exc_info` und rendert einen vollständigen Traceback ins Feld `exception`. Ohne `exc_info` geht der Stacktrace verloren.
- Kein `exc_info` auf `info`/`debug` — zu laut und unnötig.

## Message formatting

- Use `_replace_msg` to add a readable sentence while keeping structure:

```python
log.info(
    "user-login",
    _replace_msg="User {username} logged in from {ip}",
    username=user.username,
    user_id=user.id,
    ip=request.remote_addr,
)
```

## Naming and consistency

- Prefer these field names (keep them consistent):
  - IDs: `user_id`, `request_id`, `correlation_id`
  - Timing: `duration_ms`
  - HTTP: `method`, `path`, `status_code`
  - Generic: `operation`, `component`

## Sampling and throttling

- Avoid chatty `info` logs in tight loops; use `debug`, sample, or aggregate
- Consider adding a `sample_rate` field to mark sampled events

## Do / Don’t

- Do:

```python
log.info("order-created", _replace_msg="Order {order_id} created for user {user_id}", order_id=oid, user_id=uid, total_cents=total)
```

- Don’t:

```python
log.info(f"order {oid} by user {uid} created with total {total}")
```

## FAQ

- Do we still need `exc_info=True`? Yes, if you want a stack trace. Use `log.exception(...)` (preferred) or pass `exc_info=True`/`exc_info=e` on error logs. Nicestlog’s processors will capture and format it into the `exception` field.
- Can I log plain strings? Technically yes, but you lose structure. Always prefer event name + fields.

See also: full guide in `user_guide/best_practices.md`.
