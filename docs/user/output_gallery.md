# Output Gallery

What stogger output looks like in the terminal.
All examples use `stogger.init_logging(verbose=True)` unless noted.

## Log Levels with `_replace_msg`

Five log levels, each with a human-readable `_replace_msg`:

```{eval-rst}
.. erbsland-ansi::
   :escape-char: §

   §[2m2026-06-01T17:19:01Z§[0m §[32m§[1mD§[0m §[1mcache-lookup                  §[0m Cache hit for key user:123
   §[2m2026-06-01T17:19:01Z§[0m §[32m§[1mI§[0m §[1muser-login                    §[0m User alice logged in from 192.168.1.1
   §[2m2026-06-01T17:19:01Z§[0m §[33m§[1mW§[0m §[1mrate-limit-approaching        §[0m Rate limit approaching for user 123
   §[2m2026-06-01T17:19:01Z§[0m §[31m§[1mE§[0m §[1mpayment-gateway-timeout       §[0m Payment gateway stripe timed out after 5000ms
   §[2m2026-06-01T17:19:01Z§[0m §[31m§[1mC§[0m §[1mdatabase-unavailable          §[0m Database unavailable after 3 attempts
```

Dimmed ISO timestamp, colored level letter (green D/I, yellow W, red E/C), bright-padded event name, then the formatted `_replace_msg` text.

## Raw KV Pairs (no `_replace_msg`)

Without `_replace_msg`, remaining fields render as `key=value` pairs — cyan keys, magenta values, sorted alphabetically:

```{eval-rst}
.. erbsland-ansi::
   :escape-char: §

   §[2m2026-06-01T17:19:01Z§[0m §[32m§[1mI§[0m §[1morder-created                 §[0m §[36mamount§[0m=§[35m99.99§[0m §[36mcurrency§[0m=§[35m'USD'§[0m §[36mcustomer_id§[0m=§[35m67890§[0m §[36morder_id§[0m=§[35m12345§[0m
   §[2m2026-06-01T17:19:01Z§[0m §[33m§[1mW§[0m §[1mdisk-usage-high               §[0m §[36mfree_gb§[0m=§[35m12.3§[0m §[36mmount§[0m=§[35m'/var'§[0m §[36musage_percent§[0m=§[35m87§[0m
   §[2m2026-06-01T17:19:01Z§[0m §[31m§[1mE§[0m §[1mapi-response-failed           §[0m §[36mendpoint§[0m=§[35m'/api/orders'§[0m §[36mstatus_code§[0m=§[35m503§[0m §[36mupstream§[0m=§[35m'payment-service'§[0m
```

## Output Keys in Action

See [Logging Patterns](logging_patterns.md) for when to use each output key.

### `cmd_output_line` — Single command line

Dimmed `>` prefix. Use for logging a command before execution:

```{eval-rst}
.. erbsland-ansi::
   :escape-char: §

   §[2m2026-06-01T17:19:01Z§[0m §[32m§[1mI§[0m §[1mdeploy-command                §[0m §[2m> rsync -avz ./dist/ server:/var/www/§[0m
```

### `_output` — Multi-line block

Plain multi-line block (no prefix). Use for diffs, file content, structured text:

```{eval-rst}
.. erbsland-ansi::
   :escape-char: §

   §[2m2026-06-01T17:19:01Z§[0m §[32m§[1mI§[0m §[1mdiff-result                   §[0m
   --- a/file.py
   +++ b/file.py
   @@ -1,3 +1,4 @@
    import os
   +import sys
    import json
```

### `_raw_output` — Preserved ANSI colors

Tool output with its ANSI colors preserved. `_raw_output_prefix` sets the block label (`ty:` here):

```{eval-rst}
.. erbsland-ansi::
   :escape-char: §

   §[2m2026-06-01T17:19:01Z§[0m §[33m§[1mW§[0m §[1mcomponent-type-errors         §[0m ty: 3 type error(s)
   ty: §[31merror:§[0m import unknown module
   ty: §[31merror:§[0m type mismatch
   ty: §[31merror:§[0m unresolved reference
```

### `stderr` — Error output

Dimmed `err:` prefix per line. Use for subprocess stderr or error streams:

```{eval-rst}
.. erbsland-ansi::
   :escape-char: §

   §[2m2026-06-01T17:19:01Z§[0m §[31m§[1mE§[0m §[1mbuild-failed                  §[0m Build failed for myapp
   §[2merr:§[0m
   §[2merr: SyntaxError: invalid syntax§[0m
   §[2merr:   File "main.py", line 42§[0m
```

## Decorator Output

All decorators emit debug-level events with `func=`, positional args, `result`, and `duration_ms`.
See [Reference](reference.md) for decorator API details.

```{eval-rst}
.. erbsland-ansi::
   :escape-char: §

   §[2m2026-06-01T17:19:01Z§[0m §[32m§[1mD§[0m §[1mcalled                        §[0m §[36mfunc§[0m=§[35m'myapp.process_data'§[0m §[36mx§[0m=§[35m21§[0m
   §[2m2026-06-01T17:19:01Z§[0m §[32m§[1mD§[0m §[1mreturned                      §[0m §[36mduration_ms§[0m=§[35m0.042§[0m §[36mfunc§[0m=§[35m'myapp.process_data'§[0m §[36mresult§[0m=§[35m'hello world'§[0m
   §[2m2026-06-01T17:19:01Z§[0m §[32m§[1mD§[0m §[1moperation                     §[0m §[36ma§[0m=§[35m3§[0m §[36mb§[0m=§[35m7§[0m §[36mduration_ms§[0m=§[35m0.055§[0m §[36mfunc§[0m=§[35m'myapp.add'§[0m §[36mresult§[0m=§[35m10§[0m
```

## Non-Verbose Mode

With `verbose=False` (the default), only I/W/E/C pass — debug is filtered:

```{eval-rst}
.. erbsland-ansi::
   :escape-char: §

   §[2m2026-06-01T17:19:01Z§[0m §[32m§[1mI§[0m §[1mthis-should-be-visible        §[0m Only info and above in non-verbose mode
   §[2m2026-06-01T17:19:01Z§[0m §[33m§[1mW§[0m §[1mrate-limit-warning            §[0m Rate limit at 90%
```

## Exception Logging

`log.exception()` renders the same as error. The traceback context is captured in the event dict:

```{eval-rst}
.. erbsland-ansi::
   :escape-char: §

   §[2m2026-06-01T17:19:01Z§[0m §[31m§[1mE§[0m §[1moperation-failed              §[0m Operation failed: something went wrong
```

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

Configure via `[tool.stogger.format]` or `init_logging()`:

```text
2026-06-01T17:19:01.123456Z    iso            (full ISO 8601 with microseconds)
2026-06-01T17:19:01Z           iso_seconds    (default, no sub-second precision)
2026-06-01T17:19:01            iso_no_z       (no Z suffix)
+12.456                        relative       (seconds since process start)
```
