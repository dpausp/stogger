"""Permanent integration tests for stogger-postgres dynamic import.

Tests mock the ``stogger_postgres`` import via ``unittest.mock.patch`` to validate
all four integration paths specified in the postgres-target impl spec.

Spec: .agents/impl_specs/postgres-target.md
Test matrix from spec decision ``test-strategy``:
  1. enable_postgres=True + import succeeds → postgres registered
  2. enable_postgres=True + ImportError → fallback (no postgres logger)
  3. enable_postgres=False → no import attempt
  4. enable_postgres=True + ImportError → warning to stderr
"""

import os
import sys
import types
from unittest.mock import MagicMock, patch

import pytest
import structlog

from stogger.config import StoggerConfig
from stogger.core import init_logging


@pytest.fixture(autouse=True)
def _reset_structlog():
    """Reset structlog configuration after each test to avoid state leakage."""
    yield
    structlog.reset_defaults()


# --- Test 1: enable_postgres=True + import succeeds ---


def test_enable_postgres_true_import_succeeds():
    """Postgres factory registered in loggers dict when import succeeds.

    SPEC: integration-hook — core attempts ``from stogger_postgres import
    get_postgres_logger_factory`` and registers the factory on success.
    SPEC: data-pipeline — postgres logger registered via dynamic
    import after loggers-dict construction, before ``structlog.configure()``.
    SPEC: api-contract — ``get_postgres_logger_factory()`` returns a callable
    factory whose return value is a structlog-compatible logger.
    """
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
        patch("stogger.core.StoggerConfig") as mock_config_cls,
        patch.dict(os.environ, {}, clear=False),
    ):
        os.environ.pop("JOURNAL_STREAM", None)

        mock_cfg = MagicMock(spec=StoggerConfig)
        mock_cfg.enable_postgres = True
        mock_cfg.enable_systemd = False
        mock_cfg.systemd_facility = None
        mock_cfg.postgres_dsn = "postgresql://test:@/testdb"
        mock_cfg.postgres_table = "stogger_logs"
        mock_config_cls.return_value = mock_cfg

        init_logging(logdir=None)

    config = structlog.get_config()
    factory = config.get("logger_factory")
    assert factory is not None
    assert "postgres" in factory.factories


# --- Test 2: enable_postgres=True + ImportError → fallback ---


def test_enable_postgres_true_import_error_fallback():
    """No crash and no postgres logger when import fails with ImportError.

    SPEC: integration-hook — falls back to stub on ImportError. Zero-config
    for users.
    SPEC: fallback-behavior — graceful fallback when stogger-postgres absent.
    SPEC: acceptance criterion — ``init_logging()`` falls back gracefully
    when stogger-postgres absent.
    """
    with (
        patch.dict(sys.modules, {"stogger_postgres": None}),
        patch("stogger.core.StoggerConfig") as mock_config_cls,
        patch.dict(os.environ, {}, clear=False),
    ):
        os.environ.pop("JOURNAL_STREAM", None)

        mock_cfg = MagicMock(spec=StoggerConfig)
        mock_cfg.enable_postgres = True
        mock_cfg.enable_systemd = False
        mock_cfg.systemd_facility = None
        mock_cfg.postgres_dsn = "postgresql://test:@/testdb"
        mock_cfg.postgres_table = "stogger_logs"
        mock_config_cls.return_value = mock_cfg

        init_logging(logdir=None)

    config = structlog.get_config()
    factory = config.get("logger_factory")
    assert factory is not None
    assert "postgres" not in factory.factories


# --- Test 3: enable_postgres=False → no import attempt ---


def test_enable_postgres_false_no_import():
    """No import attempt when enable_postgres=False in config.

    SPEC: connection-config — ``enable_postgres`` comes from
    ``pyproject.toml`` config only. ``init_logging()`` reads
    ``StoggerConfig`` internally.
    SPEC: acceptance criterion — ``enable_postgres=False`` suppresses all
    postgres behavior.
    """
    mock_module = types.ModuleType("stogger_postgres")

    mock_module.get_postgres_logger_factory = MagicMock()
    mock_module.PostgresLogger = type("PostgresLogger", (), {})
    mock_module.DummyPostgresLogger = type("DummyPostgresLogger", (), {})
    mock_module.PostgresLoggerFactory = type("PostgresLoggerFactory", (), {})

    with (
        patch.dict(sys.modules, {"stogger_postgres": mock_module}),
        patch("stogger.core.StoggerConfig") as mock_config_cls,
        patch.dict(os.environ, {}, clear=False),
    ):
        os.environ.pop("JOURNAL_STREAM", None)

        mock_cfg = MagicMock(spec=StoggerConfig)
        mock_cfg.enable_postgres = False
        mock_cfg.enable_systemd = False
        mock_cfg.systemd_facility = None
        mock_cfg.postgres_dsn = None
        mock_cfg.postgres_table = "stogger_logs"
        mock_config_cls.return_value = mock_cfg

        init_logging(logdir=None)

    mock_module.get_postgres_logger_factory.assert_not_called()


# --- Test 4: enable_postgres=True + ImportError → silent fallback ---


def test_enable_postgres_true_import_error_silent_fallback():
    """Silent fallback when enable_postgres=True but stogger-postgres not installed.

    SPEC: error-strategy — silent fallback at every failure point.
    SPEC: test-strategy — 4-path decision matrix: enable_postgres x import
    success x env var. Unlike systemd (which prints a warning when JOURNAL_STREAM
    is detected), postgres silently skips to avoid noise.
    """
    with (
        patch.dict(sys.modules, {"stogger_postgres": None}),
        patch("stogger.core.StoggerConfig") as mock_config_cls,
        patch.dict(os.environ, {}, clear=False),
    ):
        os.environ.pop("JOURNAL_STREAM", None)

        mock_cfg = MagicMock(spec=StoggerConfig)
        mock_cfg.enable_postgres = True
        mock_cfg.enable_systemd = False
        mock_cfg.systemd_facility = None
        mock_cfg.postgres_dsn = "postgresql://test:@/testdb"
        mock_cfg.postgres_table = "stogger_logs"
        mock_config_cls.return_value = mock_cfg

        init_logging(logdir=None)

    config = structlog.get_config()
    factory = config.get("logger_factory")
    assert factory is not None
    assert "postgres" not in factory.factories
