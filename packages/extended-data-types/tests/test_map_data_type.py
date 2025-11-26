"""This module contains test functions for verifying the functionality of various map (dictionary) operations using the
`extended_data_types` package. It includes fixtures for sample maps and lists, and tests for filtering, flattening,
deduplicating, and other map manipulations.

Fixtures:
    - test_map: Provides a sample map with nested structures for testing.
    - duplicated_map: Provides a map with duplicate values for testing deduplication.
    - test_keys: Provides a list of keys for testing.
    - flattened_map: Provides the expected flat map for testing.
    - a_list: Provides a sample list of strings for testing zipmap.
    - b_list: Provides another sample list of strings for testing zipmap.
    - zipmap_result: Provides the expected result of the zipmap operation.
    - camel_case_map: Provides a sample map with camelCase keys for testing unhump_map.
    - snake_case_map: Provides the expected snake_case map after unhump_map.
    - filter_map_data: Provides a sample map for testing filter_map.
    - allowlist: Provides a list of allowed keys for filter_map.
    - denylist: Provides a list of denied keys for filter_map.

Functions:
    - test_first_non_empty_value_from_map: Tests finding the first non-empty value from a map given a list of keys.
    - test_deduplicate_map: Tests deduplication of map values.
    - test_all_values_from_map: Tests retrieving all values from a map.
    - test_flatten_map: Tests flattening of a nested map.
    - test_zipmap: Tests the zipmap operation for combining two lists into a map.
    - test_get_default_dict: Tests creation of a default dictionary.
    - test_get_default_dict_sorted: Tests creation of a sorted default dictionary.
    - test_unhump_map: Tests converting camelCase keys to snake_case.
    - test_filter_map: Tests filtering a map using allowlist and denylist.
"""

from __future__ import annotations

from collections import defaultdict

import pytest

from extended_data_types.map_data_type import (
    all_values_from_map,
    deduplicate_map,
    filter_map,
    first_non_empty_value_from_map,
    flatten_map,
    get_default_dict,
    unhump_map,
    zipmap,
)


@pytest.fixture
def test_map() -> dict:
    """Provides a sample map with nested structures for testing.

    Returns:
        dict: A sample map.
    """
    return {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3",
        "list": [1, 2, 3, {"key": "value"}],
        "nested": {"nested_key1": "nested_value1", "nested_key2": "nested_value2"},
    }


@pytest.fixture
def duplicated_map() -> dict:
    """Provides a map with duplicate values for testing deduplication.

    Returns:
        dict: A map with duplicate values.
    """
    return {
        "key1": ["value1", "value1", "value2"],
        "key2": {"subkey1": "value1", "subkey2": "value2"},
        "key3": "value3",
    }


@pytest.fixture
def test_keys() -> list[str]:
    """Provides a list of keys for testing.

    Returns:
        list[str]: A list of keys.
    """
    return ["key2", "key4", "key1"]


@pytest.fixture
def flattened_map() -> dict:
    """Provides the expected flat map for testing.

    Returns:
        dict: The expected flat map.
    """
    return {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3",
        "list.0": 1,
        "list.1": 2,
        "list.2": 3,
        "list.3.key": "value",
        "nested.nested_key1": "nested_value1",
        "nested.nested_key2": "nested_value2",
    }


@pytest.fixture
def a_list() -> list[str]:
    """Provides a sample list of strings for testing zipmap.

    Returns:
        list[str]: A sample list of strings.
    """
    return ["a", "b", "c"]


@pytest.fixture
def b_list() -> list[str]:
    """Provides another sample list of strings for testing zipmap.

    Returns:
        list[str]: A sample list of strings.
    """
    return ["1", "2", "3"]


@pytest.fixture
def zipmap_result() -> dict:
    """Provides the expected result of the zipmap operation.

    Returns:
        dict: The expected result of zipmap.
    """
    return {"a": "1", "b": "2", "c": "3"}


@pytest.fixture
def camel_case_map() -> dict:
    """Provides a sample map with camelCase keys for testing unhump_map.

    Returns:
        dict: A sample map with camelCase keys.
    """
    return {
        "camelCaseKey": "value1",
        "anotherCamelCase": {"nestedCamelCaseKey": "nested_value1"},
        "withoutPrefix": "value2",
    }


@pytest.fixture
def snake_case_map() -> dict:
    """Provides the expected snake_case map after unhump_map.

    Returns:
        dict: The expected snake_case map.
    """
    return {
        "camel_case_key": "value1",
        "another_camel_case": {"nested_camel_case_key": "nested_value1"},
    }


@pytest.fixture
def filter_map_data() -> dict:
    """Provides a sample map for testing filter_map.

    Returns:
        dict: A sample map for filtering.
    """
    return {
        "allowed1": "value1",
        "allowed2": "value2",
        "denied1": "value3",
        "denied2": "value4",
    }


@pytest.fixture
def allowlist() -> list[str]:
    """Provides a list of allowed keys for filter_map.

    Returns:
        list[str]: A list of allowed keys.
    """
    return ["allowed1", "allowed2"]


@pytest.fixture
def denylist() -> list[str]:
    """Provides a list of denied keys for filter_map.

    Returns:
        list[str]: A list of denied keys.
    """
    return ["denied1", "denied2"]


def test_first_non_empty_value_from_map(test_map: dict, test_keys: list[str]) -> None:
    """Tests finding the first non-empty value from a map given a list of keys.

    Args:
        test_map (dict): A sample map provided by the fixture.
        test_keys (list[str]): A list of keys provided by the fixture.

    Asserts:
        The result of first_non_empty_value_from_map matches the expected value.
    """
    result = first_non_empty_value_from_map(test_map, *test_keys)
    assert result == "value2"


def test_deduplicate_map(duplicated_map: dict) -> None:
    """Tests deduplication of map values.

    Args:
        duplicated_map (dict): A map with duplicate values provided by the fixture.

    Asserts:
        The result of deduplicate_map matches the expected deduplicated map.
    """
    result = deduplicate_map(duplicated_map)
    assert result == {
        "key1": ["value1", "value2"],
        "key2": {"subkey1": "value1", "subkey2": "value2"},
        "key3": "value3",
    }


def test_deduplicate_map_with_unhashable_elements() -> None:
    """Tests deduplication of map values containing unhashable elements.

    Asserts:
        The result of deduplicate_map correctly handles lists containing dicts and nested lists.
    """
    test_map = {
        "key1": [{"a": 1}, {"a": 1}, {"b": 2}],
        "key2": [["x", "y"], ["x", "y"], ["z"]],
        "key3": [{"a": 1}, "string", {"a": 1}, "string"],
    }
    result = deduplicate_map(test_map)

    # Note: dict equality works even though dicts are unhashable
    assert result == {
        "key1": [{"a": 1}, {"b": 2}],
        "key2": [["x", "y"], ["z"]],
        "key3": [{"a": 1}, "string"],
    }


def test_all_values_from_map(test_map: dict) -> None:
    """Tests retrieving all values from a map.

    Args:
        test_map (dict): A sample map provided by the fixture.

    Asserts:
        The result of all_values_from_map matches the expected list of all values.
    """
    result = all_values_from_map(test_map)
    assert result == [
        "value1",
        "value2",
        "value3",
        1,
        2,
        3,
        "value",
        "nested_value1",
        "nested_value2",
    ]


def test_flatten_map(test_map: dict, flattened_map: dict) -> None:
    """Tests flattening of a nested map.

    Args:
        test_map (dict): A sample nested map provided by the fixture.
        flattened_map (dict): The expected flat map provided by the fixture.

    Asserts:
        The result of flatten_map matches the expected flat map.
    """
    result = flatten_map(test_map)
    assert result == flattened_map


def test_zipmap(a_list: list[str], b_list: list[str], zipmap_result: dict) -> None:
    """Tests the zipmap operation for combining two lists into a map.

    Args:
        a_list (list[str]): The first list of strings provided by the fixture.
        b_list (list[str]): The second list of strings provided by the fixture.
        zipmap_result (dict): The expected result of zipmap provided by the fixture.

    Asserts:
        The result of zipmap matches the expected map.
    """
    result = zipmap(a_list, b_list)
    assert result == zipmap_result


def test_get_default_dict() -> None:
    """Tests creation of a default dictionary.

    Asserts:
        - The default dictionary can have nested keys assigned.
        - The nested levels match the expected structure.
        - Default type at the final level is a standard dictionary.
    """
    result = get_default_dict()
    result["key"]["subkey"] = "value"

    assert result["key"]["subkey"] == "value"
    assert isinstance(result["key"], dict)
    assert isinstance(
        result["key"]["subkey"], str
    )  # Final level contains the assigned value.


def test_get_default_dict_sorted() -> None:
    """Tests creation of a sorted default dictionary.

    Asserts:
        - The sorted default dictionary can have nested keys assigned.
        - Keys maintain sorted order when using SortedDict.
        - Nested levels use defaultdict with SortedDict.
    """
    from sortedcontainers import SortedDict

    # Test single level
    result_single = get_default_dict(use_sorted_dict=True, levels=1)
    result_single["c"] = 3
    result_single["a"] = 1
    result_single["b"] = 2

    # Keys should be in sorted order
    assert list(result_single.keys()) == ["a", "b", "c"]
    assert isinstance(result_single, SortedDict)

    # Test multiple levels
    result_multi = get_default_dict(use_sorted_dict=True, levels=2)
    result_multi["key1"]["c"] = 3
    result_multi["key1"]["a"] = 1
    result_multi["key1"]["b"] = 2

    # Nested level should maintain sorted order
    assert list(result_multi["key1"].keys()) == ["a", "b", "c"]
    assert isinstance(result_multi, defaultdict)
    assert isinstance(result_multi["key1"], defaultdict)


def test_get_default_dict_multiple_levels() -> None:
    """Tests creation of a nested default dictionary with multiple levels.

    Asserts:
        - The number of nested levels matches the specified argument.
        - Nested keys can be assigned up to the specified level.
        - Final level uses the correct default type.
    """
    levels = 3
    result = get_default_dict(levels=levels)
    result["key1"]["key2"]["key3"] = "value"

    assert result["key1"]["key2"]["key3"] == "value"
    assert isinstance(
        result["key1"]["key2"], defaultdict
    )  # Intermediate levels are defaultdict.
    assert isinstance(
        result["key1"]["key2"]["key3"], str
    )  # Final level contains the assigned value.


def test_get_default_dict_single_level() -> None:
    """Test the creation of a default dictionary with a single level.

    Asserts:
        - A single-level dictionary does not create additional nesting.
        - The final level uses the correct default type.
    """
    result = get_default_dict(levels=1)
    result["key"] = {"inner_key": "value"}  # Create a dict instead of a set

    assert result["key"]["inner_key"] == "value"
    assert isinstance(result["key"], dict)  # Single-level uses the default type


def test_get_default_dict_with_custom_default_type() -> None:
    """Test the creation of a default dictionary with a custom default type.

    Asserts:
        - The dictionary is of the custom type.
        - The custom method `add` works as expected.
    """

    class CustomDict(dict):
        def add(self, key, value):
            self[key] = value

    result = get_default_dict(default_type=CustomDict, levels=1)
    result.add("key", "value")

    assert isinstance(result, CustomDict)
    assert result["key"] == "value"


def test_get_default_dict_invalid_levels() -> None:
    """Tests that an invalid level value raises an exception.

    Asserts:
        - A ValueError is raised when levels < 1.
    """
    with pytest.raises(
        ValueError, match=r"The number of levels must be greater than or equal to 1\."
    ):
        get_default_dict(levels=0)


def test_unhump_map(camel_case_map: dict) -> None:
    """Tests converting camelCase keys to snake_case.

    Args:
        camel_case_map (dict): A map with camelCase keys provided by the fixture.

    Asserts:
        The result of unhump_map matches the expected snake_case map.
    """
    result = unhump_map(camel_case_map, drop_without_prefix=None)
    assert result == {
        "camel_case_key": "value1",
        "another_camel_case": {"nested_camel_case_key": "nested_value1"},
        "without_prefix": "value2",
    }


def test_filter_map(
    filter_map_data: dict, allowlist: list[str], denylist: list[str]
) -> None:
    """Tests filtering a map using allowlist and denylist.

    Args:
        filter_map_data (dict): A sample map for filtering provided by the fixture.
        allowlist (list[str]): A list of allowed keys provided by the fixture.
        denylist (list[str]): A list of denied keys provided by the fixture.

    Asserts:
        The result of filter_map matches the expected filtered map and remaining map.
    """
    filtered, remaining = filter_map(
        filter_map_data,
        allowlist=allowlist,
        denylist=denylist,
    )
    assert filtered == {"allowed1": "value1", "allowed2": "value2"}
    assert remaining == {"denied1": "value3", "denied2": "value4"}
