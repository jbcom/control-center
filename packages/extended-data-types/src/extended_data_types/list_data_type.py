"""This module provides utilities for handling lists.

It includes functions to flatten lists and to filter lists based on allowlists
and denylists.

Functions:
    - flatten_list: Flattens a list of lists into a single list.
    - filter_list: Filters a list based on allowlist and denylist.
"""

from __future__ import annotations

from typing import Any


def flatten_list(matrix: list[Any]) -> list[Any]:
    """Flattens a list of lists into a single list.

    Args:
        matrix (list[Any]): The list of lists to flatten.

    Returns:
        list[Any]: The flattened list.
    """

    def _flatten(lst: list[Any]) -> list[Any]:
        """Recursively flattens a nested list.

        Args:
            lst (list[Any]): The list to flatten.

        Returns:
            list[Any]: The flattened list.
        """
        flattened = []
        for item in lst:
            if isinstance(item, list):
                flattened.extend(_flatten(item))
            else:
                flattened.append(item)
        return flattened

    return _flatten(matrix)


def filter_list(
    items: list[str] | None,
    allowlist: list[str] | None = None,
    denylist: list[str] | None = None,
) -> list[str]:
    """Filters a list based on allowlist and denylist.

    Args:
        items (list[str] | None): The list to filter.
        allowlist (list[str] | None): The list of allowed items.
        denylist (list[str] | None): The list of denied items.

    Returns:
        list[str]: The filtered list.
    """
    if items is None:
        items = []

    allowlist_provided = allowlist is not None
    allowlist = allowlist or []
    denylist = denylist or []

    allowed_set = set(allowlist)
    denied_set = set(denylist)

    enforce_allowlist = allowlist_provided and bool(allowed_set)

    filtered = []

    for elem in items:
        if enforce_allowlist and elem not in allowed_set:
            continue

        if elem in denied_set:
            continue

        filtered.append(elem)

    return filtered
