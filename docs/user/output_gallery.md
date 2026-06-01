# Output Gallery

What stogger output looks like in the terminal.
All examples use `stogger.init_logging(verbose=True)` unless noted.
Colors are described in the legend below — the terminal renders them automatically.

## Color Legend

| Element | Color | Style |
|---------|-------|-------|
| Timestamp | Default | Dim |
| Level D, I | Green | Bright |
| Level W | Yellow | Bright |
| Level E, C | Red | Bright |
| Event name | Default | Bright, right-padded to 30 chars |
| Keys (no `_replace_msg`) | Cyan | Normal |
| Values (no `_replace_msg`) | Magenta | Normal |
| Output blocks (`>`, `err:`, etc.) | Default | Dim |
| Raw ANSI tool output | Preserved | As-is |

## Log Levels with `_replace_msg`

```text
2026-06-01T17:19:01Z D cache-lookup                   Cache hit for key user:123
2026-06-01T17:19:01Z I user-login                     User alice logged in from 192.168.1.1
2026-06-01T17:19:01Z W rate-limit-approaching         Rate limit approaching for user 123
2026-06-01T17:19:01Z E payment-gateway-timeout        Payment gateway stripe timed out after 5000ms
2026-06-01T17:19:01Z C database-unavailable           Database unavailable after 3 attempts
```

Format: dimmed ISO timestamp, colored level letter, bright-padded event name, then the formatted `_replace_msg` text.

## Raw KV Pairs (no `_replace_msg`)

```text
2026-06-01T17:19:01Z I order-created                  amount=99.99 currency='USD' customer_id=67890 order_id=12345
2026-06-01T17:19:01Z W disk-usage-high                free_gb=12.3 mount='/var' usage_percent=87
2026-06-01T17:19:01Z E api-response-failed            endpoint='/api/orders' status_code=503 upstream='payment-service'
```

Without `_replace_msg`, keys render as cyan and values as magenta, sorted alphabetically.

## Output Keys in Action

See [Logging Patterns](logging_patterns.md) for when to use each output key.

### `cmd_output_line` — Single command line

```text
2026-06-01T17:19:01Z I deploy-command                 cmd_output_line='rsync -avz ./dist/ server:/var/www/'
> rsync -avz ./dist/ server:/var/www/
```

Dimmed `>` prefix. Use for logging a command before execution.

### `_output` — Multi-line block

```text
2026-06-01T17:19:01Z I diff-result                    _output='--- a/file.py\n+++ b/file.py\n@@ ...'

--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
 import os
+import sys
 import json
```

Plain multi-line block (no prefix). Use for diffs, file content, structured text.

### `_raw_output` — Preserved ANSI colors

```text
2026-06-01T17:19:01Z W component-type-errors          ty: 3 type error(s)
ty: error: import unknown module
ty: error: type mismatch
ty: error: unresolved reference
```

Tool output with its ANSI colors preserved. `_raw_output_prefix` sets the block label (`ty:` here).

### `stderr` — Error output

```text
2026-06-01T17:19:01Z E build-failed                   Build failed for myapp
err: 
err: SyntaxError: invalid syntax
err:   File "main.py", line 42
err:
```

Dimmed `err:` prefix per line. Use for subprocess stderr or error streams.

## Decorator Output

```text
2026-06-01T17:19:01Z D called                         func='myapp.process_data' x=21
2026-06-01T17:19:01Z D returned                       duration_ms=0.042 func='myapp.process_data' result='hello world'
2026-06-01T17:19:01Z D operation                      a=3 b=7 duration_ms=0.055 func='myapp.add' result=10
```

All decorators emit debug-level events with `func=`, positional args, `result`, and `duration_ms`.
See [Reference](reference.md) for decorator API details.

## Non-Verbose Mode

```text
2026-06-01T17:19:01Z I this-should-be-visible         Only info and above in non-verbose mode
2026-06-01T17:19:01Z W rate-limit-warning             Rate limit at 90%
```

With `verbose=False` (the default), only I/W/E/C pass — debug is filtered.

## Exception Logging

```text
2026-06-01T17:19:01Z E operation-failed               Operation failed: something went wrong
```

`log.exception()` renders the same as error. The traceback context is captured in the event dict.

## JSON Format

With `log_format="json"`, the console renderer stays the same on TTY — JSON applies to file output:

```json
{
  "event": "user-login",
  "timestamp": "2026-06-01T17:19:01Z",
  "level": "info",
  "_replace_msg": "User alice logged in from 192.168.1.1",
  "user_id": 123,
  "username": "alice",
  "ip": "192.168.1.1"
}
```

## Timestamp Formats

Configure via `timestamp_format` in `[tool.stogger]` or `init_logging()`:

```text
2026-06-01T17:19:01.123456Z    iso            (full ISO 8601 with microseconds)
2026-06-01T17:19:01Z           iso_seconds    (default, no sub-second precision)
2026-06-01T17:19:01            iso_no_z       (no Z suffix)
+12.456                        relative       (seconds since process start)
```
