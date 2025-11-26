import logging
import os
import re
from collections import defaultdict
from copy import deepcopy, copy
from typing import Mapping, Literal, Any

from extended_data_types import strtobool, get_unique_signature, is_nothing, wrap_raw_data_for_export, all_non_empty
from rich.logging import RichHandler

from cloud_connectors.base.settings import DEFAULT_LOG_LEVEL, VERBOSITY


def get_log_level(level: int | str) -> int:
    """
    Converts a log level from string or integer to a logging level integer.

    Args:
        level (int | str): The log level, either as a string (e.g., 'DEBUG') or an integer.

    Returns:
        int: The corresponding log level integer or the default log level if not found.
    """
    mappings = logging.getLevelNamesMapping()
    if isinstance(level, str):
        return mappings.get(level.upper(), DEFAULT_LOG_LEVEL)

    return level if level in mappings.values() else DEFAULT_LOG_LEVEL


def get_loggers() -> list[logging.Logger]:
    """
    Retrieves all active loggers.

    Returns:
        list[logging.Logger]: A list of active loggers.
    """
    loggers = [logging.getLogger()]
    loggers += [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    return loggers


def find_logger(name: str) -> logging.Logger | None:
    """
    Finds a logger by its name.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger | None: The logger if found; otherwise, None.
    """
    for logger in get_loggers():
        if logger.name == name:
            return logger
    return None


def add_file_handler(logger: logging.Logger, log_file_name: str) -> None:
    """
    Adds a file handler to the logger, sanitizing the file name.

    Args:
        logger (logging.Logger): The logger to which the file handler is added.
        log_file_name (str): The name of the log file.
    """
    sanitized_name = re.sub(r"[^0-9a-zA-Z]+", "_", log_file_name.rstrip(".log"))
    if not sanitized_name[:1].isalnum():
        first_alpha = re.search(r"[A-Za-z0-9]", sanitized_name)
        if not first_alpha:
            raise RuntimeError(
                f"Malformed log file name: {sanitized_name} must contain at least one ASCII character"
            )
        sanitized_name = sanitized_name[first_alpha.start():]

    log_file = f"{sanitized_name}.log"
    file_handler = logging.FileHandler(log_file)
    file_formatter = logging.Formatter("[%(created)d] [%(threadName)s] [%(levelname)-8s] %(message)s")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)


def clear_existing_handlers(logger: logging.Logger):
    """Removes all existing handlers from the logger."""
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()


def add_console_handler(logger: logging.Logger) -> None:
    """
    Adds a Rich console handler to the logger.

    Args:
        logger (logging.Logger): The logger to which the console handler is added.
    """
    console_handler = RichHandler(rich_tracebacks=True)
    console_formatter = logging.Formatter("%(message)s", datefmt="[%X]")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)


class Logging:
    """
    A class to manage logging configurations for console and file outputs.

    Attributes:
        to_console (bool): Flag indicating whether to log to the console.
        to_file (bool): Flag indicating whether to log to a file.
        logger (logging.Logger): The configured logger instance.
        logs (defaultdict): A defaultdict for storing logged messages by marker.
        errors (list): A list to store error messages.
        last_error (Any): The last error that occurred.
        last_error_message (str): The message of the last error.
        active_marker (str): The current active log marker.
    """

    def __init__(
            self,
            to_console: bool = False,
            to_file: bool = True,
            logger: logging.Logger | None = None,
            logger_name: str | None = None,
            log_file_name: str | None = None,
            log_marker: str | None = None,
            logged_statements_allowlist: list[str] | None = None,
            logged_statements_denylist: list[str] | None = None
    ):
        """
        Initializes the Logging class with options for console and file logging.

        Args:
            to_console (bool): Whether to log to the console.
            to_file (bool): Whether to log to a file.
            logger (logging.Logger | None): An existing logger instance to use.
            logger_name (str): The name of the logger.
            log_file_name (str | None): The name of the log file.
            log_marker (str | None): Default marker for log messages.
            logged_statements_allowlist (list[str] | None): A list of allowed log levels.
            logged_statements_denylist (list[str] | None): A list of denied log levels.
        """
        self.to_console = to_console
        self.to_file = to_file
        # Set the logger and determine the log file name based on provided arguments or environment variables
        self.logger = self.get_logger(logger=logger, logger_name=logger_name, log_file_name=log_file_name)
        self.logs = defaultdict(set)
        self.default_log_marker = log_marker
        self.default_logged_statements_allowlist = logged_statements_allowlist
        self.default_logged_statements_denylist = logged_statements_denylist
        self.errors = []
        self.last_error = None
        self.last_error_message = None
        self.active_marker = None
        self.log_file_count = 0

    def get_logger(
            self,
            to_console: bool | None = None,
            to_file: bool | None = None,
            logger: logging.Logger | None = None,
            logger_name: str | None = None,
            log_file_name: str | None = None,
    ) -> logging.Logger:
        """
        Configures and returns a logger with console and/or file handlers.

        Args:
            to_console (bool | None): Override for console logging.
            to_file (bool | None): Override for file logging.
            logger (logging.Logger | None): An existing logger to configure.
            logger_name (str | None): A name for the logger.
            log_file_name (str | None): The log file name.

        Returns:
            logging.Logger: The configured logger instance.
        """
        to_console = to_console if to_console is not None else self.to_console
        to_file = to_file if to_file is not None else self.to_file

        # Determine the logger name or default to a unique signature of the instance
        logger_name = logger_name or get_unique_signature(self)

        # Determine log file name, using environment variable or logger name if not explicitly provided
        log_file_name = log_file_name or os.getenv("LOG_FILE_NAME") or f"{logger_name}.log"
        logger = logger or logging.getLogger(logger_name)
        logger.propagate = False

        # Clear existing handlers to prevent log duplication
        clear_existing_handlers(logger)

        # Set logger level based on environment or default to DEBUG
        log_level = get_log_level(os.getenv("LOG_LEVEL", "DEBUG"))
        logger.setLevel(log_level)

        # Use Gunicorn logger if available to inherit handlers
        gunicorn_logger = find_logger("gunicorn.error")
        if gunicorn_logger:
            logger.handlers = gunicorn_logger.handlers
            logger.setLevel(gunicorn_logger.level)
            to_console = False

        # Add console handler if enabled or overridden by environment
        if to_console or strtobool(os.getenv("OVERRIDE_TO_CONSOLE", "False")):
            add_console_handler(logger)

        # Add file handler if enabled or overridden by environment
        if to_file or strtobool(os.getenv("OVERRIDE_TO_FILE", "False")):
            add_file_handler(logger, log_file_name)

        return logger

    def verbosity_exceeded(self, verbose: bool, verbosity: int) -> bool:
        """
        Checks if the verbosity level exceeds the configured maximum.

        Args:
            verbose (bool): Indicates if verbose mode is enabled.
            verbosity (int): The verbosity level.

        Returns:
            bool: True if the verbosity level is exceeded, otherwise False.
        """
        debug_markers = getattr(self, "DEBUG_MARKERS", [])
        if self.active_marker in debug_markers:
            return False

        if verbosity > 1:
            verbose = True

        if not getattr(self, "VERBOSE", None) and verbose:
            return True

        try:
            max_verbosity = int(getattr(self, "VERBOSITY", VERBOSITY))
        except ValueError:
            max_verbosity = VERBOSITY

        return verbosity > max_verbosity

    def logged_statement(
            self,
            msg: str,
            json_data: list[Mapping[str, Any]] | Mapping[str, Any] | None = None,
            labeled_json_data: Mapping[str, Mapping[str, Any]] | None = None,
            identifiers: list[str] | None = None,
            verbose: bool | None = False,
            verbosity: int | None = 1,
            active_marker: str | None = None,
            log_level: Literal[
                "debug", "info", "warning", "error", "fatal", "critical"
            ] = "debug",
            log_marker: str | None = None,
            allowlist: list[str] | None = None,
            denylist: list[str] | None = None,
    ) -> str | None:
        """
        Logs a statement with optional data and verbosity controls.

        Args:
            msg (str): The message to log.
            json_data (list[Mapping[str, Any]] | Mapping[str, Any] | None): Optional JSON data to log.
            labeled_json_data (Mapping[str, Mapping[str, Any]] | None): Labeled JSON data to log.
            identifiers (list[str] | None): Optional identifiers to include in the message.
            verbose (bool | None): Flag for verbosity control.
            verbosity (int | None): Verbosity level.
            active_marker (str | None): Marker to indicate the active logging state.
            log_level (Literal["debug", "info", "warning", "error", "fatal", "critical"]): The level at which to log the statement.
            log_marker (str | None): The marker associated with the log statement.
            allowlist (list[str] | None): List of allowed log levels.
            denylist (list[str] | None): List of denied log levels.

        Returns:
            str | None: The formatted message if logged, otherwise None.
        """
        if not is_nothing(active_marker):
            self.active_marker = active_marker

        if not is_nothing(self.active_marker):
            msg = f"[{self.active_marker}] {msg}"

        if self.verbosity_exceeded(verbose, verbosity):
            return None

        if not is_nothing(identifiers):
            msg += " (" + ", ".join(all_non_empty(*identifiers)) + ")"

        if labeled_json_data:
            for label, jd in deepcopy(labeled_json_data).items():
                if not isinstance(jd, Mapping):
                    jd = {label: jd}
                    msg += "\n:" + wrap_raw_data_for_export(jd, allow_encoding=True)
                    continue

                msg += f"\n{label}:\n" + wrap_raw_data_for_export(jd, allow_encoding=True)

        if json_data:
            unlabeled_json_data = deepcopy(json_data) if isinstance(json_data, list) else [copy(json_data)]

            for jd in unlabeled_json_data:
                msg += "\n:" + wrap_raw_data_for_export(jd, allow_encoding=True)

        log_marker = log_marker or self.default_log_marker
        allowlist = allowlist or self.default_logged_statements_allowlist or []
        denylist = denylist or self.default_logged_statements_denylist or []

        if (
                not is_nothing(log_marker)
                and (is_nothing(allowlist) or log_level in allowlist)
                and log_level not in denylist
        ):
            self.logs[log_marker].add(f":warning: {msg}" if log_level not in ["debug", "info"] else msg)

        logger = getattr(self.logger, log_level)
        logger(msg)
        return msg
