"""This module provides utilities for string and value matching.

It includes functions to partially match strings and to compare non-empty values
for equality, handling different data types including strings, mappings, and lists.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .json_utils import encode_json
from .state_utils import is_nothing


def is_partial_match(
    a: str | None,
    b: str | None,
    check_prefix_only: bool = False,
) -> bool:
    """Checks if two strings partially match.

    Args:
        a (str | None): The first string.
        b (str | None): The second string.
        check_prefix_only (bool): Whether to check only the prefix.

    Returns:
        bool: True if there is a partial match, False otherwise.
    """
    if is_nothing(a) or is_nothing(b):
        return False

    # Convert strings to lowercase for case-insensitive comparison
    a = a.casefold() if a else ""
    b = b.casefold() if b else ""

    # Check if one string is a prefix of the other
    if check_prefix_only:
        return a.startswith(b) or b.startswith(a)

    # Check if one string is contained within the other
    return a in b or b in a


def is_non_empty_match(a: Any, b: Any) -> bool:
    """Checks if two non-empty values match.

    Args:
        a (Any): The first value.
        b (Any): The second value.

    Returns:
        bool: True if the values match, False otherwise.
    """
    if is_nothing(a) or is_nothing(b):
        return False

    # Ensure both values are of the same type
    if not isinstance(a, type(b)):
        return False

    # Handle string comparisons case-insensitively
    if isinstance(a, str):
        a = a.casefold()
        b = b.casefold()
    # Handle mapping types by encoding to JSON with sorted keys
    elif isinstance(a, Mapping):
        a = encode_json(a, sort_keys=True)
        b = encode_json(b, sort_keys=True)
    # Handle lists by sorting, ensuring types within lists are comparable
    elif isinstance(a, list) and isinstance(b, list):
        try:
            a.sort()
            b.sort()
        except TypeError:
            # If elements are not comparable, return False
            return False

    # Return comparison result
    return a == b
