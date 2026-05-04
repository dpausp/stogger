# PostgreSQL Integration

stogger sends structured log events to a PostgreSQL table, making logs queryable with
SQL without additional infrastructure. Events are stored with typed columns for common
query dimensions and a JSONB catch-all for arbitrary fields.

## When You Need This

Services that already run PostgreSQL and want log persistence without setting up a
dedicated log aggregation stack:

- Logs become rows you can `SELECT`, `JOIN`, and aggregate with standard SQL.
- The JSONB `data` column keeps all structured fields queryable without schema
  migrations.
- Works alongside console, file, and journal targets — PostgreSQL is just another
  output.

## Installation

```bash
uv add stogger-postgres
```

`stogger-postgres` pulls in `psycopg` v3 (pure-Python fallback available) and declares
`stogger` as a dependency. No code changes required — `init_logging()` discovers the
package at runtime.

## Configuration

Settings live in `[tool.stogger]` in `pyproject.toml`:

```toml
[tool.stogger]
enable_postgres = true
postgres_dsn = "postgresql://stogger:%PASSWORD%@db.example.com:5432/logs"
# socket auth: "postgresql://stogger:@/logs?host=/var/run/postgresql"
postgres_table = "stogger_logs"  # optional
```

### enable_postgres

Controls whether `init_logging()` attempts to register the PostgreSQL target.

- `true` — import `stogger-postgres` and register the database logger.
- `false` (default) — skip PostgreSQL registration entirely. No import attempt.

### postgres_dsn

Connection string passed to psycopg. Supports any valid PostgreSQL DSN.

- The `%PASSWORD%` placeholder is replaced at runtime with the value of
  `STOGGER_POSTGRES_PASSWORD`.
- For socket/peer authentication, omit the placeholder:
  `postgresql://stogger:@/logs?host=/var/run/postgresql`.
- Password must not be committed to version control — use the environment variable.

### postgres_table

Table name for log events.

- Default: `"stogger_logs"`.
- The table is created automatically at startup if it does not exist.

## How It Works

`init_logging()` follows this sequence:

1. Build the loggers dict (file, console).
2. If `enable_postgres` is `true`, attempt
   `from stogger_postgres import get_postgres_logger_factory`.
3. On `ImportError` (package not installed), log a one-time info message and continue
   without PostgreSQL.
4. The factory creates the table via `CREATE TABLE IF NOT EXISTS`, then returns a
   `PostgresLogger`.
5. Each log event triggers one synchronous INSERT.

### Fallback Behavior

| Condition | Behavior |
| --- | --- |
| `stogger-postgres` installed, `enable_postgres = true` | PostgreSQL + console + file. |
| `stogger-postgres` installed, `enable_postgres = false` | PostgreSQL skipped. Console + file active. |
| `stogger-postgres` not installed, `enable_postgres = true` | Info message logged. Console + file active. |
| Connection fails at startup | Warning to stderr. `DummyPostgresLogger` used (no-op). Console + file active. |
| INSERT fails at runtime | Warning to stderr. Event dropped. Other targets continue. |

No configuration produces crashes in any environment. Database failures produce
warnings, not exceptions.

## Table Schema

`PostgresRenderer` extracts known fields into typed columns and packs everything else
into the JSONB `data` column:

| Column | Type | Source |
| --- | --- | --- |
| `id` | BIGSERIAL PRIMARY KEY | auto |
| `timestamp` | TIMESTAMPTZ NOT NULL | event_dict `timestamp` |
| `level` | TEXT NOT NULL | event_dict `level` |
| `event` | TEXT NOT NULL | event_dict `event` |
| `func` | TEXT | event_dict `func` (from decorators) |
| `scope` | TEXT | event_dict `scope` (from `log_scope`) |
| `data` | JSONB NOT NULL DEFAULT `'{}'` | all remaining event_dict fields |

Indexes: `timestamp` (DESC), `level`, `event`. GIN index on `data`.

Common query dimensions (`timestamp`, `level`, `event`, `func`, `scope`) are real
columns with indexes. Arbitrary structured fields remain queryable via `data`.

## Querying with SQL

```sql
-- Recent errors
SELECT timestamp, event, data
FROM stogger_logs
WHERE level = 'error'
ORDER BY timestamp DESC
LIMIT 50;

-- Events from a specific function
SELECT timestamp, event, data
FROM stogger_logs
WHERE func = 'process_payment';

-- Structured field in JSONB
SELECT timestamp, event, data->>'user_id' AS user_id
FROM stogger_logs
WHERE data->>'user_id' = '123';

-- Event counts by type, last 24 hours
SELECT event, count(*)
FROM stogger_logs
WHERE timestamp > now() - interval '24 hours'
GROUP BY event
ORDER BY count(*) DESC;

-- Logs within a scope
SELECT timestamp, level, event
FROM stogger_logs
WHERE scope = 'order-processing'
ORDER BY timestamp DESC;
```

## Troubleshooting

### "stogger-postgres not available" message

The package is not installed. Add it to your dependencies:

```bash
uv add stogger-postgres
```

### Connection refused / timeout

Verify the DSN is correct and the PostgreSQL server is reachable:

```bash
psql "postgresql://stogger:@/logs?host=/var/run/postgresql"
```

Socket authentication requires the PostgreSQL socket path to match. Check
`unix_socket_directories` in `postgresql.conf`.

### Table not created automatically

Schema creation runs once at startup. If it fails (permissions, invalid DSN), a warning
is logged to stderr and the `DummyPostgresLogger` is used. Check stderr output from your
service for the warning message.

### %PASSWORD% not replaced

The `STOGGER_POSTGRES_PASSWORD` environment variable must be set in the service
environment. For systemd units:

```ini
[Service]
Environment="STOGGER_POSTGRES_PASSWORD=mysecret"
```

For NixOS:

```nix
systemd.services.myapp.environment.STOGGER_POSTGRES_PASSWORD = "mysecret";
```

Or use a secrets management solution — never commit the password to version control.
