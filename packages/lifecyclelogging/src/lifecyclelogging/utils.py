"""Utility helpers for LifecycleLogging internals."""

from __future__ import annotations

import logging

from collections.abc import Mapping, Sequence
from copy import copy, deepcopy
from typing import Any

from extended_data_types import make_raw_data_export_safe, wrap_raw_data_for_export

from .const import DEFAULT_LOG_LEVEL


def get_log_level(level: int | str) -> int:
    """Converts a log level from string or integer to a logging level integer.

    Args:
        level (int | str): The log level as a string or integer.

    Returns:
        int: The corresponding logging level integer.
    """
    if isinstance(level, str):
        try:
            return {
                "CRITICAL": logging.CRITICAL,
                "ERROR": logging.ERROR,
                "WARNING": logging.WARNING,
                "INFO": logging.INFO,
                "DEBUG": logging.DEBUG,
            }[level.upper()]
        except KeyError:
            return DEFAULT_LOG_LEVEL
    return level if isinstance(level, int) else DEFAULT_LOG_LEVEL


def get_loggers() -> list[logging.Logger]:
    """Retrieves all active loggers.

    Returns:
        list[logging.Logger]: A list of all active logger instances.
    """
    loggers = [logging.getLogger()]
    loggers.extend(logging.getLogger(name) for name in logging.root.manager.loggerDict)
    return loggers


def find_logger(name: str) -> logging.Logger | None:
    """Finds a logger by its name.

    Args:
        name (str): The name of the logger to find.

    Returns:
        logging.Logger | None: The logger instance if found, otherwise None.
    """
    for logger in get_loggers():
        if logger.name == name:
            return logger
    return None


def clear_existing_handlers(logger: logging.Logger) -> None:
    """Removes all existing handlers from the logger.

    Args:
        logger (logging.Logger): The logger from which to remove handlers.
    """
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()


def sanitize_json_data(data: Any) -> Any:
    """Sanitize data for JSON serialization using extended-data-types utilities.

    This function leverages `make_raw_data_export_safe` from extended-data-types
    to recursively convert complex types to export-safe primitives, including
    datetime objects, Path objects, and handling of large numbers.

    Args:
        data: The data to sanitize.

    Returns:
        Any: The sanitized data suitable for JSON serialization.
    """
    # Use extended-data-types' make_raw_data_export_safe for comprehensive handling
    # This handles datetime, Path, large numbers, and more
    return make_raw_data_export_safe(data, export_to_yaml=False)


def add_labeled_json(
    msg: str,
    labeled_data: Mapping[str, Mapping[str, Any]],
) -> str:
    """Add labeled JSON data to the message.

    Args:
        msg: The base message to append data to.
        labeled_data: The labeled JSON data to append.

    Returns:
        str: The message with appended labeled JSON data.
    """
    for label, data in deepcopy(labeled_data).items():
        if not isinstance(data, Mapping):
            mapped_data = {label: data}
            msg += "\n:" + wrap_raw_data_for_export(
                sanitize_json_data(mapped_data),
                allow_encoding=True,
            )
            continue

        msg += f"\n{label}:\n" + wrap_raw_data_for_export(
            sanitize_json_data(data),
            allow_encoding=True,
        )
    return msg


def add_unlabeled_json(
    msg: str,
    json_data: Mapping[str, Any] | Sequence[Mapping[str, Any]],
) -> str:
    """Add unlabeled JSON data to the message.

    Args:
        msg (str): The base message to append data to.
        json_data (Mapping[str, Any] | Sequence[Mapping[str, Any]]): The JSON data to append.

    Returns:
        str: The message with appended unlabeled JSON data.
    """
    unlabeled_json_data = (
        deepcopy(json_data) if isinstance(json_data, Sequence) else [copy(json_data)]
    )

    for jd in unlabeled_json_data:
        msg += "\n:" + wrap_raw_data_for_export(
            sanitize_json_data(jd),
            allow_encoding=True,
        )
    return msg


def add_json_data(
    msg: str,
    json_data: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None,
    labeled_json_data: Mapping[str, Mapping[str, Any]] | None,
) -> str:
    """Add JSON data to the log message.

    Args:
        msg (str): The base message to append data to.
        json_data (Mapping[str, Any] | Sequence[Mapping[str, Any]] | None): The JSON data to append.
        labeled_json_data (Mapping[str, Mapping[str, Any]] | None): The labeled JSON data to append.

    Returns:
        str: The message with appended JSON data.
    """
    if labeled_json_data:
        msg = add_labeled_json(msg, labeled_json_data)

    if json_data:
        msg = add_unlabeled_json(msg, json_data)

    return msg
