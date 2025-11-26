"""This module provides utilities for handling maps (dictionaries).

It includes functions to manipulate, flatten, filter, and deeply merge
dictionaries, and to convert keys from camelCase to snake_case.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping, MutableMapping
from typing import Any, TypeVar

import inflection

from deepmerge import Merger
from sortedcontainers import SortedDict

from .type_utils import convert_special_types


# Default merger configuration:
# - Lists: append elements
# - Dicts: recursively merge
# - Sets: union
# - Fallback: override with newer value
_DEFAULT_MERGER = Merger(
    type_strategies=[
        (list, ["append"]),
        (dict, ["merge"]),
        (set, ["union"]),
    ],
    fallback_strategies=["override"],
    type_conflict_strategies=["override"],
)


def deep_merge(*mappings: Mapping[str, Any]) -> dict[str, Any]:
    """Deeply merge multiple mappings into a single dictionary.

    This function recursively merges dictionaries, with later values taking
    precedence over earlier ones. Lists are appended, sets are unioned, and
    other types are overridden.

    Args:
        *mappings: Variable number of mappings to merge. Later mappings
            take precedence over earlier ones.

    Returns:
        A new dictionary containing the deeply merged result.

    Example:
        >>> a = {"x": {"y": 1}, "list": [1, 2]}
        >>> b = {"x": {"z": 2}, "list": [3]}
        >>> deep_merge(a, b)
        {'x': {'y': 1, 'z': 2}, 'list': [1, 2, 3]}
    """
    result: dict[str, Any] = {}
    for mapping in mappings:
        if mapping:
            result = _DEFAULT_MERGER.merge(result, dict(mapping))
    return result


def create_merger(
    list_strategy: str = "append",
    dict_strategy: str = "merge",
    set_strategy: str = "union",
    fallback_strategy: str = "override",
    type_conflict_strategy: str = "override",
) -> Merger:
    """Create a custom Merger instance with specified strategies.

    This factory function allows creating mergers with different behaviors
    for combining data structures.

    Args:
        list_strategy: Strategy for merging lists. Options: "append", "override".
        dict_strategy: Strategy for merging dicts. Options: "merge", "override".
        set_strategy: Strategy for merging sets. Options: "union", "override".
        fallback_strategy: Default strategy for unhandled types.
        type_conflict_strategy: Strategy when types conflict.

    Returns:
        A configured Merger instance.

    Example:
        >>> merger = create_merger(list_strategy="override")
        >>> merger.merge({"a": [1]}, {"a": [2]})
        {'a': [2]}
    """
    return Merger(
        type_strategies=[
            (list, [list_strategy]),
            (dict, [dict_strategy]),
            (set, [set_strategy]),
        ],
        fallback_strategies=[fallback_strategy],
        type_conflict_strategies=[type_conflict_strategy],
    )


def first_non_empty_value_from_map(m: Mapping[str, Any], *keys: str) -> Any:
    """Returns the first non-empty value from a map for the given keys.

    Args:
        m (Mapping[str, Any]): The map to search.
        keys: The keys to search for.

    Returns:
        Any: The first non-empty value.
    """
    for key in keys:
        if m.get(key):
            return m[key]
    return None


def deduplicate_map(m: Mapping[str, Any]) -> dict[str, Any]:
    """Removes duplicate values from a map.

    Args:
        m (Mapping[str, Any]): The map to deduplicate.

    Returns:
        dict[str, Any]: The deduplicated map.
    """
    deduplicated_map: dict[str, Any] = convert_special_types(m)

    for k, v in m.items():
        if isinstance(v, list):
            # Try using dict.fromkeys for hashable elements (more efficient)
            # Fall back to manual deduplication for unhashable elements
            try:
                deduplicated_map[k] = list(dict.fromkeys(v))
            except TypeError:
                # Handle unhashable elements (e.g., dicts, lists) with manual deduplication
                deduplicated_list = []
                for elem in v:
                    if elem not in deduplicated_list:
                        deduplicated_list.append(elem)
                deduplicated_map[k] = deduplicated_list
            continue

        if isinstance(v, Mapping):
            deduplicated_map[k] = deduplicate_map(v)
            continue

        if k not in deduplicated_map:
            deduplicated_map[k] = v

    return deduplicated_map


def all_values_from_map(m: Mapping[str, Any]) -> list[Any]:
    """Returns all values from a nested map.

    Args:
        m (Mapping[str, Any]): The map to retrieve values from.

    Returns:
        List[Any]: A list of all values.
    """
    values = []

    for v in m.values():
        if isinstance(v, Mapping):
            values.extend(all_values_from_map(v))
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, Mapping):
                    values.extend(all_values_from_map(item))
                else:
                    values.append(item)
        else:
            values.append(v)

    return values


def flatten_map(
    dictionary: Mapping[str, Any],
    parent_key: str | None = "",
    separator: str = ".",
) -> dict[str, Any]:
    """Flattens a nested dictionary into a flat dictionary.

    Args:
        dictionary (Mapping[str, Any]): The dictionary to flatten.
        parent_key (Optional[str]): The string to prepend to dictionary's keys.
        separator (str): The string used to separate flattened keys.

    Returns:
        Dict[str, Any]: The flattened dictionary.
    """
    items: list[tuple[str, Any]] = []
    for key, value in dictionary.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else key
        if isinstance(value, MutableMapping):
            items.extend(flatten_map(value, new_key, separator).items())
        elif isinstance(value, list):
            for k, v in enumerate(value):
                items.extend(flatten_map({str(k): v}, new_key).items())
        else:
            items.append((new_key, value))
    return dict(items)


def zipmap(a: list[str], b: list[str]) -> dict[str, str]:
    """Creates a dictionary from two lists by zipping them together.

    Args:
        a (List[str]): The first list.
        b (List[str]): The second list.

    Returns:
        Dict[str, str]: The resulting dictionary.
    """
    zipped = {}

    for idx, val in enumerate(a):
        if idx >= len(b):
            break

        zipped[val] = b[idx]

    return zipped


KT = TypeVar("KT")
VT = TypeVar("VT")


class SortedDefaultDict(defaultdict[KT, VT], SortedDict[KT, VT]):  # type: ignore[misc]
    """A dictionary that combines :class:`collections.defaultdict` and :class:`sortedcontainers.SortedDict` functionality.

    This class inherits from both :class:`collections.defaultdict` and :class:`sortedcontainers.SortedDict`,
    providing a dictionary that both automatically creates values for missing keys and maintains
    its keys in sorted order.

    The sorting behavior is inherited from :class:`sortedcontainers.SortedDict`, while the default value behavior
    comes from :class:`collections.defaultdict`. When keys are accessed that don't exist, the
    default_factory is called to create a value, just like a regular :class:`collections.defaultdict`.

    Args:
        default_factory (Callable[[], VT] | None): A callable that provides the default value for missing keys.
            If None, attempts to access missing keys will raise KeyError.

    Example:
        >>> d = SortedDefaultDict(list)
        >>> d['c'].append(3)
        >>> d['a'].append(1)
        >>> d['b'].append(2)
        >>> list(d.keys())
        ['a', 'b', 'c']
        >>> d['d']  # Creates new list automatically
        []
    """

    def __init__(self, default_factory: Callable[[], VT] | None = None) -> None:
        """Initialize a new SortedDefaultDict.

        Args:
            default_factory: Callable that provides the default value for missing keys.
                When a key is accessed that doesn't exist, this callable is invoked
                without arguments to provide the missing value. If None, accessing a
                missing key raises a KeyError.

        Raises:
            TypeError: If default_factory is not callable or None.
        """
        defaultdict.__init__(self, default_factory)
        SortedDict.__init__(self)


def get_default_dict(
    use_sorted_dict: bool = False,
    default_type: type[dict[Any, Any]] = dict,
    levels: int = 2,
) -> defaultdict[str, Any] | Any:
    """Create a nested `defaultdict` with the specified number of levels.

    Args:
        use_sorted_dict (bool): Whether to use a sorted dictionary.
        default_type (type): The default type for the dictionary.
        levels (int): The number of levels for nesting.

    Returns:
        defaultdict | Any: A nested `defaultdict` or a dictionary of the specified type.

    Raises:
        ValueError: If levels is less than 1.
    """
    if levels < 1:
        error_message = "The number of levels must be greater than or equal to 1."
        raise ValueError(error_message)

    dict_type = SortedDict if use_sorted_dict else default_type

    if levels == 1:
        return dict_type()

    if use_sorted_dict:
        return defaultdict(SortedDefaultDict)

    def nested_dict() -> defaultdict[str, Any]:
        return defaultdict(nested_dict)

    return nested_dict()


def unhump_map(
    m: Mapping[str, Any],
    drop_without_prefix: str | None = None,
) -> dict[str, Any]:
    """Converts keys in a dictionary from camelCase to snake_case.

    Args:
        m (Mapping[str, Any]): The dictionary to convert.
        drop_without_prefix (Optional[str]): Drop keys without this prefix.

    Returns:
        Dict[str, Any]: The converted dictionary.
    """
    unhumped = {}

    for k, v in m.items():
        if drop_without_prefix is not None and not k.startswith(drop_without_prefix):
            continue

        unhumped_key = inflection.underscore(k)

        if isinstance(v, Mapping):
            unhumped[unhumped_key] = unhump_map(
                v, drop_without_prefix=drop_without_prefix
            )
            continue

        unhumped[unhumped_key] = v

    return unhumped


def filter_map(
    m: Mapping[str, Any] | None,
    allowlist: list[str] | None = None,
    denylist: list[str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Filters a map based on allowlist and denylist.

    Args:
        m (Optional[Mapping[str, Any]]): The map to filter.
        allowlist (List[str]): The list of allowed keys.
        denylist (List[str]): The list of denied keys.

    Returns:
        tuple[Dict[str, Any], Dict[str, Any]]: The filtered and remaining maps.
    """
    if m is None:
        m = {}

    if allowlist is None:
        allowlist = []

    if denylist is None:
        denylist = []

    fm = {}
    rm = {}

    for k, v in m.items():
        if (len(allowlist) > 0 and k not in allowlist) or k in denylist:
            rm[k] = v
        else:
            fm[k] = v

    return fm, rm
