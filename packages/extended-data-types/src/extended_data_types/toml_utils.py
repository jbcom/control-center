"""TOML Utilities Module.

This module provides utilities for encoding and decoding TOML data using tomlkit.
"""

from __future__ import annotations

from typing import Any

import tomlkit

from tomlkit.exceptions import TOMLKitError

from .string_data_type import bytestostr
from .type_utils import convert_special_types


def decode_toml(toml_data: str | memoryview | bytes | bytearray) -> Any:
    """Decodes a TOML string into a Python object using tomlkit.

    Args:
        toml_data (str | memoryview | bytes | bytearray): The TOML string to decode.

    Returns:
        Any: The decoded Python object with any special types processed.
    """
    try:
        toml_data = bytestostr(toml_data)
    except UnicodeDecodeError as exc:
        raise TOMLKitError(f"Failed to decode bytes to string: {toml_data!r}") from exc
    return tomlkit.parse(toml_data)


def encode_toml(raw_data: Any) -> str:
    """Encodes a Python object into a TOML string using tomlkit.

    Args:
        raw_data (Any): The Python object to encode.

    Returns:
        str: The encoded TOML string.
    """
    # Convert unsupported types to simpler forms before encoding
    converted_data = convert_special_types(raw_data)
    return tomlkit.dumps(converted_data)
