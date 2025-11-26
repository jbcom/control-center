"""Base utilities for cloud connectors."""

from .errors import FailedResponseError, RequestRateLimitedError, StateFileNotFoundError
from .logging import (
    Logging,
    add_console_handler,
    add_file_handler,
    clear_existing_handlers,
    find_logger,
    get_log_level,
    get_loggers,
)
from .utils import (
    FilePath,
    Utils,
    get_default_dict,
    get_encoding_for_file_path,
    is_nothing,
    make_hashable,
    wrap_raw_data_for_export,
)

__all__ = [
    "Utils",
    "FilePath",
    "get_default_dict",
    "make_hashable",
    "wrap_raw_data_for_export",
    "is_nothing",
    "get_encoding_for_file_path",
    "FailedResponseError",
    "StateFileNotFoundError",
    "RequestRateLimitedError",
]
