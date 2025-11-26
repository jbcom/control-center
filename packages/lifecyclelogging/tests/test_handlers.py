"""Tests for logging handlers in the lifecyclelogging package."""

from __future__ import annotations

import logging

import pytest

from lifecyclelogging.handlers import add_console_handler, add_file_handler


def test_add_file_handler() -> None:
    """Test adding a file handler to a logger.

    This test verifies that a file handler is correctly added to a logger
    and that invalid file names raise an error.
    """
    logger = logging.getLogger("test_file")
    log_file = "test_file.log"

    with pytest.raises(RuntimeError, match="must contain at least one ASCII character"):
        add_file_handler(logger, "!@#$%^")

    add_file_handler(logger, log_file)
    assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)


def test_add_console_handler() -> None:
    """Test adding a console handler to a logger.

    This test verifies that a console handler is correctly added to a logger.
    """
    logger = logging.getLogger("test_console")
    add_console_handler(logger)
    assert len(logger.handlers) == 1
    assert logger.handlers[0].formatter is not None
