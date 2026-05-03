"""Shared test fixtures for stogger tests."""

import pytest
import structlog


@pytest.fixture(autouse=True)
def _reset_structlog():
    """Reset structlog configuration after each test to avoid state leakage."""
    yield
    structlog.reset_defaults()
