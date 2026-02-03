"""Pytest configuration and fixtures."""

import pytest

from terminalbot.config import Settings
from terminalbot.executor import CommandExecutor


@pytest.fixture
def test_settings():
    """Create test settings."""
    return Settings()


@pytest.fixture
def executor(test_settings):
    """Create command executor for testing."""
    return CommandExecutor(test_settings)
