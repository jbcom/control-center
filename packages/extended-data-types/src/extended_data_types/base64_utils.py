"""This module provides utilities for encoding and decoding data to and from Base64 format.

It includes functions to encode data to Base64 strings, with optional data
wrapping for export, and to decode Base64 strings back to their original data.
"""

from __future__ import annotations

from base64 import b64decode, b64encode

from .export_utils import wrap_raw_data_for_export
from .import_utils import unwrap_raw_data_from_import


def base64_encode(raw_data: str | bytes, wrap_raw_data: bool = True) -> str:
    """Encodes data to base64 format.

    Args:
        raw_data (str | bytes): The data to encode.
        wrap_raw_data (bool): Whether to wrap the raw data for export.

    Returns:
        str: The base64 encoded string.
    """
    if wrap_raw_data:
        if isinstance(raw_data, bytes):
            raw_data = raw_data.decode("utf-8")
        raw_data = wrap_raw_data_for_export(raw_data).encode("utf-8")
    elif isinstance(raw_data, str):
        raw_data = raw_data.encode("utf-8")

    return b64encode(raw_data).decode("utf-8")


def base64_decode(
    encoded_data: str,
    unwrap_raw_data: bool = True,
    encoding: str = "yaml",
) -> str | bytes:
    """Decodes data from base64 format.

    Args:
        encoded_data (str): The base64 encoded string to decode.
        unwrap_raw_data (bool): Whether to unwrap the raw data after decoding.
        encoding (str): The encoding format used for wrapping (default is 'yaml').

    Returns:
        str | bytes: The decoded data, as a string if unwrapped, otherwise as bytes.
    """
    decoded_data = b64decode(encoded_data).decode("utf-8")
    if unwrap_raw_data:
        decoded_data = unwrap_raw_data_from_import(decoded_data, encoding=encoding)
    return decoded_data
