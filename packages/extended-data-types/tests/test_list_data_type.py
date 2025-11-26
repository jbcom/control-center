"""This module contains test functions for verifying the functionality of list operations using the
`extended_data_types` package. It includes fixtures for nested lists, flat lists, and test lists with allowlists and
denylists, and tests for flattening and filtering lists.

Fixtures:
    - nested_list: Provides a nested list for testing.
    - flat_list: Provides the expected flat list for testing.
    - test_list: Provides a sample list of strings for testing.
    - allowlist: Provides a list of allowed items for filtering.
    - denylist: Provides a list of denied items for filtering.
    - allowlist_and_denylist: Provides both allowlist and denylist for combined filtering.

Functions:
    - test_flatten_list: Tests flattening of a nested list.
    - test_filter_list_allowlist: Tests filtering a list with an allowlist.
    - test_filter_list_denylist: Tests filtering a list with a denylist.
    - test_filter_list_allowlist_and_denylist: Tests filtering a list with both allowlist and denylist.
    - test_filter_list_none_input: Tests filtering with None as input.
"""

from __future__ import annotations

import pytest

from extended_data_types.list_data_type import filter_list, flatten_list


@pytest.fixture
def nested_list() -> list[list[int]]:
    """Provides a nested list for testing.

    Returns:
        list[list[int]]: A nested list of integers.
    """
    return [[1, 2, 3], [4, 5, 6], [7, 8, 9]]


@pytest.fixture
def flat_list() -> list[int]:
    """Provides the expected flat list for testing.

    Returns:
        list[int]: A flat list of integers.
    """
    return [1, 2, 3, 4, 5, 6, 7, 8, 9]


@pytest.fixture
def test_list() -> list[str]:
    """Provides a sample list of strings for testing.

    Returns:
        list[str]: A sample list of strings.
    """
    return ["apple", "banana", "cherry", "date"]


@pytest.fixture
def allowlist() -> list[str]:
    """Provides a list of allowed items for filtering.

    Returns:
        list[str]: A list of allowed items.
    """
    return ["apple", "cherry"]


@pytest.fixture
def denylist() -> list[str]:
    """Provides a list of denied items for filtering.

    Returns:
        list[str]: A list of denied items.
    """
    return ["banana", "date"]


@pytest.fixture
def allowlist_and_denylist() -> dict[str, list[str]]:
    """Provides both allowlist and denylist for combined filtering.

    Returns:
        dict[str, list[str]]: A dictionary containing both allowlist and denylist.
    """
    return {"allowlist": ["apple", "cherry", "date"], "denylist": ["date"]}


def test_flatten_list(nested_list: list[list[int]], flat_list: list[int]) -> None:
    """Tests flattening of a nested list.

    Args:
        nested_list (list[list[int]]): A nested list provided by the fixture.
        flat_list (list[int]): The expected flat list provided by the fixture.

    Asserts:
        The result of flatten_list matches the expected flat list.
    """
    result = flatten_list(nested_list)
    assert result == flat_list


def test_filter_list_allowlist(test_list: list[str], allowlist: list[str]) -> None:
    """Tests filtering a list with an allowlist.

    Args:
        test_list (list[str]): A sample list of strings provided by the fixture.
        allowlist (list[str]): A list of allowed items provided by the fixture.

    Asserts:
        The result of filter_list matches the expected filtered list with allowed items.
    """
    result = filter_list(test_list, allowlist=allowlist)
    assert result == ["apple", "cherry"]


def test_filter_list_empty_allowlist_behaves_like_no_filter(
    test_list: list[str],
) -> None:
    """An explicitly empty allowlist should allow every item."""
    result = filter_list(test_list, allowlist=[])
    assert result == test_list


def test_filter_list_denylist(test_list: list[str], denylist: list[str]) -> None:
    """Tests filtering a list with a denylist.

    Args:
        test_list (list[str]): A sample list of strings provided by the fixture.
        denylist (list[str]): A list of denied items provided by the fixture.

    Asserts:
        The result of filter_list matches the expected filtered list with denied items removed.
    """
    result = filter_list(test_list, denylist=denylist)
    assert result == ["apple", "cherry"]


def test_filter_list_allowlist_and_denylist(
    test_list: list[str], allowlist_and_denylist: dict[str, list[str]]
) -> None:
    """Tests filtering a list with both allowlist and denylist.

    Args:
        test_list (list[str]): A sample list of strings provided by the fixture.
        allowlist_and_denylist (dict[str, list[str]]): A dictionary containing both allowlist and denylist provided by the fixture.

    Asserts:
        The result of filter_list matches the expected filtered list with allowed items included and denied items removed.
    """
    result = filter_list(
        test_list,
        allowlist=allowlist_and_denylist["allowlist"],
        denylist=allowlist_and_denylist["denylist"],
    )
    assert result == ["apple", "cherry"]


def test_filter_list_none_input() -> None:
    """Tests filtering with None as input.

    Asserts:
        The result of filter_list with None input is an empty list.
    """
    result = filter_list(None)
    assert result == []
