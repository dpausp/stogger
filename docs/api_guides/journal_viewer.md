# Journal Viewer Module

:::{admonition} Test Coverage: 86.2%
:class: tip

This module has high test coverage and is well-documented.
:::

The `nicestlog.journal_viewer` module provides a beautiful systemd journal viewer that makes `journalctl` actually usable, with the same colored output style as nicestlog console logging.

## Quick Start

```python
from nicestlog.journal_viewer import JournalViewer, JournalQueryOptions

viewer = JournalViewer(show_pid=True, show_service=True)

# Query last 50 entries
for entry in viewer.query_journal(JournalQueryOptions(lines=50)):
    print(viewer.format_entry(entry))

# Filter by service
for entry in viewer.query_journal(
    JournalQueryOptions(service="myapp.service", lines=100)
):
    print(viewer.format_entry(entry))
```

## JournalViewer

The main class for viewing systemd journal entries with beautiful formatting.

```python
from nicestlog.journal_viewer import JournalViewer

viewer = JournalViewer(
    show_hostname=False,  # Show hostname in output
    show_pid=True,        # Show process ID
    show_service=True,    # Show service/identifier
    max_width=120,        # Maximum line width
)
```

### query_journal

Query the systemd journal and yield structured entries.

```python
# Using JournalQueryOptions (recommended)
from nicestlog.journal_viewer import JournalQueryOptions

for entry in viewer.query_journal(JournalQueryOptions(
    service="myapp.service",
    since="1 hour ago",
    level="error",
    lines=50,
    follow=False,
)):
    print(entry.message)
    print(entry.fields)
```

### format_entry

Format a journal entry with colors and alignment.

```python
entry = viewer.parse_journal_entry(raw_journal_dict)
formatted = viewer.format_entry(entry)
print(formatted)
```

### parse_journal_entry

Parse a raw systemd journal entry into a structured `JournalEntry` dataclass.

```python
entry = viewer.parse_journal_entry({
    "__REALTIME_TIMESTAMP": timestamp,
    "MESSAGE": "user-login",
    "SYSLOG_IDENTIFIER": "myapp",
    "_PID": "12345",
    "PRIORITY": 6,
    "NICESTLOG_user_id": "42",
})
```

## JournalQueryOptions

Options for journal queries.

```python
from nicestlog.journal_viewer import JournalQueryOptions

options = JournalQueryOptions(
    service="myapp.service",   # Filter by service
    since="1 hour ago",        # Start time
    until=None,                # End time
    level="info",              # Minimum log level
    lines=50,                  # Maximum entries
    follow=False,              # Follow new entries (like tail -f)
)
```

### Time Format Support

The `since` and `until` fields support multiple time formats:

- Relative: `"1 hour ago"`, `"30 minutes ago"`, `"2 days ago"`
- Absolute: `"2025-01-15 10:30:00"`, `"2025-01-15T10:30"`
- Keywords: `"today"`, `"yesterday"`

## JournalEntry

Structured representation of a parsed journal entry.

```python
@dataclass
class JournalEntry:
    timestamp: datetime
    hostname: str
    service: str
    pid: str
    level: str          # "critical", "error", "warning", "info", "debug"
    message: str
    fields: dict[str, Any]   # NICESTLOG_* fields
    raw_entry: dict[str, Any]
```

## CLI Usage

The journal viewer also provides a standalone CLI:

```bash
# View logs for a service
nicestlog tools journal -u myapp.service -n 50

# Filter by level
nicestlog tools journal --since '1 hour ago' --level error

# Follow mode
nicestlog tools journal -f -u myapp.service

# JSON output
nicestlog tools journal --json
```

## Priority Mapping

| Priority | Level |
|----------|-------|
| 0-2 | critical |
| 3 | error |
| 4 | warning |
| 5-6 | info |
| 7 | debug |

## API Reference

```{autoapi} nicestlog.journal_viewer
:members:
```
