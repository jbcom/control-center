"""Pytest configuration and fixtures for vendor_connectors tests."""

from unittest.mock import MagicMock

import pytest
from lifecyclelogging import Logging


@pytest.fixture
def mock_logger():
    """Provide a mock Logging instance for testing."""
    logging = MagicMock(spec=Logging)
    logging.logger = MagicMock()
    return logging


@pytest.fixture
def base_connector_kwargs(mock_logger):
    """Provide common kwargs for all connectors."""
    return {
        "logger": mock_logger,
        "from_environment": False,
    }
