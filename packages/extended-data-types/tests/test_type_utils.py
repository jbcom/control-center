"""Test suite for extended_data_types.type_utils module.

This module contains unit tests for various utility functions provided by
the type_utils module, ensuring correct functionality of type conversions,
special type handling, and error handling mechanisms.
"""

from __future__ import annotations

import datetime

from pathlib import Path
from typing import Any

import pytest

from extended_data_types.type_utils import (
    ConversionError,
    convert_special_type,
    convert_special_types,
    get_default_value_for_type,
    get_primitive_type_for_instance_type,
    make_hashable,
    reconstruct_special_type,
    reconstruct_special_types,
    strtobool,
    strtodate,
    strtodatetime,
    strtofloat,
    strtoint,
    strtopath,
    strtotime,
    typeof,
)


# Constants for expected test values
EXPECTED_FLOAT_1 = 3.14
EXPECTED_FLOAT_2 = 42.0
EXPECTED_INT_1 = 42
EXPECTED_INT_2 = 3


@pytest.fixture(params=[("yes", True), ("no", False), ("invalid", None)])
def strtobool_data(request: Any) -> tuple[str, bool | None]:
    """Provides data for testing strtobool function.

    Yields:
        tuple[str, bool | None]: A tuple containing the input string and the expected boolean or None result.
    """
    return request.param


@pytest.fixture(
    params=[("3.14", EXPECTED_FLOAT_1), ("42", EXPECTED_FLOAT_2), ("invalid", None)]
)
def strtofloat_data(request: Any) -> tuple[str, float | None]:
    """Provides data for testing strtofloat function.

    Yields:
        tuple[str, float | None]: A tuple containing the input value and the expected float or None result.
    """
    return request.param


@pytest.fixture(
    params=[("42", EXPECTED_INT_1), ("3.0", EXPECTED_INT_2), ("invalid", None)]
)
def strtoint_data(request: Any) -> tuple[str, int | None]:
    """Provides data for testing strtoint function.

    Yields:
        tuple[str, int | None]: A tuple containing the input value and the expected int or None result.
    """
    return request.param


@pytest.fixture(
    params=[
        ("/valid/path", Path("/valid/path")),
        (b"/valid/bytes/path", Path("/valid/bytes/path")),
        (None, None),
        (Path("/already/path"), Path("/already/path")),
    ]
)
def valid_path_data(request: Any) -> tuple[str | bytes | Path | None, Path | None]:
    """Provides valid input and expected output pairs for testing strtopath function.

    Yields:
        tuple[str | bytes | Path | None, Path | None]: A tuple containing the input value and the expected Path or None result.
    """
    return request.param


@pytest.fixture(
    params=[("invalid:://path", ValueError, True), (b"\x80invalid", ValueError, True)]
)
def invalid_path_data(request: Any) -> tuple[str | bytes, type[Exception], bool]:
    """Provides invalid input, expected exception type, and raise_on_error flag for testing strtopath.

    Yields:
        tuple[str | bytes, Type[Exception], bool]: A tuple containing the input value, expected exception type, and the raise_on_error flag.
    """
    return request.param


@pytest.fixture(params=["invalid:://path", b"\x80invalid"])
def silent_invalid_path_data(request: Any) -> str | bytes:
    """Provides invalid input values for testing strtopath when raise_on_error is False.

    Yields:
        str | bytes: The invalid input value to test.
    """
    return request.param


@pytest.fixture(
    params=[
        ("2023-09-05", datetime.date(2023, 9, 5)),
        ("2022-01-01", datetime.date(2022, 1, 1)),
        ("invalid-date", None),
    ]
)
def strtodate_data(request: Any) -> tuple[str, datetime.date | None]:
    """Provides data for testing strtodate function.

    Yields:
        tuple[str, datetime.date | None]: A tuple containing the input string and the expected date object or None.
    """
    return request.param


@pytest.fixture(
    params=[
        (
            "2023-09-05T12:30:00",
            datetime.datetime(2023, 9, 5, 12, 30, 0, tzinfo=datetime.timezone.utc),
        ),
        (
            "2023-09-05 12:30:00",
            datetime.datetime(2023, 9, 5, 12, 30, 0, tzinfo=datetime.timezone.utc),
        ),
        (
            "2023-09-05T12:30:00.123456",
            datetime.datetime(
                2023, 9, 5, 12, 30, 0, 123456, tzinfo=datetime.timezone.utc
            ),
        ),
        ("invalid-datetime", None),
    ]
)
def strtodatetime_data(request: Any) -> tuple[str, datetime.datetime | None]:
    """Provides data for testing strtodatetime function.

    Yields:
        tuple[str, datetime.datetime | None]: A tuple containing the input string and the expected datetime object or None.
    """
    return request.param


@pytest.fixture(
    params=[
        ("12:30:00", datetime.time(12, 30, 0)),
        ("12:30", datetime.time(12, 30, 0)),
        ("12:30:00.123456", datetime.time(12, 30, 0, 123456)),
        ("invalid-time", None),
    ]
)
def strtotime_data(request: Any) -> tuple[str, datetime.time | None]:
    """Provides data for testing strtotime function.

    Yields:
        tuple[str, datetime.time | None]: A tuple containing the input string and the expected time object or None.
    """
    return request.param


def test_strtobool(strtobool_data: tuple[str, bool | None]) -> None:
    """Tests converting a string to a boolean value.

    Args:
        strtobool_data (tuple[str, bool | None]): A fixture providing the input string and the expected boolean or None result.

    Asserts:
        The result of strtobool is True for truthy strings, False for falsy strings, and raises a ConversionError for invalid strings if specified.
    """
    val, expected = strtobool_data
    assert strtobool(val) == expected
    if expected is None and val == "invalid":
        with pytest.raises(
            ConversionError, match=r"Invalid <class 'bool'> value: 'invalid'"
        ):
            strtobool(val, raise_on_error=True)


def test_strtofloat(strtofloat_data: tuple[str, float | None]) -> None:
    """Tests converting a string to a float value.

    Args:
        strtofloat_data (tuple[str, float | None]): A fixture providing the input value and the expected float or None result.

    Asserts:
        The result of strtofloat matches the expected float value and raises a ConversionError for invalid strings if specified.
    """
    val, expected = strtofloat_data
    assert strtofloat(val) == expected
    if expected is None and val == "invalid":
        with pytest.raises(
            ConversionError, match=r"Invalid <class 'float'> value: 'invalid'"
        ):
            strtofloat(val, raise_on_error=True)


def test_strtoint(strtoint_data: tuple[str, int | None]) -> None:
    """Tests converting a string to an integer value.

    Args:
        strtoint_data (tuple[str, int | None]): A fixture providing the input value and the expected int or None result.

    Asserts:
        The result of strtoint matches the expected integer value and raises a ConversionError for invalid strings if specified.
    """
    val, expected = strtoint_data
    assert strtoint(val) == expected
    if expected is None and val == "invalid":
        with pytest.raises(
            ConversionError, match=r"Invalid <class 'int'> value: 'invalid'"
        ):
            strtoint(val, raise_on_error=True)


def test_strtopath(
    valid_path_data: tuple[str | bytes | Path | None, Path | None],
) -> None:
    """Tests the strtopath function for converting valid inputs into Path objects.

    Args:
        valid_path_data (tuple[str | bytes | Path | None, Path | None]): A fixture providing the input value and the expected Path or None result.

    Asserts:
        The result of strtopath matches the expected Path object or None.
    """
    value, expected = valid_path_data
    assert strtopath(value) == expected


def test_strtopath_invalid(
    invalid_path_data: tuple[str | bytes, type[Exception], bool],
) -> None:
    """Tests the strtopath function for handling invalid inputs that should raise exceptions.

    Args:
        invalid_path_data (tuple[str | bytes, Type[Exception], bool]): A fixture providing the input value, expected exception type, and the raise_on_error flag.

    Asserts:
        The strtopath function raises the expected exception with the correct error message when the raise_on_error flag is set to True.
    """
    value, expected_exception, raise_on_error = invalid_path_data
    with pytest.raises(
        expected_exception, match=r"Invalid <class 'pathlib.Path'> value"
    ):
        strtopath(value, raise_on_error=raise_on_error)


def test_strtopath_invalid_silent(silent_invalid_path_data: str | bytes) -> None:
    """Tests the strtopath function with invalid inputs when fail_silently is set to True.

    Args:
        silent_invalid_path_data (str | bytes): A fixture providing the invalid input value to test.

    Asserts:
        The strtopath function returns None when the input is invalid and the raise_on_error flag is False.
    """
    assert strtopath(silent_invalid_path_data) is None


def test_strtodate(strtodate_data: tuple[str, datetime.date | None]) -> None:
    """Tests converting a string to a date value.

    Args:
        strtodate_data (tuple[str, datetime.date | None]): A fixture providing the input string and the expected date object or None.

    Asserts:
        The result of strtodate matches the expected date value and raises a ConversionError for invalid strings if specified.
    """
    val, expected = strtodate_data
    assert strtodate(val) == expected
    if expected is None and val == "invalid-date":
        with pytest.raises(
            ConversionError,
            match=r"Invalid <class 'datetime.date'> value: 'invalid-date'",
        ):
            strtodate(val, raise_on_error=True)


def test_strtodatetime(
    strtodatetime_data: tuple[str, datetime.datetime | None],
) -> None:
    """Tests converting a string to a datetime value.

    Args:
        strtodatetime_data (tuple[str, datetime.datetime | None]): A fixture providing the input string and the expected datetime object or None.

    Asserts:
        The result of strtodatetime matches the expected datetime value and raises a ConversionError for invalid strings if specified.
    """
    val, expected = strtodatetime_data
    assert strtodatetime(val) == expected
    if expected is None and val == "invalid-datetime":
        with pytest.raises(
            ConversionError,
            match=r"Invalid <class 'datetime.datetime'> value: 'invalid-datetime'",
        ):
            strtodatetime(val, raise_on_error=True)


def test_strtotime(strtotime_data: tuple[str, datetime.time | None]) -> None:
    """Tests converting a string to a time value.

    Args:
        strtotime_data (tuple[str, datetime.time | None]): A fixture providing the input string and the expected time object or None.

    Asserts:
        The result of strtotime matches the expected time value and raises a ConversionError for invalid strings if specified.
    """
    val, expected = strtotime_data
    assert strtotime(val) == expected
    if expected is None and val == "invalid-time":
        with pytest.raises(
            ConversionError,
            match=r"Invalid <class 'datetime.time'> value: 'invalid-time'",
        ):
            strtotime(val, raise_on_error=True)


# Test for get_default_value_for_type function
@pytest.mark.parametrize(
    ("input_type", "expected"),
    [
        (list, []),
        (dict, {}),
        (str, ""),
        (int, None),
        (type(None), None),
    ],
)
def test_get_default_value_for_type(input_type: type, expected: Any) -> None:
    """Tests the default value returned for various types."""
    assert get_default_value_for_type(input_type) == expected


# Test for get_primitive_type_for_instance_type function
@pytest.mark.parametrize(
    ("value", "expected_type"),
    [
        (42, int),
        (3.14, float),
        (True, bool),
        ("hello", str),
        (b"bytes", bytes),
        ([1, 2, 3], list),
        ((1, 2, 3), list),
        ({"key": "value"}, dict),
        ({1, 2}, set),
        (None, type(None)),
        (object(), object),
    ],
)
def test_get_primitive_type_for_instance_type(value: Any, expected_type: type) -> None:
    """Tests the primitive type returned for various instance types."""
    assert get_primitive_type_for_instance_type(value) == expected_type


# Test for typeof function
@pytest.mark.parametrize(
    ("item", "primitive_only", "expected_type"),
    [
        (42, False, int),
        (42, True, int),
        ([1, 2, 3], False, list),
        ([1, 2, 3], True, list),
        ({"key": "value"}, False, dict),
        ({"key": "value"}, True, dict),
    ],
)
def test_typeof(item: Any, primitive_only: bool, expected_type: type) -> None:
    """Tests typeof function with and without primitive_only flag."""
    assert typeof(item, primitive_only) == expected_type


# Test for convert_special_type function
@pytest.mark.parametrize(
    ("obj", "expected"),
    [
        (datetime.date(2023, 9, 5), "2023-09-05"),
        (
            datetime.datetime(2023, 9, 5, 12, 30, tzinfo=datetime.timezone.utc),
            "2023-09-05T12:30:00",
        ),
        (Path("/some/path"), "/some/path"),
        ("simple string", "simple string"),
        (123, 123),
        (3.14, 3.14),
    ],
)
def test_convert_special_type(obj: Any, expected: Any) -> None:
    """Tests conversion of special types to simpler forms."""
    assert convert_special_type(obj) == expected


# Test for convert_special_types function
@pytest.mark.parametrize(
    ("obj", "expected"),
    [
        ({"date": datetime.date(2023, 9, 5)}, {"date": "2023-09-05"}),
        (
            [
                "/path/to/file",
                datetime.datetime(2023, 9, 5, 12, 30, tzinfo=datetime.timezone.utc),
            ],
            ["/path/to/file", "2023-09-05T12:30:00"],
        ),
        ({datetime.date(2023, 9, 5)}, ["2023-09-05"]),  # Update expected format to list
        (
            ["text", 123, {"key": Path("/some/path")}],
            ["text", 123, {"key": "/some/path"}],
        ),
    ],
)
def test_convert_special_types(obj: Any, expected: Any) -> None:
    """Tests conversion of nested special types to simpler forms."""
    assert convert_special_types(obj) == expected


@pytest.mark.parametrize(
    ("obj", "expected"),
    [
        ("2023-09-05", datetime.date(2023, 9, 5)),  # Date string to datetime.date
        (
            "2023-09-05T12:30:00",
            datetime.datetime(2023, 9, 5, 12, 30, tzinfo=datetime.timezone.utc),
        ),  # Datetime string to datetime.datetime
        ("/some/path", Path("/some/path")),  # Path string to Path
        ("simple string", "simple string"),  # Simple string remains unchanged
        ("123", 123),  # Numeric string to integer
        ("3.14", 3.14),  # Numeric string to float
        ("true", True),  # Boolean string to bool
        ("false", False),
        ("None", None),  # "None" string to NoneType
        ("", ""),  # Empty string remains unchanged
    ],
)
def test_reconstruct_special_type(obj: str, expected: Any) -> None:
    """Tests reconstruction of strings back into their original special types."""
    assert reconstruct_special_type(obj, fail_silently=False) == expected


# Test for reconstruct_special_types function
@pytest.mark.parametrize(
    ("obj", "expected"),
    [
        ({"date": "2023-09-05"}, {"date": datetime.date(2023, 9, 5)}),
        (
            ["/path/to/file", "2023-09-05T12:30:00"],
            [
                Path("/path/to/file"),
                datetime.datetime(2023, 9, 5, 12, 30, tzinfo=datetime.timezone.utc),
            ],
        ),
        (
            ["text", "123", {"key": "/some/path"}],
            ["text", 123, {"key": Path("/some/path")}],
        ),
        (
            ["2023-09-05", {"nested": ["2023-09-05T12:30:00"]}],
            [
                datetime.date(2023, 9, 5),
                {
                    "nested": [
                        datetime.datetime(
                            2023, 9, 5, 12, 30, tzinfo=datetime.timezone.utc
                        )
                    ]
                },
            ],
        ),
        (
            ["true", "false", "None"],
            [True, False, None],
        ),  # Test boolean and None reconstruction in a list
    ],
)
def test_reconstruct_special_types(obj: Any, expected: Any) -> None:
    """Tests reconstruction of nested structures back into their original types."""
    assert reconstruct_special_types(obj, fail_silently=False) == expected


# Test for reconstruct_special_type with fail_silently=True
def test_reconstruct_special_type_fail_silently() -> None:
    """Tests reconstruction with fail_silently=True, ensuring no exception is raised and original value is returned."""
    assert (
        reconstruct_special_type("invalid path:://example") == "invalid path:://example"
    )
    assert (
        reconstruct_special_type("not a number", fail_silently=True) == "not a number"
    )


@pytest.mark.parametrize(
    ("obj", "expected"),
    [
        (
            [{"nested": ["true", {"deep": "2023-09-05T12:30:00"}]}],
            [
                {
                    "nested": [
                        True,
                        {
                            "deep": datetime.datetime(
                                2023, 9, 5, 12, 30, tzinfo=datetime.timezone.utc
                            )
                        },
                    ]
                }
            ],
        ),
    ],
)
def test_reconstruct_deeply_nested_structure(obj: Any, expected: Any) -> None:
    """Tests reconstruction of deeply nested structures."""
    assert reconstruct_special_types(obj, fail_silently=False) == expected


class TestMakeHashable:
    """Tests for the make_hashable function."""

    def test_primitives_unchanged(self) -> None:
        """Test that primitive types are returned unchanged."""
        assert make_hashable("string") == "string"
        assert make_hashable(42) == 42
        assert make_hashable(3.14) == 3.14
        assert make_hashable(True) is True
        assert make_hashable(None) is None

    def test_list_to_tuple(self) -> None:
        """Test that lists are converted to tuples."""
        assert make_hashable([1, 2, 3]) == (1, 2, 3)
        assert make_hashable(["a", "b"]) == ("a", "b")

    def test_tuple_stays_tuple(self) -> None:
        """Test that tuples remain tuples."""
        assert make_hashable((1, 2, 3)) == (1, 2, 3)

    def test_dict_to_frozenset(self) -> None:
        """Test that dicts are converted to frozensets of tuples."""
        result = make_hashable({"a": 1, "b": 2})
        assert isinstance(result, frozenset)
        assert result == frozenset([("a", 1), ("b", 2)])

    def test_nested_structure(self) -> None:
        """Test that nested structures are recursively converted."""
        result = make_hashable({"key": [1, 2, {"nested": "value"}]})
        assert isinstance(result, frozenset)
        # The list should be converted to tuple, and nested dict to frozenset
        expected_nested = frozenset([("nested", "value")])
        expected_list = (1, 2, expected_nested)
        assert result == frozenset([("key", expected_list)])

    def test_result_is_hashable(self) -> None:
        """Test that the result can be used as a dict key."""
        complex_obj = {"a": [1, 2], "b": {"c": 3}}
        hashable = make_hashable(complex_obj)
        # Should not raise - can be used as dict key
        test_dict = {hashable: "value"}
        assert test_dict[hashable] == "value"

    def test_custom_object_to_string(self) -> None:
        """Test that custom objects are converted to string."""

        class CustomClass:
            def __str__(self) -> str:
                return "custom_str"

        result = make_hashable(CustomClass())
        assert result == "custom_str"
