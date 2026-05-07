"""Shared test fixtures for stogger tests."""

import pytest
import structlog


@pytest.fixture(autouse=True)
def _reset_structlog():
    """Reset structlog configuration after each test to avoid state leakage."""
    yield
    structlog.reset_defaults()
    # Clear pending test-dep warnings to prevent atexit noise from test fakes
    from stogger.config import _PENDING_WARNINGS

    _PENDING_WARNINGS.clear()
