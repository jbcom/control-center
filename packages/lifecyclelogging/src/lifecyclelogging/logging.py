"""Core logging functionality for flexible and configurable logging management.

This module provides a Logging class that supports advanced logging features including:
- Configurable console and file logging
- Message storage and filtering
- Verbosity control
- Context and storage marker systems

The module allows for fine-grained control over log message handling, storage,
and output across different logging contexts.
"""

from __future__ import annotations

import logging
import os

from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import (
    Any,
    cast,
)

from extended_data_types import get_unique_signature, strtobool

from .const import VERBOSITY
from .handlers import add_console_handler, add_file_handler
from .log_types import LogLevel
from .utils import add_json_data, clear_existing_handlers, find_logger, get_log_level


class Logging:
    """A class to manage logging configurations for console and file outputs.

    This class supports two types of message markers:
    1. Storage markers (log_marker): Used to categorize and store messages in collections
    2. Context markers (context_marker): Prepended to messages and can override verbosity

    The context marker system can also designate certain markers as "verbosity bypass markers"
    which will cause messages with those markers to ignore verbosity settings entirely.
    """

    def __init__(
        self,
        enable_console: bool = False,
        enable_file: bool = True,
        logger: logging.Logger | None = None,
        logger_name: str | None = None,
        log_file_name: str | None = None,
        default_storage_marker: str | None = None,
        allowed_levels: Sequence[str] | None = None,
        denied_levels: Sequence[str] | None = None,
        enable_verbose_output: bool = False,
        verbosity_threshold: int = VERBOSITY,
    ) -> None:
        """Initialize the Logging class with options for console and file logging.

        This class provides two types of message marking systems:
        1. Storage markers: Used to categorize and collect messages in storage
        2. Context markers: Used to prefix messages and control verbosity

        Args:
            enable_console: Whether to enable console output.
            enable_file: Whether to enable file output.
            logger: An existing logger instance to use.
            logger_name: The name for a new logger instance.
            log_file_name: The name of the log file if file logging enabled.
            default_storage_marker: Default marker for storing messages.
            allowed_levels: List of allowed log levels (if empty, all allowed).
            denied_levels: List of denied log levels.
            enable_verbose_output: Whether to allow verbose messages.
            verbosity_threshold: Maximum verbosity level (1-5) to display.

        The logger configured will have the following characteristics:
        - Non-propagating (won't pass messages to parent loggers)
        - Level set from LOG_LEVEL env var or DEBUG if not set
        - Console/file output based on parameters and env vars
        - Gunicorn logger integration if available
        """
        # Output configuration
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.logger = self._configure_logger(
            logger=logger,
            logger_name=logger_name,
            log_file_name=log_file_name,
        )

        # Message storage
        self.stored_messages: defaultdict[str, set[str]] = defaultdict(set)
        self.error_list: list[str] = []
        self.last_error_instance: Any = None
        self.last_error_text: str | None = None

        # Message categorization and marking
        self.default_storage_marker = default_storage_marker
        self.current_context_marker: str | None = None
        self.verbosity_bypass_markers: list[str] = []

        # Log level filtering
        self.allowed_levels = self._normalize_levels(allowed_levels)
        self.denied_levels = self._normalize_levels(denied_levels)

        # Verbosity control
        self.enable_verbose_output = enable_verbose_output
        self.verbosity_threshold = verbosity_threshold

        # File management
        self.log_rotation_count = 0

    @staticmethod
    def _normalize_levels(levels: Sequence[str] | None) -> tuple[str, ...]:
        """Normalize provided log levels to lower-case tuples."""
        if not levels:
            return ()

        return tuple(level.lower() for level in levels)

    def register_verbosity_bypass_marker(self, marker: str) -> None:
        """Add a context marker that bypasses verbosity restrictions."""
        if marker not in self.verbosity_bypass_markers:
            self.verbosity_bypass_markers.append(marker)

    def _configure_logger(
        self,
        logger: logging.Logger | None = None,
        logger_name: str | None = None,
        log_file_name: str | None = None,
    ) -> logging.Logger:
        """Configure the logger instance.

        Args:
            logger: An existing logger instance to use.
            logger_name: The name for a new logger instance.
            log_file_name: The name of the log file if file logging enabled.

        Returns:
            logging.Logger: The configured logger instance.
        """
        logger_name = logger_name or get_unique_signature(self)
        log_file_name = (
            log_file_name or os.getenv("LOG_FILE_NAME") or f"{logger_name}.log"
        )
        logger = logger or logging.getLogger(logger_name)
        logger.propagate = False

        clear_existing_handlers(logger)

        log_level = get_log_level(os.getenv("LOG_LEVEL", "DEBUG"))
        logger.setLevel(log_level)

        self._setup_handlers(logger, log_file_name)
        return logger

    def _setup_handlers(self, logger: logging.Logger, log_file_name: str) -> None:
        """Set up console and file handlers.

        Args:
            logger: The logger to which handlers will be added.
            log_file_name: The name of the log file for file handler.
        """
        gunicorn_logger = find_logger("gunicorn.error")
        if gunicorn_logger:
            logger.handlers = gunicorn_logger.handlers
            logger.setLevel(gunicorn_logger.level)
            return

        if self.enable_console or strtobool(os.getenv("OVERRIDE_TO_CONSOLE", "False")):
            add_console_handler(logger)

        if self.enable_file or strtobool(os.getenv("OVERRIDE_TO_FILE", "False")):
            # Pass the log file name directly
            add_file_handler(logger, log_file_name)

    def verbosity_exceeded(self, verbose: bool, verbosity: int) -> bool:
        """Determines if a message should be suppressed based on verbosity settings.

        Args:
            verbose: Flag indicating if this is a verbose message.
            verbosity: The verbosity level of the message (1-5).

        Returns:
            bool: True if the message should be suppressed, False if it should be shown.

        A message is not suppressed if:
        1. The current context marker is in verbosity_bypass_markers
        2. Verbosity level <= threshold and either:
        - verbose=False, or
        - verbose=True and verbose output is enabled
        """
        if (
            self.current_context_marker
            and self.current_context_marker in self.verbosity_bypass_markers
        ):
            return False

        if verbosity > 1:
            verbose = True

        if verbose and not self.enable_verbose_output:
            return True

        return verbosity > self.verbosity_threshold

    def _prepare_message(
        self,
        msg: str,
        context_marker: str | None,
        identifiers: Sequence[str] | None,
    ) -> str:
        """Prepare the log message with context markers and identifiers.

        Args:
            msg: The base message to prepare.
            context_marker: Optional marker to prefix message with and set as current context.
            identifiers: Optional identifiers to append in parentheses.

        Returns:
            str: The prepared message with any context marker prefix and identifiers.
        """
        if context_marker is not None:
            self.current_context_marker = context_marker
            msg = f"[{self.current_context_marker}] {msg}"

        if identifiers:
            msg += " (" + ", ".join(cast(list[str], identifiers)) + ")"

        return msg

    def _store_logged_message(
        self,
        msg: str,
        log_level: LogLevel,
        storage_marker: str | None,
        allowed_levels: tuple[str, ...],
        denied_levels: tuple[str, ...],
    ) -> None:
        """Store the logged message if it meets the filtering criteria.

        Args:
            msg: The message to store.
            log_level: The level the message was logged at.
            storage_marker: The marker to store the message under.
            allowed_levels: Normalized levels that are allowed (if empty, all allowed).
            denied_levels: Normalized levels that are denied.

        Messages are stored in self.stored_messages under their storage_marker if:
        1. A storage_marker is provided
        2. The log_level is in allowed_levels (or allowed_levels is empty)
        3. The log_level is not in denied_levels

        Warning-level and above messages are prefixed with ':warning:'.
        """
        if not storage_marker:
            return

        if (
            not allowed_levels or log_level in allowed_levels
        ) and log_level not in denied_levels:
            self.stored_messages[storage_marker].add(
                f":warning: {msg}" if log_level not in ["debug", "info"] else msg,
            )

    def logged_statement(
        self,
        msg: str,
        json_data: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None = None,
        labeled_json_data: Mapping[str, Mapping[str, Any]] | None = None,
        identifiers: Sequence[str] | None = None,
        verbose: bool = False,
        verbosity: int = 1,
        context_marker: str | None = None,
        log_level: LogLevel = "debug",
        storage_marker: str | None = None,
        allowed_levels: Sequence[str] | None = None,
        denied_levels: Sequence[str] | None = None,
    ) -> str | None:
        """Log a statement with optional data, context marking, and storage.

        Args:
            msg: The message to log.
            json_data: Optional JSON data to append.
            labeled_json_data: Optional labeled JSON data to append.
            identifiers: Optional identifiers to append in parentheses.
            verbose: Whether this is a verbose message.
            verbosity: Verbosity level (1-5).
            context_marker: Marker to prefix message with and check for verbosity bypass.
            log_level: Level to log at.
            storage_marker: Marker for storing in message collections.
            allowed_levels: Override of allowed log levels.
            denied_levels: Override of denied log levels.

        Returns:
            str | None: The final message if logged, None if suppressed by verbosity.
        """
        if self.verbosity_exceeded(verbose, verbosity) and not (
            context_marker and context_marker in self.verbosity_bypass_markers
        ):
            return None

        final_msg = self._prepare_message(msg, context_marker, identifiers)
        final_msg = add_json_data(final_msg, json_data, labeled_json_data)

        # Normalize levels once here before passing to storage
        final_allowed = (
            self._normalize_levels(allowed_levels)
            if allowed_levels is not None
            else self.allowed_levels
        )
        final_denied = (
            self._normalize_levels(denied_levels)
            if denied_levels is not None
            else self.denied_levels
        )

        self._store_logged_message(
            final_msg,
            log_level,
            storage_marker or self.default_storage_marker,
            final_allowed,
            final_denied,
        )

        logger_method = getattr(self.logger, log_level)
        logger_method(final_msg)
        return final_msg
