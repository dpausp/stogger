"""stogger-postgres — PostgreSQL I/O for stogger."""

from __future__ import annotations

import os
import sys


class PostgresLogger:
    """Write log messages to PostgreSQL via INSERT."""

    def __init__(self, conn, table: str) -> None:
        self.conn = conn
        self.table = table

    def msg(self, column_dict: dict) -> None:
        # SPEC: postgres-target::error-strategy — INSERT failure prints warning to stderr, silently continues
        from psycopg import sql  # noqa: PLC0415  # type: ignore[unresolved-import]

        try:
            columns = column_dict.keys()
            placeholders = ", ".join(["%s"] * len(columns))
            query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                sql.Identifier(self.table),
                sql.SQL(", ").join(sql.Identifier(c) for c in columns),
                sql.SQL(placeholders),
            )
            with self.conn.cursor() as cur:
                cur.execute(query, list(column_dict.values()))
            self.conn.commit()
        except Exception:  # noqa: BLE001
            print(f"stogger-postgres: INSERT failed into {self.table}", file=sys.stderr)  # noqa: T201


class DummyPostgresLogger:
    """No-op PostgreSQL logger for when the database is unavailable."""

    def msg(self, column_dict: dict) -> None:
        pass


class PostgresLoggerFactory:
    """Creates PostgresLogger or DummyPostgresLogger based on connection availability."""

    def __init__(self, dsn: str, table: str = "stogger_logs") -> None:
        self.dsn = dsn
        self.table = table

    def __call__(self):
        # SPEC: postgres-target::connection-config — %PASSWORD% replaced with STOGGER_POSTGRES_PASSWORD env var
        resolved_dsn = self.dsn
        if "%PASSWORD%" in resolved_dsn:
            resolved_dsn = resolved_dsn.replace("%PASSWORD%", os.environ.get("STOGGER_POSTGRES_PASSWORD", ""))

        # SPEC: postgres-target::error-strategy — any exception returns DummyPostgresLogger
        try:
            import psycopg  # noqa: PLC0415  # type: ignore[unresolved-import]
            from psycopg import sql  # noqa: PLC0415  # type: ignore[unresolved-import]

            conn = psycopg.connect(resolved_dsn)
        except Exception:  # noqa: BLE001
            print(  # noqa: T201
                f"stogger-postgres: connection failed for {self.table}",
                file=sys.stderr,
            )
            return DummyPostgresLogger()

        # SPEC: postgres-target::schema-creation — CREATE TABLE IF NOT EXISTS at startup
        try:
            table_ident = sql.Identifier(self.table)
            create_table = sql.SQL(
                "CREATE TABLE IF NOT EXISTS {} ("
                "  id BIGSERIAL PRIMARY KEY,"
                "  timestamp TIMESTAMPTZ NOT NULL,"
                "  level TEXT NOT NULL,"
                "  event TEXT NOT NULL,"
                "  func TEXT,"
                "  scope TEXT,"
                "  data JSONB NOT NULL DEFAULT '{{}}'"
                ")"
            ).format(table_ident)
            idx_timestamp = sql.SQL("CREATE INDEX IF NOT EXISTS {} ON {} (timestamp DESC)").format(
                sql.Identifier(f"idx_{self.table}_timestamp"), table_ident
            )
            idx_level = sql.SQL("CREATE INDEX IF NOT EXISTS {} ON {} (level)").format(
                sql.Identifier(f"idx_{self.table}_level"), table_ident
            )
            idx_event = sql.SQL("CREATE INDEX IF NOT EXISTS {} ON {} (event)").format(
                sql.Identifier(f"idx_{self.table}_event"), table_ident
            )
            idx_data = sql.SQL("CREATE INDEX IF NOT EXISTS {} ON {} USING GIN (data)").format(
                sql.Identifier(f"idx_{self.table}_data"), table_ident
            )

            with conn.cursor() as cur:
                cur.execute(create_table)
                cur.execute(idx_timestamp)
                cur.execute(idx_level)
                cur.execute(idx_event)
                cur.execute(idx_data)
            conn.commit()
        except Exception:  # noqa: BLE001
            print(  # noqa: T201
                f"stogger-postgres: schema creation failed for {self.table}",
                file=sys.stderr,
            )
            return DummyPostgresLogger()

        return PostgresLogger(conn, self.table)


def get_postgres_logger_factory(dsn: str, table: str = "stogger_logs") -> PostgresLoggerFactory:
    """Return a PostgresLoggerFactory instance."""
    return PostgresLoggerFactory(dsn, table)
