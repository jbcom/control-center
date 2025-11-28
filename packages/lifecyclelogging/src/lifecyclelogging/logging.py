"""Core logging functionality for flexible and configurable logging management.

This module provides a Logging class that supports advanced logging features including:
- Configurable console and file logging
- Message storage and filtering
- Verbosity control
- Context and storage marker systems
- Clean exit with formatted output (exit_run)

The module allows for fine-grained control over log message handling, storage,
and output across different logging contexts.
"""

from __future__ import annotations

import base64
import logging
import os
import sys

from collections import defaultdict
from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import (
    Any,
    Callable,
    ClassVar,
    cast,
)

import orjson

from extended_data_types import (
    get_unique_signature,
    is_nothing,
    strtobool,
    to_camel_case,
    to_kebab_case,
    to_pascal_case,
    to_snake_case,
    wrap_raw_data_for_export,
)

from .const import VERBOSITY
from .handlers import add_console_handler, add_file_handler
from .log_types import LogLevel
from .utils import add_json_data, clear_existing_handlers, find_logger, get_log_level


# Type alias for key transformation functions
KeyTransform = Callable[[str], str]


class ExitRunError(Exception):
    """Raised when exit_run encounters a formatting or data error."""


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

    def log_results(
        self,
        results: Any,
        log_file_name: str,
        no_formatting: bool = False,
        ext: str | None = None,
        verbose: bool = False,
        verbosity: int = 0,
    ) -> None:
        """Log results to a file.

        Args:
            results: The results to log.
            log_file_name: Base name for the log file.
            no_formatting: If True, write results as-is without JSON formatting.
            ext: File extension (defaults to ".json").
            verbose: Whether this is a verbose log.
            verbosity: Verbosity level for this log.
        """
        if self.verbosity_exceeded(verbose, verbosity):
            return

        log_file_path = Path(f"./{log_file_name}").with_suffix(ext or ".json")
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        if no_formatting:
            log_file_path.write_text(str(results))
        else:
            log_file_path.write_text(
                wrap_raw_data_for_export(results, allow_encoding=True)
            )

        self.logged_statement(f"New results log: {log_file_path}")

    # Built-in key transforms from extended-data-types
    KEY_TRANSFORMS: ClassVar[dict[str, KeyTransform]] = {
        "snake_case": to_snake_case,
        "camel_case": to_camel_case,
        "pascal_case": to_pascal_case,
        "kebab_case": to_kebab_case,
    }

    def _resolve_key_transform(
        self,
        key_transform: KeyTransform | str | None,
        unhump_results: bool,
        prefix: str | None,
    ) -> KeyTransform | None:
        """Resolve key_transform parameter to a callable.

        Args:
            key_transform: User-provided transform (callable, string name, or None).
            unhump_results: Legacy flag for snake_case transformation.
            prefix: If set, implies transformation is needed.

        Returns:
            A callable transform function or None.
        """
        # Explicit transform takes precedence
        if key_transform is not None:
            if callable(key_transform):
                return key_transform
            if isinstance(key_transform, str):
                if key_transform not in self.KEY_TRANSFORMS:
                    available = ", ".join(self.KEY_TRANSFORMS.keys())
                    raise ValueError(
                        f"Unknown key_transform '{key_transform}'. "
                        f"Available: {available}"
                    )
                return self.KEY_TRANSFORMS[key_transform]

        # Legacy unhump_results flag
        if unhump_results or prefix:
            return to_snake_case

        return None

    def _transform_nested_keys(
        self,
        data: Mapping[str, Any],
        transform_fn: KeyTransform,
    ) -> dict[str, Any]:
        """Recursively transform all keys in a nested mapping.

        Args:
            data: The mapping to transform.
            transform_fn: Function to apply to each key.

        Returns:
            A new dict with all keys transformed.
        """
        result = {}
        for key, value in data.items():
            transformed_key = transform_fn(key)
            if isinstance(value, Mapping):
                result[transformed_key] = self._transform_nested_keys(
                    value, transform_fn
                )
            elif isinstance(value, list):
                result[transformed_key] = [
                    self._transform_nested_keys(item, transform_fn)
                    if isinstance(item, Mapping)
                    else item
                    for item in value
                ]
            else:
                result[transformed_key] = value
        return result

    def exit_run(
        self,
        results: Mapping[str, Any] | None = None,
        unhump_results: bool = False,
        key_transform: KeyTransform | str | None = None,
        prefix: str | None = None,
        prefix_allowlist: Sequence[str] | None = None,
        prefix_denylist: Sequence[str] | None = None,
        prefix_delimiter: str = "_",
        sort_by_field: str | None = None,
        format_results: bool = True,
        encode_to_base64: bool = False,
        encode_all_values_to_base64: bool = False,
        key: str | None = None,
        exit_on_completion: bool = True,
        **format_opts: Any,
    ) -> Any:
        """Format results and optionally exit the program cleanly.

        This method handles the lifecycle of formatting and outputting results,
        typically used at the end of a data processing run. It supports:
        - Error aggregation and reporting
        - Result transformation (key transforms, prefixing, sorting)
        - Base64 encoding
        - JSON serialization
        - Clean stdout output and exit

        Args:
            results: The results to format and output. Defaults to empty dict.
            unhump_results: Convert camelCase keys to snake_case (shorthand for
                key_transform="snake_case").
            key_transform: Transform function for result keys. Can be:
                - A callable that takes a string and returns a string
                - A string naming a built-in transform: "snake_case", "camel_case",
                  "pascal_case", "kebab_case"
                - None to skip transformation
                When unhump_results=True, defaults to "snake_case".
            prefix: Prefix to add to result keys (implies key transformation).
            prefix_allowlist: Keys to include when prefixing.
            prefix_denylist: Keys to exclude when prefixing.
            prefix_delimiter: Delimiter between prefix and key (default "_").
            sort_by_field: Sort results by this field's value.
            format_results: Whether to format results before base64 encoding.
            encode_to_base64: Encode entire result to base64.
            encode_all_values_to_base64: Encode each top-level value to base64.
            key: Wrap results in a dict with this key.
            exit_on_completion: If True, write to stdout and exit(0).
                If False, return the formatted results.
            **format_opts: Additional options for wrap_raw_data_for_export.

        Returns:
            If exit_on_completion=False, returns the formatted results.
            Otherwise, writes to stdout and exits with code 0.

        Raises:
            RuntimeError: If there are accumulated errors in error_list.
            ExitRunError: If result formatting fails.

        Examples:
            # Simple snake_case transformation (most common)
            logging.exit_run(results, unhump_results=True)

            # Explicit transform
            logging.exit_run(results, key_transform="kebab_case")

            # Custom transform function
            logging.exit_run(results, key_transform=lambda k: k.upper())
        """
        # Resolve key_transform from various inputs
        transform_fn = self._resolve_key_transform(
            key_transform, unhump_results, prefix
        )
        try:
            self.log_results(results, "results")

            if self.error_list:
                raise RuntimeError(os.linesep.join(self.error_list))

            prefix_allowlist = list(prefix_allowlist) if prefix_allowlist else []
            prefix_denylist = list(prefix_denylist) if prefix_denylist else []

            if results is None:
                results = {}

            if sort_by_field:
                sorted_results = {}
                field_value_counts: dict[str, int] = {}
                for top_level_key, top_level_value in results.items():
                    field_data = top_level_value.get(sort_by_field)
                    if is_nothing(field_data):
                        raise ExitRunError(
                            f"Cannot return results when top level key {top_level_key}'s "
                            f"value for sort by field {sort_by_field} is empty or does not exist"
                        )
                    # Handle duplicate field values by appending a suffix
                    new_key = str(field_data)
                    if new_key in field_value_counts:
                        field_value_counts[new_key] += 1
                        new_key = f"{new_key}_{field_value_counts[new_key]}"
                    else:
                        field_value_counts[new_key] = 0
                    sorted_results[new_key] = top_level_value
                results = sorted_results

            if transform_fn is not None:
                if prefix:
                    for top_level_key, top_level_value in results.items():
                        if not isinstance(top_level_value, Mapping):
                            results[top_level_key] = top_level_value
                            continue

                        transformed_result = {}
                        for field_name, field_data in top_level_value.items():
                            transformed_key = transform_fn(field_name)

                            if (
                                (
                                    is_nothing(prefix_allowlist)
                                    or field_name in prefix_allowlist
                                    or transformed_key in prefix_allowlist
                                )
                                and field_name not in prefix_denylist
                                and transformed_key not in prefix_denylist
                            ):
                                transformed_key = prefix_delimiter.join(
                                    [prefix, transformed_key]
                                )

                            if isinstance(field_data, Mapping):
                                transformed_result[transformed_key] = (
                                    self._transform_nested_keys(
                                        field_data, transform_fn
                                    )
                                )
                            elif isinstance(field_data, list):
                                transformed_result[transformed_key] = [
                                    self._transform_nested_keys(item, transform_fn)
                                    if isinstance(item, Mapping)
                                    else item
                                    for item in field_data
                                ]
                            else:
                                transformed_result[transformed_key] = field_data

                        results[top_level_key] = transformed_result
                else:
                    results = self._transform_nested_keys(results, transform_fn)

            if not exit_on_completion:
                return results

            if "default" not in format_opts:
                format_opts["default"] = str

            def encode_result_with_base64(r: Any) -> str:
                if format_results:
                    self.logger.info(
                        "Formatting results before encoding them with base64"
                    )
                    r = wrap_raw_data_for_export(r, **format_opts)

                # Ensure we have a string for encoding
                if isinstance(r, bytes):
                    return base64.b64encode(r).decode("utf-8")
                if isinstance(r, str):
                    return base64.b64encode(r.encode("utf-8")).decode("utf-8")
                return base64.b64encode(str(r).encode("utf-8")).decode("utf-8")

            if encode_all_values_to_base64:
                self.logger.info("Encoding all top-level values in results with base64")
                results = {
                    top_level_key: encode_result_with_base64(top_level_value)
                    for top_level_key, top_level_value in deepcopy(results).items()
                }
                self.log_results(results, "results_values_base64_encoded")

            if encode_to_base64:
                self.logger.info("Encoding results with base64")
                results = encode_result_with_base64(results)
                self.log_results(results, "results_base64_encoded")

            if key:
                self.logger.info("Wrapping results in key %s", key)
                results = {key: results}

            if not isinstance(results, str):
                self.logger.info("Dumping results to JSON")
                results = orjson.dumps(results, default=str).decode("utf-8")

            sys.stdout.write(results)
            sys.exit(0)
        except ExitRunError as exc:
            err_msg = (
                f"Failed to dump results because of a formatting error:\n\n{results}"
            )
            self.logger.critical(err_msg, exc_info=True)
            raise RuntimeError(err_msg) from exc
