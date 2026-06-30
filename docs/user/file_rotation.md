# File Rotation

For long-running applications — daemons, resident CLIs, services, desktop apps that
stay alive for days — the default `{syslog_identifier}.log` file in `logdir` grows
unbounded. stogger's file rotation caps the file at a configurable size and keeps a
fixed number of rotated backups.

## When You Need This

- **Daemons and services** running for days or weeks without restart
- **Memory-snapshot logging** or any other high-volume structured logging that would
  produce gigabytes of log data
- **Single-process applications** that own their log files (multi-process setups should
  use the [systemd journal](systemd.md) or [PostgreSQL](postgres.md) targets instead —
  file rotation is not multi-process safe)

## Configuration

Settings live in `[tool.stogger]` in `pyproject.toml`:

```toml
[tool.stogger]
logdir = "~/.local/state/myapp"
syslog_identifier = "myapp"
log_rotation = "size"          # "size" | "none" (default: "none")
log_max_bytes = 10_000_000     # rotate when file would exceed this (default: 10 MB)
log_backup_count = 5           # number of backups: base.log.1 through base.log.N
```

### log_rotation

Selects the rotation mode.

- `"none"` (default) — no rotation; file grows unbounded. Current behavior.
- `"size"` — rotate when the next write would push file size strictly above
  `log_max_bytes`.

Any other value raises `ValueError` at `init_logging()` time. Fail loudly so typos
surface immediately, not as silent unbounded growth later.

### log_max_bytes

Size threshold in bytes for `log_rotation = "size"`. Default `10_000_000` (10 MB).

A file holding exactly `log_max_bytes` is still valid — rotation only fires when the
next write would push the size strictly above this value. This avoids spurious rotation
on the first write of exactly `max_bytes` length.

### log_backup_count

Number of rotated backup files to keep. Default `5`.

Naming follows stdlib `logging.handlers.RotatingFileHandler`:

```
myapp.log          # current file (live writes go here)
myapp.log.1        # most recent backup
myapp.log.2
myapp.log.3
myapp.log.4
myapp.log.5        # oldest backup — gets dropped on next rotation
```

On each rotation:

1. Existing backups shift: `.N → .(N+1)` (oldest is overwritten)
2. Current file is renamed to `.1`
3. A fresh `myapp.log` is opened and the triggering write lands there

`backup_count = 0` disables rotation entirely — same as `log_rotation = "none"`. Useful
when you want a bounded single-file slot but no backup history.

## Python API

All three settings can also be passed directly to `init_logging()`:

```python
import stogger

stogger.init_logging(
    logdir="~/.local/state/myapp",
    syslog_identifier="myapp",
    log_rotation="size",
    log_max_bytes=10_000_000,
    log_backup_count=5,
)
```

Priority: **environment > kwargs > pyproject.toml**. Same as all other stogger settings.

## Environment Variables

| Variable | Config Key | Type |
|----------|-----------|------|
| `STOGGER_LOG_ROTATION` | `log_rotation` | str (`"size"` or `"none"`) |
| `STOGGER_LOG_MAX_BYTES` | `log_max_bytes` | int |
| `STOGGER_LOG_BACKUP_COUNT` | `log_backup_count` | int |

Non-int values for the int vars are silently ignored (the config default applies) and
logged at debug level for diagnosis.

## Example

Voice-focused-desktop daemon with 7-day retention, rotating at 10 MB:

```toml
[tool.stogger]
logdir = "~/.local/state/vfd"
syslog_identifier = "vfd"
log_rotation = "size"
log_max_bytes = 10_000_000
log_backup_count = 7
```

After a week of heavy logging:

```
~/.local/state/vfd/
├── vfd.log
├── vfd.log.1
├── vfd.log.2
├── vfd.log.3
├── vfd.log.4
├── vfd.log.5
├── vfd.log.6
└── vfd.log.7
```

Total disk usage bounded at `log_max_bytes * (log_backup_count + 1)` = 80 MB.

## Interaction with External Rotation

If you use `logrotate(8)` or another external rotation tool, leave
`log_rotation = "none"` (the default). External rotation relies on the logging process
detecting inode changes (which `RotatingFileWriter` does not do — stogger opens the file
in append mode once and writes to the same handle for the process lifetime). Running
both will conflict: external rotation renames `myapp.log` to `myapp.log.1`, but stogger
keeps writing to the original (now-renamed) file descriptor.

## What's Deliberately Not Supported

See ADR [rotating-file-logging](../dev/adr/rotating-file-logging.md) for the full
rationale. Summary:

- **Timed rotation** (`when=midnight`, hourly, etc.) — separate axis with its own design
  questions. Use external `logrotate(8)` if you need it now.
- **Compression** of backup files — adds CPU cost on rollover and naming complexity.
  Apply compression externally if needed.
- **Multi-process file locking** — stogger targets single-process apps. Multi-process
  deployment should use journald or PostgreSQL targets.
