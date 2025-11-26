"""The state_utils module provides utility functions for handling and evaluating data structure "emptiness".

It includes functions to determine whether a value is considered "nothing", to extract
non-empty values, and to assess the state of provided arguments and keyword arguments.

Functions:
    - is_nothing: Determines if a value is considered "nothing" (e.g., None, empty string, empty list, empty dict).
    - are_nothing: Checks if all provided values (both positional and keyword arguments) are "nothing".
    - all_non_empty: Returns all non-empty values from provided arguments and keyword arguments.
    - all_non_empty_in_list: Returns a list of non-empty values from the provided list.
    - all_non_empty_in_dict: Returns a dictionary of non-empty values from the provided dictionary.
    - first_non_empty: Retrieves the first non-empty value from a set of provided values.
    - any_non_empty: Retrieves the first non-empty value from a mapping for a given set of keys.
    - yield_non_empty: Yields non-empty values from a mapping for a given set of keys.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Any


def is_nothing(v: Any) -> bool:
    """Checks if a value is considered 'nothing'.

    Args:
        v (Any): The value to check.

    Returns:
        bool: True if the value is considered 'nothing', False otherwise.
    """
    if v in [None, "", {}, []]:
        return True

    if str(v) == "" or str(v).isspace():
        return True

    if isinstance(v, (list, set)):
        v = [vv for vv in v if vv not in [None, "", {}, []]]
        if len(v) == 0:
            return True

    return False


def are_nothing(*args: Any, **kwargs: Any) -> bool:
    """Checks if all provided values (both args and kwargs) are considered 'nothing'.

    Args:
        args (Any): Positional arguments to check.
        kwargs (Any): Keyword arguments to check.

    Returns:
        bool: True if all values are considered 'nothing', False otherwise.
    """
    non_empty = all_non_empty(*args, **kwargs)

    if non_empty is None:
        return True

    if isinstance(non_empty, (list, dict)):
        return len(non_empty) == 0

    if isinstance(non_empty, tuple):
        list_part, dict_part = non_empty
        return len(list_part) == 0 and len(dict_part) == 0

    return False


def all_non_empty(
    *args: Any, **kwargs: Any
) -> list[Any] | dict[str, Any] | tuple[list[Any], dict[str, Any]] | None:
    """Returns all non-empty values from the provided args and kwargs.

    Args:
        args (Any): Positional arguments to check.
        kwargs (Any): Keyword arguments to check.

    Returns:
        Union[List[Any], Dict[str, Any], Tuple[List[Any], Dict[str, Any]], None]:
            A list, dict, tuple of list
    """
    if len(args) == 0 and len(kwargs) == 0:
        return None

    if len(args) == 0:
        return all_non_empty_in_dict(dict(kwargs))

    results = all_non_empty_in_list(list(args))
    if len(kwargs) == 0:
        return results

    return results, all_non_empty_in_dict(dict(kwargs))


def all_non_empty_in_list(input_list: list[Any]) -> list[Any]:
    """Returns a list of all non-empty values from the input list.

    Args:
        input_list (List[Any]): A list of items to check for emptiness.

    Returns:
        List: A list of non-empty values.
    """
    return [item for item in input_list if not is_nothing(item)]


def all_non_empty_in_dict(input_dict: dict[Any, Any]) -> dict[Any, Any]:
    """Returns a dictionary of all non-empty values from the input dictionary.

    Args:
        input_dict (Dict[Any, Any]): A dictionary of items to check for emptiness.

    Returns:
        Dict: A dictionary of non-empty values.
    """
    return {key: value for key, value in input_dict.items() if not is_nothing(value)}


def first_non_empty(*vals: Any) -> Any:
    """Returns the first non-empty value.

    Args:
        vals (Any): The values to check.

    Returns:
        Any: The first non-empty value, or None if all are 'nothing'.
    """
    non_empty_vals = all_non_empty(*vals)
    return (
        non_empty_vals[0]
        if isinstance(non_empty_vals, list) and non_empty_vals
        else None
    )


def any_non_empty(m: dict[Any, Any], *keys: Any) -> dict[Any, Any]:
    """Returns the first non-empty value from a mapping for the given keys.

    Args:
        m (Dict): The mapping to check.
        keys (Any): The keys to check.

    Returns:
        Dict[Any, Any]: A mapping containing the first non-empty value.
    """
    for k in keys:
        v = m.get(k)
        if not is_nothing(v):
            return {k: v}
    return {}


def yield_non_empty(
    m: dict[Any, Any], *keys: Any
) -> Generator[dict[Any, Any], None, None]:
    """Yields non-empty values from a mapping for the given keys.

    Args:
        m (Dict): The mapping to check.
        keys (Any): The keys to check.

    Yields:
        Generator[Dict[Any, Any], None, None]: A generator yielding non-empty values.
    """
    for k in keys:
        v = m.get(k)
        if not is_nothing(v):
            yield {k: v}
