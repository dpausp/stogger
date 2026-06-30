"""Real integration tests for stogger-postgres (requires installed package)."""

import pytest

_ = pytest.importorskip("stogger_postgres")

from stogger_postgres import (
    DummyPostgresLogger,
    PostgresLogger,
    PostgresLoggerFactory,
    get_postgres_logger_factory,
)


@pytest.mark.integration
def test_get_postgres_logger_factory_returns_factory():
    factory = get_postgres_logger_factory(
        dsn="postgresql://test:@/test?host=/var/run/postgresql",
        table="stogger_logs",
    )
    assert callable(factory)


@pytest.mark.integration
def test_postgres_logger_factory_creates_logger():
    # Without a real DB, factory should return DummyPostgresLogger on connection failure
    factory = PostgresLoggerFactory(
        dsn="postgresql://nonexistent:test@localhost:5432/nonexistent_db",
        table="test_logs",
    )
    logger = factory()
    assert hasattr(logger, "msg")


@pytest.mark.integration
def test_dummy_postgres_logger_msg_noop():
    logger = DummyPostgresLogger()
    logger.msg({"event": "test"})  # Should not raise
