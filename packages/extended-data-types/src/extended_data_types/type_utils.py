"""Type Utilities.

This module provides utility functions related to Python types, specifically for retrieving
default values based on the type, converting special types to simpler forms, and reconstructing
simplified types back to their original forms. It includes functions for getting default values
for common types, determining whether to return primitive or exact types of a given value, and
handling conversions for datetime, path, and complex types.

Functions:
    - get_default_value_for_type: Returns the default value for a given type.
    - get_primitive_type_for_instance_type: Returns the primitive type for a given value.
    - typeof: Returns the type (or primitive type) of a given value.
    - convert_special_type: Converts a single special type to a simpler form.
    - convert_special_types: Converts an object and its contents to simpler forms.
    - reconstruct_special_type: Reconstructs a simplified type back to its original form.
    - reconstruct_special_types: Reconstructs an object and its contents back to their original types.

Classes:
    - ConversionError: Custom error class for handling conversion failures.
    - ReconstructionError: Custom error class for handling reconstruction failures.

Constants:
    - DATE_PATTERN: Regex for matching ISO 8601 date strings.
    - DATETIME_PATTERN: Regex for matching ISO 8601 datetime strings.
    - TIME_PATTERN: Regex for matching time strings.
    - PATH_PATTERN: Regex for matching Unix and Windows-style paths.
    - NUMBER_PATTERN: Regex for matching numeric strings.
    - TRUTHY_PATTERN: Regex for matching truthy strings.
    - FALSY_PATTERN: Regex for matching falsy strings.
"""

from __future__ import annotations

import datetime
import os
import pathlib
import re

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from orjson import JSONDecodeError
from yaml.error import YAMLError

from .json_utils import decode_json
from .string_data_type import removesuffix
from .yaml_utils import YamlPairs, YamlTagged, decode_yaml


# Patterns for matching date, datetime, and time strings
DATE_PATTERN: re.Pattern[str] = re.compile(r"^\d{4}-\d{2}-\d{2}$")  # Matches YYYY-MM-DD
DATETIME_PATTERN: re.Pattern[str] = re.compile(
    r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2})?(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?$"
)  # Matches extended datetime formats like YYYY-MM-DDTHH:MM[:SS][.fff][Z|±hh:mm]
TIME_PATTERN: re.Pattern[str] = re.compile(
    r"^\d{2}:\d{2}(:\d{2}(\.\d{1,6})?)?$"
)  # Matches HH:MM[:SS] and microseconds
PATH_PATTERN: re.Pattern[str] = re.compile(
    r'^(?:[a-zA-Z]:)?[\\/](?:[^<>:"|?*\n]+[\\/])*[^<>:"|?*\n]*$'
)
NUMBER_PATTERN: re.Pattern[str] = re.compile(r"^-?\d+(\.\d+)?$")
TRUTHY_PATTERN: re.Pattern[str] = re.compile(r"^(y|yes|t|true|on|1)$", re.IGNORECASE)
FALSY_PATTERN: re.Pattern[str] = re.compile(r"^(n|no|f|false|off|0)$", re.IGNORECASE)


class ConversionError(ValueError):
    """Custom error class for handling conversion failures.

    This error is raised during type conversions when the input value does not
    conform to the expected type format. For Path types, it ensures consistent
    error messaging across Python versions by normalizing the type representation.

    Args:
        expected_type (type): The expected Python type.
        value (Any): The actual value being converted.

    Raises:
        ValueError: Always raises as this is an error class.

    Example:
        >>> raise ConversionError(int, 'invalid')
        ConversionError: Invalid <class 'int'> value: 'invalid'
        >>> raise ConversionError(Path, 'invalid:://path')
        ConversionError: Invalid <class 'pathlib.Path'> value: 'invalid:://path'
        >>> raise ConversionError(float, 'not_a_number')
        ConversionError: Invalid <class 'float'> value: 'not_a_number'

    Note:
        When the expected_type is pathlib.Path, the error message will consistently
        display as "<class 'pathlib.Path'>" regardless of the internal Path implementation
        in different Python versions.
    """

    def __init__(self, expected_type: type, value: Any):
        """Initialize the ConversionError with expected type and value.

        Args:
            expected_type (type): The expected Python type. Special handling is
                applied for pathlib.Path to ensure consistent error messages across
                Python versions.
            value (Any): The actual value that failed conversion. Will be
                represented using repr() in the error message.

        Note:
            For Path types, the error message will always use 'pathlib.Path'
            notation regardless of the internal implementation details of the
            Path class in different Python versions.
        """
        self.expected_type = expected_type
        self.value = value

        # Handle Path type specially to ensure consistent error messages
        if expected_type == Path:
            type_str = "<class 'pathlib.Path'>"
        else:
            type_str = str(self.expected_type)

        super().__init__(f"Invalid {type_str} value: {self.value!r}")


def strtobool(val: str | bool | None, raise_on_error: bool = False) -> bool | None:
    """Converts a string representation of truth to boolean.

    Args:
        val (str | bool | None): The value to convert.
        raise_on_error (bool): Whether to raise an error on invalid value. Defaults to False.

    Returns:
        bool | None: The converted boolean value, or None if invalid and raise_on_error is False.

    Raises:
        ConversionError: If the value is invalid and raise_on_error is True.
    """
    if isinstance(val, bool) or val is None:
        return val

    if isinstance(val, str):
        if TRUTHY_PATTERN.match(val):
            return True
        if FALSY_PATTERN.match(val):
            return False

    if raise_on_error:
        raise ConversionError(bool, val)

    return None


def strtofloat(val: str, raise_on_error: bool = False) -> float | None:
    """Converts a string representation of a float to a float.

    Args:
        val (str): The string value to convert.
        raise_on_error (bool): Whether to raise an error on invalid value. Defaults to False.

    Returns:
        float | None: The converted float value, or None if invalid and raise_on_error is False.

    Raises:
        ConversionError: If the value is invalid and raise_on_error is True.
    """
    if NUMBER_PATTERN.match(val):
        try:
            return float(val)
        except ValueError as exc:
            if raise_on_error:
                raise ConversionError(float, val) from exc

    if raise_on_error:
        raise ConversionError(float, val)

    return None


def strtoint(val: str, raise_on_error: bool = False) -> int | None:
    """Converts a string representation of an integer to an int.

    Args:
        val (str): The string value to convert.
        raise_on_error (bool): Whether to raise an error on invalid value. Defaults to False.

    Returns:
        int | None: The converted integer value, or None if invalid and raise_on_error is False.

    Raises:
        ConversionError: If the value is invalid and raise_on_error is True.
    """
    try:
        float_value = strtofloat(val, raise_on_error=raise_on_error)
        if float_value is not None:
            return int(float_value)
    except ConversionError as exc:
        if raise_on_error:
            raise ConversionError(int, val) from exc

    if raise_on_error:
        raise ConversionError(int, val)

    return None


def strtopath(
    val: str | bytes | os.PathLike[str] | None, raise_on_error: bool = False
) -> Path | None:
    """Converts a string or byte representation of a path to a pathlib.Path object.

    Args:
        val (str | bytes | pathlib.Path | None): The value to convert.
        raise_on_error (bool): Whether to raise an error on invalid value. Defaults to False.

    Returns:
        pathlib.Path | None: The converted Path object, or None if invalid and raise_on_error is False.

    Raises:
        ConversionError: If the value is invalid and raise_on_error is True.
    """
    if isinstance(val, Path) or val is None:
        return val
    try:
        if isinstance(val, bytes):
            try:
                val = val.decode("utf-8")
            except UnicodeDecodeError as exc:
                if raise_on_error:
                    raise ConversionError(Path, val) from exc
                return None
        # Ensure val is converted to string before matching
        if not PATH_PATTERN.match(str(val)):
            raise ConversionError(Path, val)
        return Path(val)
    except (ValueError, TypeError) as exc:
        if raise_on_error:
            raise ConversionError(Path, val) from exc
    return None


def strtodate(val: str, raise_on_error: bool = False) -> datetime.date | None:
    """Converts a string representation of a date to a datetime.date object.

    Args:
        val (str): The string to convert, expected to be in the format YYYY-MM-DD.
        raise_on_error (bool): Whether to raise an error on invalid format. Defaults to False.

    Returns:
        datetime.date | None: The converted date object, or None if the format is invalid.

    Raises:
        ConversionError: If the value is invalid and raise_on_error is True.
    """
    if not DATE_PATTERN.match(val):
        if raise_on_error:
            raise ConversionError(datetime.date, val)
        return None
    try:
        return datetime.datetime.strptime(val, "%Y-%m-%d").date()
    except ValueError as exc:
        if raise_on_error:
            raise ConversionError(datetime.date, val) from exc
    return None


def strtodatetime(val: str, raise_on_error: bool = False) -> datetime.datetime | None:
    """Converts a string representation of a datetime to a datetime.datetime object.

    Args:
        val (str): The string to convert, expected to match various datetime formats like
        YYYY-MM-DDTHH:MM[:SS][.fff][Z|±hh:mm].
        raise_on_error (bool): Whether to raise an error on invalid format. Defaults to False.

    Returns:
        datetime.datetime | None: The converted datetime object, or None if the format is invalid.

    Raises:
        ConversionError: If the value is invalid and raise_on_error is True.
    """
    if not DATETIME_PATTERN.match(val):
        if raise_on_error:
            raise ConversionError(datetime.datetime, val)
        return None
    try:
        dt = datetime.datetime.fromisoformat(val.replace(" ", "T"))
        if dt.tzinfo is None:
            # Set UTC timezone if not provided
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt
    except ValueError as exc:
        if raise_on_error:
            raise ConversionError(datetime.datetime, val) from exc
    return None


def strtotime(val: str, raise_on_error: bool = False) -> datetime.time | None:
    """Converts a string representation of a time to a datetime.time object.

    Args:
        val (str): The string to convert, expected to be in the format HH:MM[:SS] or HH:MM:SS.ffffff.
        raise_on_error (bool): Whether to raise an error on invalid format. Defaults to False.

    Returns:
        datetime.time | None: The converted time object, or None if the format is invalid.

    Raises:
        ConversionError: If the value is invalid and raise_on_error is True.
    """
    if not TIME_PATTERN.match(val):
        if raise_on_error:
            raise ConversionError(datetime.time, val)
        return None

    try:
        if "." in val:
            return datetime.datetime.strptime(val, "%H:%M:%S.%f").time()
        if ":" in val[5:]:
            return datetime.datetime.strptime(val, "%H:%M:%S").time()
        return datetime.datetime.strptime(val, "%H:%M").time()
    except ValueError as exc:
        if raise_on_error:
            raise ConversionError(datetime.time, val) from exc
    return None


def get_default_value_for_type(input_type: type) -> Any:
    """Returns the default value for a given type."""
    if input_type is list:
        return []
    if input_type is dict:
        return {}
    if input_type is str:
        return ""
    return None


def get_primitive_type_for_instance_type(value: Any) -> type:
    """Gets the primitive type for a given value."""
    if isinstance(value, (bool, int, float, str, bytes, bytearray)):
        return type(value)
    if isinstance(value, (list, tuple)):
        return list
    if isinstance(value, dict):
        return dict
    if isinstance(value, (set, frozenset)):
        return set
    return type(None) if value is None else object


def typeof(item: Any, primitive_only: bool = False) -> type:
    """Determines either the primitive or exact type of a given value."""
    return get_primitive_type_for_instance_type(item) if primitive_only else type(item)


def convert_special_type(obj: Any) -> Any:
    """Converts a single special type to a simpler form."""
    if isinstance(obj, YamlTagged):
        obj = obj.__wrapped__
    elif isinstance(obj, YamlPairs):
        obj = list(obj)

    if isinstance(obj, (datetime.date, datetime.datetime)):
        return removesuffix(obj.isoformat(), "+00:00")
    if isinstance(obj, pathlib.Path):
        return str(obj)
    if isinstance(obj, (int, float, str, bool, type(None))):
        return obj

    return str(obj)


def convert_special_types(obj: Any) -> Any:
    """Converts an object and its contained objects of special types to simpler forms."""
    if isinstance(obj, Mapping):
        return {k: convert_special_types(v) for k, v in obj.items()}
    if isinstance(obj, (set, list)):
        return [convert_special_types(v) for v in obj]

    return convert_special_type(obj)


def is_potential_yaml(obj: str) -> bool:
    """Check if the given string is a potential YAML document.

    :param obj: The string to be checked.
    :return: True if the string is a potential YAML document, False otherwise.
    """
    yaml_indicators = [
        obj.startswith("---"),  # YAML document start
        ": " in obj,  # Key-value pattern
        "\n- " in obj,  # List item pattern
        "&" in obj,  # Anchor indicator
        "* " in obj,  # Alias indicator
    ]
    return any(yaml_indicators)


def is_potential_json(obj: str) -> bool:
    """Check if the given string is a potential JSON object or array.

    :param obj: The string to be checked.
    :return: True if the string is a potential JSON object or array, False otherwise.
    """
    return (obj.startswith("{") and obj.endswith("}")) or (
        obj.startswith("[") and obj.endswith("]")
    )


def reconstruct_special_type(converted_obj: str, fail_silently: bool = False) -> Any:
    """Attempts to reconstruct a special type from a string representation by sequentially
    matching known patterns and decoding them.

    Args:
        converted_obj (str): The string representation of the object to reconstruct.
        fail_silently (bool): Whether to fail silently without raising errors. Defaults to False.

    Returns:
        Any: The reconstructed object or the original string if reconstruction fails.

    Raises:
        ConversionError: If reconstruction fails and fail_silently is False.
    """
    try:
        if converted_obj == "None":
            return None
        if DATETIME_PATTERN.match(converted_obj):
            return strtodatetime(converted_obj)
        if DATE_PATTERN.match(converted_obj):
            return strtodate(converted_obj)
        if TIME_PATTERN.match(converted_obj):
            return strtotime(converted_obj)
        if PATH_PATTERN.match(converted_obj):
            return pathlib.Path(converted_obj)
        if TRUTHY_PATTERN.match(converted_obj) or FALSY_PATTERN.match(converted_obj):
            return strtobool(converted_obj)
        if NUMBER_PATTERN.match(converted_obj):
            if converted_obj.isdigit():
                return strtoint(converted_obj)
            return strtofloat(converted_obj)

        if is_potential_yaml(converted_obj):
            return decode_yaml(converted_obj)

        if is_potential_json(converted_obj):
            return decode_json(converted_obj)
    except (ValueError, TypeError, YAMLError, JSONDecodeError) as exc:
        if not fail_silently:
            raise ConversionError(type(converted_obj), converted_obj) from exc
    return converted_obj


def reconstruct_special_types(obj: Any, fail_silently: bool = False) -> Any:
    """Recursively reconstructs special types within nested data structures.

    Args:
        obj (Any): The object to reconstruct.
        fail_silently (bool): Whether to fail silently without raising errors. Defaults to False.

    Returns:
        Any: The reconstructed object with special types restored where applicable.
    """
    if isinstance(obj, str):
        return reconstruct_special_type(obj, fail_silently=fail_silently)
    if isinstance(obj, Mapping):
        return {
            k: reconstruct_special_types(v, fail_silently=fail_silently)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [reconstruct_special_types(v, fail_silently=fail_silently) for v in obj]
    if isinstance(obj, set):
        return {reconstruct_special_types(v, fail_silently=fail_silently) for v in obj}
    return obj


def make_hashable(obj: Any) -> Any:
    """Convert an object to a hashable type for use in cache keys or sets.

    This function recursively converts mutable types (dicts, lists) to their
    immutable equivalents (frozensets of tuples, tuples) so they can be used
    as dictionary keys or in sets.

    Args:
        obj: The object to convert to a hashable type.

    Returns:
        A hashable representation of the object:
        - Primitives (str, int, float, bool, None) are returned as-is
        - Lists and tuples are converted to tuples of hashable items
        - Dicts are converted to frozensets of (key, value) tuples
        - Other types are converted to their string representation

    Examples:
        >>> make_hashable({"a": 1, "b": [2, 3]})
        frozenset({('a', 1), ('b', (2, 3))})
        >>> make_hashable([1, 2, {"x": "y"}])
        (1, 2, frozenset({('x', 'y')}))
    """
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    if isinstance(obj, (list, tuple)):
        return tuple(make_hashable(item) for item in obj)
    if isinstance(obj, dict):
        return frozenset((k, make_hashable(v)) for k, v in sorted(obj.items()))
    # For other types, convert to string
    return str(obj)
