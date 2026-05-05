---
lifecycle:
  requirements:
    completed_at: "2026-05-04T15:00:00Z"
    git_rev: "d3e20c9"
  design:
    completed_at: "2026-05-04T15:30:00Z"
    git_rev: "d3e20c9"
  implement:
    completed_at: "2026-05-04T19:00:00Z"
    git_rev: "ef5c723"
  workflow:
    completed_at: "2026-05-04T19:00:00Z"
    git_rev: "ef5c723"
  verify:
---

# postgres-target

## Context

Stogger logs to console, file, and systemd journal but has no database target. PostgreSQL as a logging target makes logs queryable, analysable, and persistent — especially useful for services already running PostgreSQL. The new target follows the established external-package pattern (mirroring stogger-systemd) to keep the core dependency-free.

## Decisions

### package-placement

#### Context

PostgreSQL requires a heavy native dependency. Stogger core is deliberately free of I/O-heavy dependencies. The stogger-systemd package establishes the precedent: external package as workspace member, discovered at runtime via dynamic import.

#### Decision

External package `stogger-postgres` as workspace member under `packages/`. The renderer (`PostgresRenderer`) lives in core stogger (like `SystemdJournalRenderer`). The logger/factory (`PostgresLogger`, `PostgresLoggerFactory`) lives in the external package.

#### Alternatives

a. Built into stogger core — forces all users to install psycopg
b. Optional extra behind `[postgres]` — breaks with established pattern

#### Consequences

Clean separation. Core stays light. Users who want PostgreSQL install `stogger-postgres`. Runtime dynamic import mirrors journal pattern exactly.

### postgres-driver

#### Context

The sync-per-event write pattern is decided (see `write-pattern`). The driver must support synchronous writes, have a pure-Python fallback for environments without a C compiler, and be actively maintained.

#### Decision

psycopg v3 (psycopg). Modern API, pure-Python fallback via `psycopg[pure]`, pipeline mode for future batched writes, `COPY` support for bulk operations. Declared as dependency in `packages/stogger-postgres/pyproject.toml`.

#### Alternatives

a. psycopg2 — legacy, C-extension only, difficult on some platforms
b. pg8000 — pure-Python but less widely adopted, fewer features

#### Consequences

Standard modern choice. Pure-Python fallback ensures installability everywhere. Pipeline mode available if write-pattern evolves to batched.

### schema-columns

#### Context

Events have known high-cardinality fields (timestamp, level, event, func, scope) plus arbitrary user-defined fields. The schema must balance query performance on known fields with flexibility for unknown fields.

#### Decision

Fixed columns for high-query-volume fields + JSONB catch-all:

| Column | Type | Source |
|---|---|---|
| `id` | BIGSERIAL PRIMARY KEY | auto |
| `timestamp` | TIMESTAMPTZ NOT NULL | event_dict `timestamp` |
| `level` | TEXT NOT NULL | event_dict `level` |
| `event` | TEXT NOT NULL | event_dict `event` |
| `func` | TEXT | event_dict `func` (from decorators) |
| `scope` | TEXT | event_dict `scope` (from log_scope) |
| `data` | JSONB NOT NULL DEFAULT '{}' | all remaining event_dict fields |

Indexes: `timestamp` (DESC), `level`, `event`. GIN index on `data`.

#### Alternatives

a. Minimal (id, timestamp, level, event + JSONB) — func/scope require JSONB queries
b. Fully configurable schema — no out-of-the-box experience

#### Consequences

Common query dimensions are real columns with indexes. func and scope as separate columns enable efficient filtering by decorated function or scope name. Arbitrary fields remain queryable via JSONB.

### data-pipeline

#### Context

The renderer transforms event_dict for the target. The logger performs I/O. This separation is established by SystemdJournalRenderer (transforms to journal fields) → JournalLogger.msg(dict) (calls journal.send).

#### Decision

`PostgresRenderer` (in core stogger) extracts known fields into column dict, packs remaining fields into JSONB `data`, returns `{"postgres": column_dict}`. `PostgresLogger.msg(column_dict)` (in external package) executes the INSERT. `DummyPostgresLogger` is the no-op fallback.

Renderer responsibility: field extraction, column mapping, JSONB packing.
Logger responsibility: connection management, schema creation, INSERT execution.

#### Alternatives

a. Raw pass-through — logger does transformation + INSERT, renderer is dummy. Violates renderer/logger separation.
b. SQL string — renderer produces INSERT statement. Couples renderer to table schema directly.

#### Consequences

Consistent with established structlog patterns. Renderer is testable without database. Logger is thin I/O layer.

### connection-config

#### Context

Users must configure the database connection. Socket/peer authentication is common (no password needed). When passwords are needed, they must not be committed to version control.

#### Decision

DSN in `pyproject.toml` under `[tool.stogger]` key `postgres_dsn`. Password optional via `STOGGER_POSTGRES_PASSWORD` environment variable. Placeholder `%PASSWORD%` in DSN is replaced at runtime. Socket auth: DSN without placeholder works directly (e.g. `postgresql://stogger:@/logs?host=/var/run/postgresql`).

Config keys added to `StoggerConfig`:
- `enable_postgres: bool = False`
- `postgres_dsn: str | None = None`
- `postgres_table: str = "stogger_logs"`

#### Alternatives

a. Full DSN from environment variable only — works but DSN must be entirely in ENV
b. Separate config keys per connection parameter — more config overhead

#### Consequences

DSN can be safely versioned. Password never in code. Socket auth has zero extra complexity.

### error-strategy

#### Context

Logging must not crash the application. If a target fails, other targets continue.

#### Decision

Silent fallback at every failure point: connection failure, schema creation failure, INSERT failure. Each logs a warning to stderr (not to structlog — avoids recursive logging). Target is skipped, other targets continue. Mirrors the journal fallback pattern in `_build_logger_factories()`.

#### Alternatives

a. Buffer and retry — memory leak risk during extended outages
b. Fail hard — crashes application when database is down

#### Consequences

Robust under database outages. Users see warnings, logs flow to working targets.

### schema-creation

#### Context

The table must exist before INSERTs. Users should not need manual DDL steps.

#### Decision

`CREATE TABLE IF NOT EXISTS` executed in `PostgresLoggerFactory.__call__()` — once per logger instantiation, at startup. If creation fails, `DummyPostgresLogger` is returned (no-op fallback).

#### Alternatives

a. Lazy creation on first INSERT — delays error detection
b. Explicit setup function — worse DX, user must remember to call it

#### Consequences

Table is guaranteed to exist before any INSERT. Errors surface immediately at startup. No manual setup required.

### write-pattern

#### Context

Logging happens in the hot path. The target must not noticeably slow down the application.

#### Decision

Synchronous INSERT per event. Each `PostgresLogger.msg(dict)` executes one INSERT and returns. Overhead ~1-2ms per event.

#### Alternatives

a. Batched writes — higher throughput but more complex, delayed delivery
b. Async background writer — highest throughput but most complex

#### Consequences

Low latency per event. Predictable behaviour. For very high volume (>1000 events/s), batched writes may be needed in future.

### test-strategy

#### Context

Tests must cover the target without requiring a running PostgreSQL instance in CI. The stogger-systemd package establishes the test pattern.

#### Decision

Mirror the systemd test pattern:

1. **Mock-based integration tests** (in stogger core): 4-path decision matrix testing `enable_postgres` × import success × env var presence. Uses `patch.dict(sys.modules, ...)` to mock `stogger_postgres`.

2. **Real-package tests** (in `packages/stogger-postgres/`): guarded by `pytest.importorskip("stogger_postgres")` and `@pytest.mark.integration`. Tests `get_postgres_logger_factory()`, `PostgresLoggerFactory.__call__()`, `DummyPostgresLogger.msg()`.

3. **Spec validation tests**: in `tests/impl_spec/test_postgres_target.py` with xfail markers. Test import paths, config keys, renderer contract, schema creation flow.

#### Alternatives

a. Spec validation tests only — less confidence
b. No automated tests — unacceptable for new target

#### Consequences

Full coverage of the registration flow without PostgreSQL in CI. Real-package tests available for local development with a running database.

## Requirements

### Interface Contracts

**pyproject.toml configuration:**
```toml
[tool.stogger]
enable_postgres = true
postgres_dsn = "postgresql://stogger:%PASSWORD%@db.example.com:5432/logs"
# socket auth: "postgresql://stogger:@/logs?host=/var/run/postgresql"
postgres_table = "stogger_logs"  # optional
```

**Environment variables:**
```
STOGGER_POSTGRES_PASSWORD=mysecret   # replaces %PASSWORD% in DSN
```

### Files to Create

- `packages/stogger-postgres/pyproject.toml` — workspace member, depends on stogger + psycopg
- `packages/stogger-postgres/src/stogger_postgres/__init__.py` — PostgresLogger, DummyPostgresLogger, PostgresLoggerFactory, get_postgres_logger_factory()

### Files to Modify

- `src/stogger/config.py` — add enable_postgres, postgres_dsn, postgres_table to StoggerConfig
- `src/stogger/core.py` — add PostgresRenderer, update _build_logger_factories(), update MultiRenderer constructor

### Test Files

- `tests/test_postgres_integration.py` — mock-based 4-path matrix (mirrors test_systemd_integration.py)
- `tests/test_postgres_integration_real.py` — real-package tests (mirrors test_systemd_integration_real.py)
- `tests/impl_spec/test_postgres_target.py` — spec validation tests with xfail markers
