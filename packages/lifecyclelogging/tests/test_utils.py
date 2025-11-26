"""Unit tests for utility functions in the lifecyclelogging package."""

from __future__ import annotations

import logging

from typing import Any

import pytest

from lifecyclelogging.utils import (
    clear_existing_handlers,
    find_logger,
    get_log_level,
    get_loggers,
    sanitize_json_data,
)


def test_get_log_level() -> None:
    """Test log level conversion utility function.

    This test verifies that log levels are correctly converted from strings
    or integers to logging level integers.
    """
    assert get_log_level("DEBUG") == logging.DEBUG
    assert get_log_level("info") == logging.INFO
    assert get_log_level(logging.WARNING) == logging.WARNING
    assert get_log_level("INVALID") == logging.DEBUG  # Default


def test_get_loggers() -> None:
    """Test retrieving all active loggers.

    This test verifies that all active logger instances are retrieved.
    """
    loggers = get_loggers()
    assert len(loggers) > 0
    assert all(isinstance(logger, logging.Logger) for logger in loggers)


def test_find_logger() -> None:
    """Test finding a logger by name.

    This test verifies that a logger can be found by its name and that
    non-existent loggers return None.
    """
    test_logger = logging.getLogger("test_find")
    found_logger = find_logger("test_find")
    assert found_logger is test_logger
    assert find_logger("nonexistent") is None


def test_clear_existing_handlers() -> None:
    """Test clearing all handlers from a logger.

    This test verifies that all handlers are removed from a logger.
    """
    logger = logging.getLogger("test_clear")
    logger.addHandler(logging.NullHandler())
    assert len(logger.handlers) > 0

    clear_existing_handlers(logger)
    assert len(logger.handlers) == 0


@pytest.mark.parametrize(
    ("input_data", "expected"),
    [
        (123, 123),
        (2**60, 2**60),  # Large ints are preserved (valid in YAML/Python)
        ({"key": 123}, {"key": 123}),
        ({"key": 2**60}, {"key": 2**60}),
        ([1, 2**60, "test"], [1, 2**60, "test"]),
        (complex(1, 2), complex(1, 2)),  # Complex numbers preserved
    ],
)
def test_sanitize_json_data(input_data: Any, expected: Any) -> None:
    """Test JSON data sanitization utility function.

    This test verifies that data is correctly sanitized for export.
    Note: make_raw_data_export_safe preserves Python types that are valid
    in YAML (like large ints and complex numbers) rather than stringifying them.
    """
    assert sanitize_json_data(input_data) == expected
