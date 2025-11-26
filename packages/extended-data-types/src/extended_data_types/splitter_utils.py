"""This module contains utility functions for splitting lists and dictionaries by the type of their items.

It includes functions `split_list_by_type` and `split_dict_by_type` which categorize elements
based on their type and return defaultdict of type list or dict respectively.

Functions:
    - split_list_by_type: Splits a list by the type of its items.
    - split_dict_by_type: Splits a dictionary by the type of its values.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .type_utils import typeof


def split_list_by_type(
    input_list: list[Any], primitive_only: bool = False
) -> defaultdict[type, list[Any]]:
    """Split a list by the type of its items, with an option to categorize by primitive types only.

    Args:
        input_list (List[Any]): The list to split.
        primitive_only (bool): If True, categorize items based on primitive types (int, float, str, etc.)
        rather than their exact type.

    Returns:
        DefaultDict[type, List[Any]]: A defaultdict storing lists of elements categorized by their type.
    """
    result: defaultdict[type, list[Any]] = defaultdict(list)
    for item in input_list:
        result[typeof(item, primitive_only=primitive_only)].append(item)
    return result


def split_dict_by_type(
    input_dict: dict[Any, Any], primitive_only: bool = False
) -> defaultdict[type, dict[Any, Any]]:
    """Split a dictionary by the type of its values, with an option to categorize by primitive types only.

    Args:
        input_dict (Dict[Any, Any]): The dictionary to split.
        primitive_only (bool): If True, categorize values based on primitive types (int, float, str, etc.)
        rather than their exact type.

    Returns:
        DefaultDict[type, Dict[Any, Any]]: A defaultdict storing dictionaries of elements categorized by their type.
    """
    result: defaultdict[type, dict[Any, Any]] = defaultdict(dict)
    for key, value in input_dict.items():
        result[typeof(value, primitive_only=primitive_only)][key] = value
    return result
