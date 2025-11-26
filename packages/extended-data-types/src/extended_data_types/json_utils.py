"""JSON Utilities Module.

This module provides utilities for encoding and decoding JSON.
"""

from __future__ import annotations

from typing import Any, Callable

import orjson


def decode_json(json_data: str | memoryview | bytes | bytearray) -> Any:
    """Decodes a JSON string or bytes into a Python object using orjson.

    Args:
        json_data (str | memoryview | bytes | bytearray): The JSON string or bytes to decode.

    Returns:
        Any: The decoded Python object.
    """
    return orjson.loads(json_data)


def encode_json(
    raw_data: Any,
    default: Callable[[Any], Any] | None = None,
    indent_2: bool = False,
    naive_utc: bool = False,
    non_str_keys: bool = False,
    omit_microseconds: bool = False,
    passthrough_dataclass: bool = False,
    passthrough_datetime: bool = False,
    passthrough_subclass: bool = False,
    serialize_numpy: bool = False,
    strict_integer: bool = False,
    utc_z: bool = False,
    sort_keys: bool = False,
    append_newline: bool = False,
) -> str:
    """Encodes a Python object into a JSON string using orjson.

    Args:
        raw_data (Any): The Python object to encode.
        default (Callable[[Any], Any] | None): A callable for serializing unsupported types.
        indent_2 (bool): Pretty-print output with an indent of two spaces.
        naive_utc (bool): Serialize naive datetime objects as UTC.
        non_str_keys (bool): Allow dict keys of types other than str.
        omit_microseconds (bool): Omit microseconds in datetime and time objects.
        passthrough_dataclass (bool): Passthrough dataclasses to default handler.
        passthrough_datetime (bool): Passthrough datetime objects to default handler.
        passthrough_subclass (bool): Passthrough subclasses of built-in types to default handler.
        serialize_numpy (bool): Serialize numpy arrays natively.
        strict_integer (bool): Enforce 53-bit limit on integers.
        utc_z (bool): Use 'Z' instead of '+00:00' for UTC datetime.
        sort_keys (bool): Serialize dict keys in sorted order.
        append_newline (bool): Append newline to the end of the output.

    Returns:
        str: The encoded JSON string.

    Raises:
        orjson.JSONEncodeError: If an unsupported type is encountered and default is not provided.
    """
    # Calculate the bitmask for orjson options based on the parameters
    option = 0
    if indent_2:
        option |= orjson.OPT_INDENT_2
    if naive_utc:
        option |= orjson.OPT_NAIVE_UTC
    if non_str_keys:
        option |= orjson.OPT_NON_STR_KEYS
    if omit_microseconds:
        option |= orjson.OPT_OMIT_MICROSECONDS
    if passthrough_dataclass:
        option |= orjson.OPT_PASSTHROUGH_DATACLASS
    if passthrough_datetime:
        option |= orjson.OPT_PASSTHROUGH_DATETIME
    if passthrough_subclass:
        option |= orjson.OPT_PASSTHROUGH_SUBCLASS
    if serialize_numpy:
        option |= orjson.OPT_SERIALIZE_NUMPY
    if strict_integer:
        option |= orjson.OPT_STRICT_INTEGER
    if utc_z:
        option |= orjson.OPT_UTC_Z
    if sort_keys:
        option |= orjson.OPT_SORT_KEYS
    if append_newline:
        option |= orjson.OPT_APPEND_NEWLINE

    # Use orjson.dumps to encode the object with the calculated options
    return orjson.dumps(raw_data, default=default, option=option).decode("utf-8")
