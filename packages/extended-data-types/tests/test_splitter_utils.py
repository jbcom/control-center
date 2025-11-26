"""This module contains test functions for verifying the functionality of utility functions
in `splitter_utils` for splitting lists and dictionaries by the type of their elements.

Functions:
    - test_split_list_by_type: Tests splitting a list by the type of its items.
    - test_split_list_by_type_empty: Tests splitting an empty list.
    - test_split_dict_by_type: Tests splitting a dictionary by the type of its values.
    - test_split_dict_by_type_empty: Tests splitting an empty dictionary.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import pytest

from extended_data_types.splitter_utils import split_dict_by_type, split_list_by_type


@pytest.mark.parametrize(
    ("input_list", "expected_output"),
    [
        (
            [1, "a", 2.5, "b", 3, 4.0, None],
            defaultdict(
                list,
                {int: [1, 3], str: ["a", "b"], float: [2.5, 4.0], type(None): [None]},
            ),
        ),
        (
            [True, 1, "string", 2.5],
            defaultdict(list, {bool: [True], int: [1], str: ["string"], float: [2.5]}),
        ),
    ],
)
def test_split_list_by_type(
    input_list: list[Any], expected_output: defaultdict[type, list[Any]]
) -> None:
    """Tests splitting a list by the type of its items.

    Args:
        input_list (List[Any]): The list to split.
        expected_output (DefaultDict[Type, List[Any]]): The expected output categorized by type.

    Asserts:
        The result of split_list_by_type matches the expected defaultdict with lists of elements categorized by their type.
    """
    result = split_list_by_type(input_list)
    assert result == expected_output


def test_split_list_by_type_empty() -> None:
    """Tests splitting an empty list.

    Asserts:
        The result of split_list_by_type is an empty defaultdict.
    """
    input_list: list[Any] = []
    expected_output = defaultdict(list)

    result = split_list_by_type(input_list)
    assert result == expected_output


@pytest.mark.parametrize(
    ("input_dict", "expected_output"),
    [
        (
            {"a": 1, "b": "string", "c": 3.5, "d": 2, "e": None},
            defaultdict(
                dict,
                {
                    int: {"a": 1, "d": 2},
                    str: {"b": "string"},
                    float: {"c": 3.5},
                    type(None): {"e": None},
                },
            ),
        ),
        (
            {1: True, 2: False, 3: None, 4: "yes"},
            defaultdict(
                dict,
                {bool: {1: True, 2: False}, type(None): {3: None}, str: {4: "yes"}},
            ),
        ),
    ],
)
def test_split_dict_by_type(
    input_dict: dict[Any, Any], expected_output: defaultdict[type, dict[Any, Any]]
) -> None:
    """Tests splitting a dictionary by the type of its values.

    Args:
        input_dict (Dict[Any, Any]): The dictionary to split.
        expected_output (DefaultDict[Type, Dict[Any, Any]]): The expected output categorized by type.

    Asserts:
        The result of split_dict_by_type matches the expected defaultdict with dictionaries of elements categorized by their type.
    """
    result = split_dict_by_type(input_dict)
    assert result == expected_output


def test_split_dict_by_type_empty() -> None:
    """Tests splitting an empty dictionary.

    Asserts:
        The result of split_dict_by_type is an empty defaultdict.
    """
    input_dict: dict[Any, Any] = {}
    expected_output = defaultdict(dict)

    result = split_dict_by_type(input_dict)
    assert result == expected_output
