"""Test Suite for State Utilities.

This module contains tests for the `state_utils` functions from the `extended_data_types` package.
These functions are used to evaluate whether certain values or collections of values are considered
"nothing" (i.e., empty, None, or containing no meaningful data), and to extract non-empty values
from various inputs.

Functions Tested:
    - is_nothing: Determines if a single value is considered "nothing".
    - are_nothing: Checks if all values in a set of inputs are "nothing".
    - all_non_empty: Retrieves all non-empty elements from a collection of inputs.
    - first_non_empty: Finds the first non-empty value from a set of inputs.
    - any_non_empty: Retrieves any non-empty values from a mapping given a set of keys.
    - yield_non_empty: Yields non-empty values from a mapping.

Each test function provides specific scenarios to ensure the robustness and correctness of the
`state_utils` functions under various conditions.
"""

from __future__ import annotations

from typing import Any

import pytest

from extended_data_types.state_utils import (
    all_non_empty,
    any_non_empty,
    are_nothing,
    first_non_empty,
    is_nothing,
    yield_non_empty,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, True),
        ("", True),
        ({}, True),
        ([], True),
        ("   ", True),
        (0, False),
        ("non-empty", False),
        ([None, ""], True),
        ([1, 2], False),
    ],
)
def test_is_nothing(value: Any, expected: bool) -> None:
    """Tests determining if a value is considered "nothing".

    Args:
        value (Any): The value to check.
        expected (bool): The expected result indicating if the value is "nothing".

    Asserts:
        The result of is_nothing matches the expected boolean value.
    """
    assert is_nothing(value) == expected


@pytest.mark.parametrize(
    ("values", "kwargs", "expected"),
    [
        ((None, "", [], {}), {}, True),
        ((None, "value", 0, "another"), {}, False),
        ((1, 2, None), {}, False),
        (([], {"a": "A"}, [], {"b": "B"}), {}, False),
    ],
)
def test_are_nothing(
    values: tuple[Any, ...], kwargs: dict[str, Any], expected: bool
) -> None:
    """Tests determining if all values in a set of inputs are "nothing".

    Args:
        values (tuple): A tuple of values to check.
        kwargs (dict): A dictionary of keyword arguments to check.
        expected (bool): The expected result indicating if all values are "nothing".

    Asserts:
        The result of are_nothing matches the expected boolean value.
    """
    assert are_nothing(*values, **kwargs) == expected


@pytest.mark.parametrize(
    ("args", "kwargs", "expected"),
    [
        ((), {}, None),  # No inputs
        (["Hello", "", "World"], {}, ["Hello", "World"]),  # List with empty string
        (["Hello"], {"World": ""}, (["Hello"], {})),  # List and dict with empty string
        ([None, "", [], {}], {}, []),  # All "nothing" values
        ([1, 2, None], {}, [1, 2]),  # List with integers and None
        (
            [1, 2, None],
            {"key": "value"},
            ([1, 2], {"key": "value"}),
        ),  # Mixed args and kwargs
        (
            ["Hello"],
            {"key1": None, "key2": "World"},
            (["Hello"], {"key2": "World"}),
        ),  # Non-empty list and dict
        (
            [],
            {"key1": None, "key2": None},
            {},
        ),  # Empty list and dict with "nothing" values
        ([None, "", "Test"], {"key": None}, (["Test"], {})),  # Non-empty string in list
    ],
)
def test_all_non_empty(args, kwargs, expected):
    """Tests the all_non_empty function for various input scenarios.

    Args:
        args (tuple): Positional arguments to be passed to all_non_empty.
        kwargs (dict): Keyword arguments to be passed to all_non_empty.
        expected (Any): The expected result of calling all_non_empty with the provided args and kwargs.

    Scenarios Tested:
        - No inputs (empty args and kwargs): Should return None.
        - List with empty string: Should return a list with non-empty strings.
        - List and dict with empty string: Should return a tuple of non-empty list and dict.
        - List with all "nothing" values: Should return an empty list.
        - List with integers and None: Should return a list of non-empty integers.
        - Mixed args and kwargs: Should return a tuple of non-empty list and dict.
        - Non-empty list and dict: Should return a tuple of non-empty list and dict.
        - Empty list and dict with "nothing" values: Should return an empty dict.
        - Non-empty string in list: Should return a tuple with the non-empty string and an empty dict.

    Asserts:
        The result of all_non_empty matches the expected value.
    """
    result = all_non_empty(*args, **kwargs)
    assert result == expected, (
        f"Args: '{args}', Kwargs: '{kwargs}', Expected {expected}, got {result}"
    )


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        ((None, "", "value", "another"), "value"),
        ((None, "", [], {}), None),
        ((1, 2, None), 1),
    ],
)
def test_first_non_empty(values: tuple[Any, ...], expected: Any) -> None:
    """Tests retrieving the first non-empty value from a set of inputs.

    Args:
        values (tuple): A tuple of values to check.
        expected (Any): The expected first non-empty value.

    Asserts:
        The result of first_non_empty matches the expected first non-empty value.
    """
    assert first_non_empty(*values) == expected


@pytest.mark.parametrize(
    ("mapping", "keys", "expected"),
    [
        ({"key1": None, "key2": "value"}, ("key1", "key2"), {"key2": "value"}),
        ({"key1": None, "key2": None}, ("key1", "key2"), {}),
        ({"key1": "value1", "key2": "value2"}, ("key3", "key1"), {"key1": "value1"}),
    ],
)
def test_any_non_empty(
    mapping: dict[str, Any], keys: tuple[str, ...], expected: dict[str, Any]
) -> None:
    """Tests retrieving any non-empty values from a mapping given a set of keys.

    Args:
        mapping (dict): The mapping to check.
        keys (tuple): The keys to look for in the mapping.
        expected (dict): The expected mapping of non-empty values.

    Asserts:
        The result of any_non_empty matches the expected mapping of non-empty values.
    """
    assert any_non_empty(mapping, *keys) == expected


def test_yield_non_empty() -> None:
    """Tests yielding non-empty values from a mapping given a set of keys.

    Asserts:
        The result of yield_non_empty matches the expected list of non-empty mappings.
    """
    mapping = {"key1": None, "key2": "value", "key3": "another"}
    keys = ("key1", "key2", "key3")
    expected = [{"key2": "value"}, {"key3": "another"}]
    result = list(yield_non_empty(mapping, *keys))
    assert result == expected
