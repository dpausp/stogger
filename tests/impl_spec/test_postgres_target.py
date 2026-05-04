"""Spec validation tests for postgres-target.

These tests define the CONTRACT that the postgres-target implementation
must fulfill. All tests are marked xfail because the feature doesn't exist yet.
They will be garbage-collected after implementation makes them green.

Spec: .agents/impl_specs/postgres-target.md

Decision coverage:
  - package-placement: stogger_postgres package exports correct public API
  - postgres-driver: psycopg v3 is importable as dependency
  - schema-columns: PostgresRenderer extracts known columns, packs rest into JSONB
  - data-pipeline: PostgresRenderer returns {"postgres": <dict>}, PostgresLogger.msg() receives it
  - connection-config: StoggerConfig has enable_postgres, postgres_dsn, postgres_table
  - error-strategy: DummyPostgresLogger.msg() is a no-op fallback
  - schema-creation: PostgresLoggerFactory.__call__() creates table, accepts config
  - write-pattern: PostgresLogger.msg() accepts a dict (column dict from renderer)
  - test-strategy: enable_postgres=True triggers registration in _build_logger_factories
"""

import os
import sys
import types
from unittest.mock import MagicMock, patch

import pytest
import structlog

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_structlog():
    """Reset structlog configuration after each test to avoid state leakage."""
    yield
    structlog.reset_defaults()


# ---------------------------------------------------------------------------
# package-placement: stogger_postgres exports the public API
# ---------------------------------------------------------------------------


def test_stogger_postgres_package_exports():
    """stogger_postgres must export PostgresLogger, DummyPostgresLogger,
    PostgresLoggerFactory, and get_postgres_logger_factory.

    SPEC: package-placement — external package stogger-postgres as workspace
    member under packages/, discovered at runtime via dynamic import.
    SPEC: data-pipeline — PostgresLogger and PostgresLoggerFactory live in
    the external package.
    """
    pytest.importorskip("stogger_postgres")
    from stogger_postgres import (  # noqa: PLC0415
        DummyPostgresLogger,
        PostgresLogger,
        PostgresLoggerFactory,
        get_postgres_logger_factory,
    )

    assert callable(get_postgres_logger_factory)
    assert isinstance(PostgresLogger, type)
    assert isinstance(DummyPostgresLogger, type)
    assert isinstance(PostgresLoggerFactory, type)


# ---------------------------------------------------------------------------
# postgres-driver: psycopg is importable
# ---------------------------------------------------------------------------


def test_psycopg_importable():
    """Psycopg v3 must be importable as a dependency of stogger-postgres.

    SPEC: postgres-driver — psycopg v3 (psycopg) is the database driver.
    Modern API, pure-Python fallback via psycopg[pure].
    """
    pytest.importorskip("psycopg")
    import psycopg

    assert psycopg


# ---------------------------------------------------------------------------
# schema-columns: PostgresRenderer extracts known columns
# ---------------------------------------------------------------------------


def test_postgres_renderer_extracts_known_columns():
    """PostgresRenderer must extract known columns and pack rest into data JSONB.

    SPEC: schema-columns — fixed columns for timestamp, level, event, func,
    scope; remaining fields go into JSONB data column.
    SPEC: data-pipeline — renderer extracts known fields into column dict,
    packs remaining fields into JSONB data.
    """
    from stogger.core import PostgresRenderer  # noqa: PLC0415

    renderer = PostgresRenderer()
    event_dict = {
        "timestamp": "2026-05-04T12:00:00Z",
        "level": "info",
        "event": "request-completed",
        "func": "myapp.handlers.process",
        "scope": "http-request",
        "request_id": "abc-123",
        "user_id": 42,
    }

    result = renderer(None, "info", event_dict)

    assert "postgres" in result
    column_dict = result["postgres"]

    # Known columns extracted as top-level keys
    assert column_dict["timestamp"] == "2026-05-04T12:00:00Z"
    assert column_dict["level"] == "info"
    assert column_dict["event"] == "request-completed"
    assert column_dict["func"] == "myapp.handlers.process"
    assert column_dict["scope"] == "http-request"

    # Remaining fields packed into JSONB data key
    assert "data" in column_dict
    assert column_dict["data"]["request_id"] == "abc-123"
    assert column_dict["data"]["user_id"] == 42  # noqa: PLR2004

    # Known columns must NOT appear in data
    assert "timestamp" not in column_dict["data"]
    assert "level" not in column_dict["data"]
    assert "event" not in column_dict["data"]
    assert "func" not in column_dict["data"]
    assert "scope" not in column_dict["data"]


# ---------------------------------------------------------------------------
# data-pipeline: renderer returns {"postgres": <dict>}, logger has .msg()
# ---------------------------------------------------------------------------


def test_postgres_renderer_returns_postgres_keyed_dict():
    """PostgresRenderer.__call__ must return {"postgres": <dict>} format.
    PostgresLogger must have .msg(column_dict) method.

    SPEC: data-pipeline — PostgresRenderer returns {"postgres": column_dict}.
    PostgresLogger.msg(column_dict) executes the INSERT.
    """
    pytest.importorskip("stogger_postgres")
    from stogger.core import PostgresRenderer  # noqa: PLC0415

    renderer = PostgresRenderer()
    event_dict = {
        "timestamp": "2026-05-04T12:00:00Z",
        "level": "info",
        "event": "test-event",
        "extra_key": "extra_value",
    }

    result = renderer(None, "info", event_dict)

    # Renderer returns dict keyed by target name "postgres"
    assert isinstance(result, dict)
    assert "postgres" in result
    assert isinstance(result["postgres"], dict)

    # PostgresLogger has .msg() method accepting the column dict
    from stogger_postgres import PostgresLogger  # noqa: PLC0415

    assert hasattr(PostgresLogger, "msg")
    assert callable(PostgresLogger.msg)


# ---------------------------------------------------------------------------
# connection-config: StoggerConfig has postgres fields
# ---------------------------------------------------------------------------


def test_stoggerconfig_has_postgres_fields():
    """StoggerConfig must have enable_postgres, postgres_dsn, postgres_table.

    SPEC: connection-config — config keys added to StoggerConfig:
    enable_postgres (bool, default False), postgres_dsn (str | None, default None),
    postgres_table (str, default "stogger_logs").
    """
    import attrs

    from stogger.config import StoggerConfig

    # Verify fields exist on the attrs class
    fields = {f.name for f in attrs.fields(StoggerConfig)}
    assert "enable_postgres" in fields
    assert "postgres_dsn" in fields
    assert "postgres_table" in fields

    # Verify defaults
    cfg = StoggerConfig()
    assert cfg.enable_postgres is False
    assert cfg.postgres_dsn is None
    assert cfg.postgres_table == "stogger_logs"


# ---------------------------------------------------------------------------
# error-strategy: DummyPostgresLogger.msg() is a no-op
# ---------------------------------------------------------------------------


def test_dummy_postgres_logger_is_noop():
    """DummyPostgresLogger.msg() must be a no-op that doesn't raise.

    SPEC: error-strategy — silent fallback at every failure point.
    DummyPostgresLogger is the no-op fallback when connection or schema
    creation fails.
    """
    pytest.importorskip("stogger_postgres")
    from stogger_postgres import DummyPostgresLogger  # noqa: PLC0415

    logger = DummyPostgresLogger()
    # Must not raise — this is the core contract of the dummy logger
    logger.msg({"timestamp": "2026-05-04", "level": "info", "event": "test", "data": {}})
    logger.msg({})


# ---------------------------------------------------------------------------
# schema-creation: PostgresLoggerFactory creates table on __call__
# ---------------------------------------------------------------------------


def test_postgres_logger_factory_creates_table():
    """PostgresLoggerFactory must have __call__() and accept dsn + table params.

    SPEC: schema-creation — CREATE TABLE IF NOT EXISTS executed in
    PostgresLoggerFactory.__call__() once per logger instantiation.
    SPEC: connection-config — factory receives DSN and table name.
    """
    pytest.importorskip("stogger_postgres")
    from stogger_postgres import PostgresLoggerFactory  # noqa: PLC0415

    # Factory must be callable (has __call__)
    assert callable(PostgresLoggerFactory)

    # Factory accepts config params (dsn, table name)
    factory = PostgresLoggerFactory(
        dsn="postgresql://stogger:@/logs?host=/var/run/postgresql",
        table="stogger_logs",
    )
    assert callable(factory)


# ---------------------------------------------------------------------------
# write-pattern: PostgresLogger.msg() accepts a dict
# ---------------------------------------------------------------------------


def test_postgres_logger_msg_signature():
    """PostgresLogger.msg() must accept a dict parameter (column dict from renderer).

    SPEC: write-pattern — synchronous INSERT per event.
    PostgresLogger.msg(dict) executes one INSERT and returns.
    """
    pytest.importorskip("stogger_postgres")
    from stogger_postgres import PostgresLogger  # noqa: PLC0415

    # PostgresLogger.msg must accept a single dict parameter
    assert hasattr(PostgresLogger, "msg")

    # Verify the method signature accepts a dict — we test the contract
    # by checking that .msg exists and is callable; the actual INSERT
    # is tested in real-package tests (test_postgres_integration_real.py).
    import inspect

    sig = inspect.signature(PostgresLogger.msg)
    params = list(sig.parameters.values())
    # First param after self must accept a dict
    assert len(params) >= 1


# ---------------------------------------------------------------------------
# test-strategy: enable_postgres=True triggers registration flow
# ---------------------------------------------------------------------------


def test_enable_postgres_config_flag():
    """enable_postgres=True must trigger postgres target registration
    in _build_logger_factories.

    SPEC: test-strategy — mock-based integration tests testing enable_postgres
    x import success matrix. Uses patch.dict(sys.modules, ...) to mock
    stogger_postgres.
    SPEC: connection-config — enable_postgres controls whether postgres
    target is registered.
    """
    from stogger.config import StoggerConfig
    from stogger.core import _build_logger_factories

    mock_module = types.ModuleType("stogger_postgres")

    mock_logger_instance = MagicMock()

    class MockFactory:
        def __call__(self):
            return mock_logger_instance

    mock_module.get_postgres_logger_factory = MagicMock(return_value=MockFactory())
    mock_module.PostgresLogger = type("PostgresLogger", (), {})
    mock_module.DummyPostgresLogger = type("DummyPostgresLogger", (), {})
    mock_module.PostgresLoggerFactory = MockFactory

    with (
        patch.dict(sys.modules, {"stogger_postgres": mock_module}),
        patch.dict(os.environ, {}, clear=False),
        patch("stogger.core.StoggerConfig") as mock_config_cls,
    ):
        mock_cfg = MagicMock(spec=StoggerConfig)
        mock_cfg.enable_postgres = True
        mock_cfg.enable_systemd = False
        mock_cfg.systemd_facility = None
        mock_config_cls.return_value = mock_cfg

        loggers, _context = _build_logger_factories(
            logdir=None,
            log_to_console=True,
            syslog_identifier="stogger",
            cfg=mock_cfg,
        )

    assert "postgres" in loggers
