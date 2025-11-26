"""This module contains test functions for verifying the functionality of string and collection matching utilities using
the `extended_data_types` package. It includes parameterized tests for partial matching, non-empty matching of
various types, and matching types to their primitive equivalents.

Functions:
    - test_is_partial_match: Tests partial matching of strings with optional prefix check.
    - test_is_non_empty_match: Tests non-empty matching of various types including strings, dictionaries, lists, and sets.
    - test_match_instance_type_to_primitive_type: Tests matching instance types to their primitive equivalents.
"""

from __future__ import annotations

import pytest

from extended_data_types.matcher_utils import is_non_empty_match, is_partial_match


@pytest.mark.parametrize(
    ("a", "b", "check_prefix_only", "expected"),
    [
        ("HelloWorld", "helloworld", False, True),
        ("Hello", "hello world", False, True),
        ("hello", "world", False, False),
        ("prefix", "pre", True, True),
        ("pre", "prefix", True, True),
        ("pre", "suffix", True, False),
    ],
)
def test_is_partial_match(
    a: str, b: str, check_prefix_only: bool, expected: bool
) -> None:
    """Tests partial matching of strings with optional prefix check.

    Args:
        a (str): The first string to compare.
        b (str): The second string to compare.
        check_prefix_only (bool): If True, only check if one string is a prefix of the other.
        expected (bool): The expected result of the partial match.

    Asserts:
        The result of is_partial_match matches the expected boolean value.
    """
    assert is_partial_match(a, b, check_prefix_only=check_prefix_only) == expected


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        ("Hello", "hello", True),
        ({"key": "value"}, {"key": "value"}, True),
        ({"key": "value"}, {"KEY": "VALUE"}, False),
        ([1, 2, 3], [3, 2, 1], True),
        ([1, 2], [1, 2, 3], False),
        (123, 123, True),
        (123, "123", False),
        (None, None, False),
    ],
)
def test_is_non_empty_match(a: any, b: any, expected: bool) -> None:
    """Tests non-empty matching of various types including strings, dictionaries, and lists.

    Args:
        a (any): The first item to compare.
        b (any): The second item to compare.
        expected (bool): The expected result of the non-empty match.

    Asserts:
        The result of is_non_empty_match matches the expected boolean value.
    """
    assert is_non_empty_match(a, b) == expected
