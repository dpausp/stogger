# Systemd Journal Integration

stogger sends structured log events to the systemd journal when running under systemd. This avoids duplicate timestamps and level indicators that appear when console output is captured by the journal.

## When You Need This

Any Python service that runs as a systemd unit benefits from journal integration:

- Console output in systemd gets prefixed with journal metadata (timestamp, unit name) — stogger's own formatting adds a second set, producing redundant headers in `journalctl`.
- The journal renderer writes native journal fields (`PRIORITY`, `SYSLOG_IDENTIFIER`, `CODE_LINE`) instead of formatted text lines.
- Console logging is automatically suppressed when `JOURNAL_STREAM` is detected.

## Installation

```bash
uv add stogger-systemd
```

`stogger-systemd` pulls in `systemd-python` (Linux-only) and declares `stogger` as a dependency. No code changes required — `init_logging()` discovers the package at runtime.

## Configuration

Settings live in `[tool.stogger]` in `pyproject.toml`:

```toml
[tool.stogger]
systemd = "auto"                     # auto | required | off
systemd_facility = 128               # optional: syslog facility code (default: LOG_LOCAL0 = 128)
```

### systemd

Controls how `init_logging()` handles systemd journal integration.

| Value | Behavior |
|-------|----------|
| `"auto"` (default) | Try journal if available, silently fall back to no-op if not. |
| `"required"` | Journal must be available — raises `RuntimeError` at init if missing. |
| `"off"` | Skip journal registration entirely. No import attempt. |

Also configurable via `init_logging(systemd=SystemdMode.AUTO)` or `STOGGER_SYSTEMD=auto` env var.

### systemd_facility

Syslog facility code passed to `SystemdJournalRenderer`. Maps to `syslog.LOG_LOCALn` constants.

- `null` / unset (default) — uses `LOG_LOCAL0` (128).
- Integer value — passed through to the renderer unchanged.

Most services never need to change this. It matters only when filtering journal output by facility.

## How It Works

`init_logging()` follows this sequence:

1. Build the loggers dict (file, console).
2. Suppress console output when `JOURNAL_STREAM` env var is set (systemd sets this for every service).
3. If `systemd` mode is `"auto"` or `"required"`, attempt `from stogger.systemd import get_journal_logger_factory`.
4. If `systemd` mode is `"required"` and journal is unavailable, raise `RuntimeError`.
5. Configure structlog with all available targets.

### Fallback Behavior

| Condition | Behavior |
|-----------|----------|
| `systemd = "auto"`, journal available | Journal + file. Console suppressed when `JOURNAL_STREAM` set. |
| `systemd = "auto"`, no journal | Silent fallback to no-op. Console + file active. |
| `systemd = "required"`, journal available | Journal + file. Console suppressed when `JOURNAL_STREAM` set. |
| `systemd = "required"`, no journal | `RuntimeError` raised at init. |
| `systemd = "off"` | No journal integration. Console + file active. |

No configuration produces errors or warnings in non-systemd environments.

## Journal Fields

`SystemdJournalRenderer` transforms each event into journal-native fields:

| Field | Source |
|-------|--------|
| `PRIORITY` | Mapped from log level (`info` → 6, `warning` → 4, `error` → 3, etc.) |
| `SYSLOG_IDENTIFIER` | `syslog_identifier` from config (default: `"stogger"`) |
| `SYSLOG_FACILITY` | `systemd_facility` from config (default: 128) |
| `CODE_LINE` | Source file and line number |
| `MESSAGE` | Event ID + formatted `_replace_msg` or key-value pairs |
| All event keys | Uppercased (e.g. `USER_ID=123`, `ACTION="login"`) |

## Querying with journalctl

```bash
# All logs from your service
journalctl -u myapp.service

# Filter by syslog identifier
journalctl -t myapp

# Errors only
journalctl -t myapp -p err

# Specific event by ID
journalctl -t myapp MESSAGE="user-login*"

# Structured field query
journalctl -t myapp USER_ID=123

# Follow live output
journalctl -u myapp.service -f

# Since a specific time
journalctl -u myapp.service --since "1 hour ago"
```

## systemd Unit Example

```ini
[Unit]
Description=My Application
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/myapp
SyslogIdentifier=myapp
StandardOutput=journal
StandardError=journal

# Let stogger detect journal via JOURNAL_STREAM
# No special configuration needed

[Install]
WantedBy=multi-user.target
```

The `SyslogIdentifier` in the unit file and `syslog_identifier` in `[tool.stogger]` should match. This ensures consistent filtering with `journalctl -t`.

## NixOS Example

For NixOS deployments, the service definition fits into the system configuration:

```nix
systemd.services.myapp = {
  wantedBy = [ "multi-user.target" ];
  after = [ "network.target" ];
  serviceConfig = {
    ExecStart = "${pkgs.myapp}/bin/myapp";
    SyslogIdentifier = "myapp";
    StandardOutput = "journal";
    StandardError = "journal";
  };
};
```

## Troubleshooting

### Duplicate entries in journalctl

Console logging is not suppressed. This happens when `JOURNAL_STREAM` is not set in the service environment. Verify with:

```bash
systemctl show myapp.service -p Environment
```

Under normal systemd operation, `JOURNAL_STREAM` is always present.

### "stogger-systemd not available" message

The package is not installed. Add it to your dependencies:

```bash
uv add stogger-systemd
```

### Journal fields are empty or missing

Check that `systemd` is not set to `"off"` in `[tool.stogger]`. The default is `"auto"`, so this only applies if explicitly disabled.

### systemd-python fails to install

`systemd-python` requires libsystemd headers. On NixOS this is handled automatically. On other distributions:

```bash
# Debian/Ubuntu
apt install libsystemd-dev

# Fedora
dnf install systemd-devel
```
