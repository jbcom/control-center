"""Common test fixtures for lifecyclelogging tests.

This module provides shared fixtures for use across multiple test modules.
"""

from __future__ import annotations

import pytest

from lifecyclelogging import Logging


@pytest.fixture
def logger() -> Logging:
    """Create a logger instance for testing with outputs disabled.

    Returns:
        Logging: A logger instance with console and file outputs disabled.
    """
    return Logging(enable_console=False, enable_file=False)
