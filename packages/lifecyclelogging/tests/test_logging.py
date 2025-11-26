"""Unit tests for the Logging class in the lifecyclelogging package."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from lifecyclelogging import Logging
from lifecyclelogging.log_types import LogLevel


def test_logger_initialization() -> None:
    """Test logger initialization with specific settings.

    This test verifies that a logger is initialized with the correct settings
    and that console output can be enabled.
    """
    logger = Logging(enable_console=True)
    assert logger.enable_console is True
    assert logger.logger is not None


def test_basic_logging(logger: Logging) -> None:
    """Test basic message logging without any markers or verbosity.

    This test verifies that a basic message is logged correctly.
    """
    msg = "Test message"
    result = logger.logged_statement(msg, log_level="info")  # type: ignore[arg-type]
    assert result == msg


def test_json_logging(logger: Logging) -> None:
    """Test logging with attached JSON data.

    This test verifies that JSON data is correctly appended to log messages.
    """
    json_data: Mapping[str, Any] = {"key": "value"}
    msg = "JSON test"
    result = logger.logged_statement(msg, json_data=json_data, log_level="debug")  # type: ignore[arg-type]
    assert result is not None
    assert "key" in result
    assert "value" in result


def test_storage_marker(logger: Logging) -> None:
    """Test storing messages under specific markers.

    This test verifies that messages are stored under the correct storage markers.
    """
    msg = "Test message"
    storage_marker = "test_category"

    result = logger.logged_statement(
        msg,
        storage_marker=storage_marker,
        log_level="info",  # type: ignore[arg-type]
    )

    assert result == msg
    assert storage_marker in logger.stored_messages
    assert msg in logger.stored_messages[storage_marker]


def test_context_marker(logger: Logging) -> None:
    """Test message prefixing with context markers.

    This test verifies that messages are correctly prefixed with context markers.
    """
    msg = "Test message"
    context_marker = "test_context"

    result = logger.logged_statement(
        msg,
        context_marker=context_marker,
        log_level="info",  # type: ignore[arg-type]
    )

    assert result == f"[{context_marker}] {msg}"


def test_verbosity_bypass(logger: Logging) -> None:
    """Test that verbosity bypass markers override verbosity settings.

    This test verifies that messages with verbosity bypass markers are logged
    regardless of verbosity settings.
    """
    msg = "Should appear despite verbosity"
    context_marker = "bypass_test"
    logger.register_verbosity_bypass_marker(context_marker)

    # Even with verbose disabled and high verbosity, message should appear
    result = logger.logged_statement(
        msg,
        context_marker=context_marker,
        verbose=True,
        verbosity=5,
        log_level="debug",  # type: ignore[arg-type]
    )

    assert result is not None
    assert msg in result


def test_register_verbosity_bypass_marker(logger: Logging) -> None:
    """Ensure bypass markers are registered without duplication."""
    marker = "bypass"
    logger.register_verbosity_bypass_marker(marker)
    logger.register_verbosity_bypass_marker(marker)

    assert marker in logger.verbosity_bypass_markers
    # Sets inherently prevent duplicates, so count should be 1
    assert len([m for m in logger.verbosity_bypass_markers if m == marker]) == 1


def test_verbosity_control(logger: Logging) -> None:
    """Test verbosity control without bypass markers.

    This test verifies that messages are suppressed or logged based on verbosity
    settings and thresholds.
    """
    msg = "Test message"

    # Without enable_verbose_output, verbose messages should be suppressed
    result = logger.logged_statement(
        msg,
        verbose=True,
        verbosity=1,
        log_level="debug",  # type: ignore[arg-type]
    )
    assert result is None

    # Enable verbose output
    logger.enable_verbose_output = True
    logger.verbosity_threshold = 2

    # Now message within threshold should appear
    result = logger.logged_statement(
        msg,
        verbose=True,
        verbosity=2,
        log_level="debug",  # type: ignore[arg-type]
    )
    assert result == msg

    # But message above threshold should not
    result = logger.logged_statement(
        msg,
        verbose=True,
        verbosity=3,
        log_level="debug",  # type: ignore[arg-type]
    )
    assert result is None


def test_log_level_filtering(logger: Logging) -> None:
    """Test message filtering based on log levels.

    This test verifies that messages are stored or suppressed based on allowed
    and denied log levels.
    """
    msg = "Test message"
    storage_marker = "filter_test"

    # Test with allowed levels
    logger = Logging(
        enable_console=False,
        enable_file=False,
        allowed_levels=["info", "warning"],
        default_storage_marker=storage_marker,
    )

    # Allowed level should be stored
    logger.logged_statement(msg, log_level="info")  # type: ignore[arg-type]
    assert msg in logger.stored_messages[storage_marker]

    # Denied level should not be stored
    logger.logged_statement("Should not store", log_level="debug")  # type: ignore[arg-type]
    assert "Should not store" not in logger.stored_messages[storage_marker]


def test_log_level_normalization() -> None:
    """Ensure allowed and denied levels are normalized for filtering."""
    storage_marker = "normalized"
    logger = Logging(
        enable_console=False,
        enable_file=False,
        allowed_levels=["INFO"],
        denied_levels=["ERROR"],
        default_storage_marker=storage_marker,
    )

    logger.logged_statement("Allowed", log_level="info")  # type: ignore[arg-type]
    assert "Allowed" in logger.stored_messages[storage_marker]

    logger.logged_statement("Denied", log_level="error")  # type: ignore[arg-type]
    assert "Denied" not in logger.stored_messages[storage_marker]


@pytest.mark.parametrize(
    "log_level",
    ["debug", "info", "warning", "error", "fatal", "critical"],
)
def test_all_log_levels(logger: Logging, log_level: LogLevel) -> None:
    """Test logging at each available log level.

    This test verifies that messages are logged correctly at each log level
    and that warning-level messages are prefixed appropriately.
    """
    msg = f"Test message at {log_level} level"
    storage_marker = "level_test"

    result = logger.logged_statement(
        msg,
        storage_marker=storage_marker,
        log_level=log_level,
    )

    assert result == msg
    assert storage_marker in logger.stored_messages
    stored_msg = next(
        iter(m for m in logger.stored_messages[storage_marker] if msg in m)
    )

    # Check for warning prefix on appropriate levels
    if log_level not in ["debug", "info"]:
        assert stored_msg.startswith(":warning:")
    else:
        assert not stored_msg.startswith(":warning:")
