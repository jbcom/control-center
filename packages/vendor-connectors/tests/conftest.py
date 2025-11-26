"""Pytest configuration and fixtures for cloud_connectors tests."""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_logger():
    """Provide a mock logger for testing."""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.debug = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    return logger


@pytest.fixture
def base_connector_kwargs(mock_logger):
    """Provide common kwargs for all connectors."""
    return {
        "logger": mock_logger,
        "to_console": False,
        "to_file": False,
    }
