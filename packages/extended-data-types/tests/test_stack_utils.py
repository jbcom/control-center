"""This module contains test functions for verifying the functionality of stack and method utilities using the
`extended_data_types` package. It includes tests for filtering methods, retrieving available methods from an instance,
and getting the caller of a function.

Fixtures:
    - methods_list: Provides a list of method names for testing.
    - dummy_instance: Provides an instance of DummyClass for testing.

Functions:
    - test_get_caller: Tests retrieving the caller of a function.
    - test_filter_methods: Tests filtering method names based on visibility and documentation.
    - test_get_available_methods: Tests retrieving available methods from an instance.
    - test_python_version_is_at_least: Tests the version check function.
"""

from __future__ import annotations

import sys

import pytest

from extended_data_types.stack_utils import (
    current_python_version_is_at_least,
    filter_methods,
    get_available_methods,
    get_caller,
    get_inputs_from_docstring,
    update_docstring,
)


def dummy_function() -> str:
    """A dummy function to test get_caller.

    Returns:
        str: The name of the caller function.
    """
    return get_caller()


class DummyClass:
    """A dummy class containing various methods to test method filtering."""

    def public_method(self) -> None:
        """This is a public method."""

    def _private_method(self) -> None:
        """This is a private method."""

    def __dunder_method(self) -> None:
        """This is a dunder method."""

    def public_method_no_doc(self) -> None:
        """A public method with no documentation."""

    def method_with_noparse(self) -> None:
        """NOPARSE This method should not be included."""


@pytest.fixture
def methods_list() -> list[str]:
    """Provides a list of method names for testing.

    Returns:
        list[str]: A list of method names.
    """
    return [
        "public_method",
        "_private_method",
        "__dunder_method",
        "public_method_no_doc",
        "method_with_noparse",
    ]


@pytest.fixture
def dummy_instance() -> DummyClass:
    """Provides an instance of DummyClass for testing.

    Returns:
        DummyClass: An instance of DummyClass.
    """
    return DummyClass()


def test_get_caller() -> None:
    """Tests retrieving the caller of a function.

    Asserts:
        The result of dummy_function matches the expected caller function name.
    """
    assert dummy_function() == "test_get_caller"


def test_filter_methods(methods_list: list[str]) -> None:
    """Tests filtering method names based on visibility and documentation.

    Args:
        methods_list (list[str]): A list of method names provided by the fixture.

    Asserts:
        The result of filter_methods matches the expected filtered list of method names.
    """
    filtered = filter_methods(methods_list)
    assert filtered == ["public_method", "public_method_no_doc", "method_with_noparse"]


def test_get_available_methods() -> None:
    """Tests retrieving available methods from a class.

    Asserts:
        The available methods in DummyClass match the expected methods and documentation.
    """
    available_methods = get_available_methods(DummyClass)
    assert "public_method" in available_methods
    assert "method_with_noparse" not in available_methods
    assert available_methods["public_method"] == "This is a public method."
    assert "public_method_no_doc" in available_methods
    assert (
        available_methods["public_method_no_doc"]
        == "A public method with no documentation."
    )


def test_get_inputs_from_docstring() -> None:
    """Tests extracting input details from a method's docstring.

    Asserts:
        Extracted inputs match the expected dictionary structure.
    """
    docstring = """
    env=name: API_KEY, required: true, sensitive: false
    env=name: DB_PASSWORD, required: true, sensitive: true
    env=name: USERNAME, required: false, sensitive: false
    """
    expected = {
        "api_key": {"required": "true", "sensitive": "false"},
        "db_password": {"required": "true", "sensitive": "true"},
        "username": {"required": "false", "sensitive": "false"},
    }

    result = get_inputs_from_docstring(docstring)
    assert result == expected


def test_get_inputs_from_docstring_empty() -> None:
    """Tests extracting input details from an empty docstring.

    Asserts:
        Extracted inputs are an empty dictionary.
    """
    docstring = ""
    expected = {}

    result = get_inputs_from_docstring(docstring)
    assert result == expected


def test_update_docstring() -> None:
    """Test updating a docstring with new input definitions.

    Asserts:
        - The updated docstring contains all new inputs in the correct format.
    """
    original_docstring = """
    env=name: API_KEY, required: true, sensitive: false
    """
    new_inputs = {
        "DB_PASSWORD": {"required": "true", "sensitive": "true"},
        "USERNAME": {"required": "false", "sensitive": "false"},
    }
    expected_docstring = """
    env=name: API_KEY, required: true, sensitive: false
    env=name: DB_PASSWORD, required: true, sensitive: true
    env=name: USERNAME, required: false, sensitive: false
    """

    result = update_docstring(original_docstring, new_inputs)
    assert result.strip() == expected_docstring.strip()


def test_update_docstring_idempotency() -> None:
    """Test that updating a docstring is idempotent.

    Asserts:
        - Repeated updates do not change the docstring further.
    """
    original_docstring = """
    env=name: API_KEY, required: true, sensitive: false
    env=name: DB_PASSWORD, required: true, sensitive: true
    """
    new_inputs = {
        "API_KEY": {"required": "true", "sensitive": "false"},
        "DB_PASSWORD": {"required": "true", "sensitive": "true"},
    }
    expected_docstring = """
    env=name: API_KEY, required: true, sensitive: false
    env=name: DB_PASSWORD, required: true, sensitive: true
    """

    result = update_docstring(original_docstring, new_inputs)
    assert result.strip() == expected_docstring.strip()


def test_python_version_is_at_least() -> None:
    """Tests the version check function.

    Asserts:
        The result of current_python_version_is_at_least matches the expected boolean value.
    """
    major, minor = sys.version_info.major, sys.version_info.minor

    # Test with the current version
    assert current_python_version_is_at_least(minor, major) is True
    assert current_python_version_is_at_least(minor + 1, major) is False
    assert current_python_version_is_at_least(minor, major + 1) is False

    # Test with a lower version
    assert current_python_version_is_at_least(0, 0) is True
    assert current_python_version_is_at_least(8, 3) is (sys.version_info >= (3, 8))
    assert current_python_version_is_at_least(8, 2) is True
    assert current_python_version_is_at_least(9, 3) is (sys.version_info >= (3, 9))
