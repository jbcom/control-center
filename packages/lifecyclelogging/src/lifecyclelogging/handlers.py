"""Handlers for different logging outputs."""

from __future__ import annotations

import logging
import re

from pathlib import Path

from rich.logging import RichHandler


def add_file_handler(logger: logging.Logger, log_file_name: str) -> None:
    """Add a file handler to the logger, ensuring the file name is valid.

    Args:
        logger (logging.Logger): The logger to which the file handler will be added.
        log_file_name (str): The name of the log file.
    """
    # Convert to Path object to separate directory from filename
    original_path = Path(log_file_name)

    # Sanitize only the filename part (not the directory path)
    filename = original_path.name
    sanitized_name = re.sub(r"[^0-9a-zA-Z.]+", "_", filename.rstrip(".log"))
    if not sanitized_name[:1].isalnum():
        first_alpha = re.search(r"[A-Za-z0-9]", sanitized_name)
        if not first_alpha:
            error_message = f"Malformed log file name: {log_file_name} must contain at least one ASCII character"
            raise RuntimeError(error_message)
        sanitized_name = sanitized_name[first_alpha.start() :]

    # Add .log extension back if not present
    if not sanitized_name.endswith(".log"):
        sanitized_name += ".log"

    # Reconstruct the full path with sanitized filename
    log_file_path = (original_path.parent / sanitized_name).resolve()

    # Ensure the directory exists
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Add the file handler
    file_handler = logging.FileHandler(log_file_path)
    file_formatter = logging.Formatter(
        "[%(created)d] [%(threadName)s] [%(levelname)-8s] %(message)s",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)


def add_console_handler(logger: logging.Logger) -> None:
    """Adds a Rich console handler to the logger.

    Args:
        logger (logging.Logger): The logger to which the console handler will be added.
    """
    console_handler = RichHandler(rich_tracebacks=True)
    console_formatter = logging.Formatter("%(message)s", datefmt="[%X]")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
