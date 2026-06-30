"""Real integration tests for stogger-systemd (requires installed package)."""

import pytest

_ = pytest.importorskip("stogger_systemd")

from stogger_systemd import (
    DummyJournalLogger,
    JournalLogger,
    JournalLoggerFactory,
    get_journal_logger_factory,
)


@pytest.mark.integration
def test_get_journal_logger_factory_returns_factory():
    """get_journal_logger_factory returns a JournalLoggerFactory instance."""
    factory = get_journal_logger_factory()
    assert isinstance(factory, JournalLoggerFactory)


@pytest.mark.integration
def test_journal_logger_factory_creates_logger():
    """JournalLoggerFactory creates a logger with a msg method."""
    factory = get_journal_logger_factory()
    logger = factory()
    assert hasattr(logger, "msg")
    assert isinstance(logger, (JournalLogger, DummyJournalLogger))


@pytest.mark.integration
def test_dummy_journal_logger_msg_noop():
    """DummyJournalLogger.msg is a no-op that does not raise."""
    logger = DummyJournalLogger()
    logger.msg({"MESSAGE": "test"})  # Should not raise
