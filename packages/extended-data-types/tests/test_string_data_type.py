"""Test Suite for Extended Data Types - String Operations

This module contains test functions and fixtures for verifying the functionality of various string operations
provided by the `extended_data_types` package. The module covers a wide range of string manipulation and validation
functions, including key sanitization, string truncation, case modification, URL validation, title casing, boolean
conversion, and path handling.

### Fixtures
Fixtures are used extensively to provide test data, promoting reusability and clarity. The module includes the following fixtures:
    - `test_key`: Provides a sample key with invalid characters for sanitization testing.
    - `sanitized_key`: Provides the expected sanitized key after processing.
    - `truncate_data`: Provides sample data for testing string truncation with specified lengths.
    - `lower_first_char_data`: Provides input strings and expected results for testing lowercase conversion of the first character.
    - `upper_first_char_data`: Provides input strings and expected results for testing uppercase conversion of the first character.
    - `url_data`: Provides URLs and expected validation results for testing URL checks.
    - `titleize_name_data`: Provides camelCase names and expected TitleCase results for testing titleization.
    - `strtobool_data`: Provides strings representing truth values for testing boolean conversion.
    - `strtofloat_data`: Provides strings representing floats for testing float conversion.
    - `strtoint_data`: Provides strings representing integers for testing integer conversion.
    - `valid_path_data`: Provides valid input values and expected results for testing path conversion.
    - `invalid_path_data`: Provides invalid inputs and expected exceptions for testing path conversion with errors.
    - `silent_invalid_path_data`: Provides invalid inputs for testing path conversion when errors are silenced.
    - `removeprefix_data`: Provides input strings, prefixes, and expected results for testing prefix removal.
    - `removesuffix_data`: Provides input strings, suffixes, and expected results for testing suffix removal.

### Test Functions
The module contains the following test functions:
    - `test_sanitize_key`: Tests sanitizing a key by removing invalid characters.
    - `test_truncate`: Tests truncating a string to a specified length.
    - `test_lower_first_char`: Tests converting the first character of a string to lowercase.
    - `test_upper_first_char`: Tests converting the first character of a string to uppercase.
    - `test_is_url`: Tests checking if a string is a valid URL.
    - `test_titleize_name`: Tests converting camelCase names to TitleCase.
    - `test_strtobool`: Tests converting a string to a boolean value.
    - `test_strtofloat`: Tests converting a string to a float value.
    - `test_strtoint`: Tests converting a string to an integer value.
    - `test_strtopath`: Tests converting valid inputs into pathlib.Path objects.
    - `test_strtopath_invalid`: Tests handling invalid path inputs that should raise exceptions.
    - `test_strtopath_invalid_silent`: Tests handling invalid path inputs when errors are silenced.
    - `test_removeprefix`: Tests removing a prefix from a string.
    - `test_removesuffix`: Tests removing a suffix from a string.
"""

from __future__ import annotations

from typing import Any

import pytest

from extended_data_types.string_data_type import (
    bytestostr,
    is_url,
    lower_first_char,
    removeprefix,
    removesuffix,
    sanitize_key,
    titleize_name,
    truncate,
    upper_first_char,
)


@pytest.fixture
def test_key() -> str:
    """Provides a sample key with invalid characters for testing.

    Returns:
        str: A sample key with invalid characters.
    """
    return "key-with*invalid_chars"


@pytest.fixture
def sanitized_key() -> str:
    """Provides the expected sanitized key for testing.

    Returns:
        str: The expected sanitized key.
    """
    return "key_with_invalid_chars"


@pytest.fixture(
    params=[
        ("This is a long message", 10, "This is..."),
        ("Short msg", 10, "Short msg"),
        ("Needs zero length", 0, ""),
    ]
)
def truncate_data(request: Any) -> tuple[str, int, str]:
    """Provides data for testing the truncate function.

    Yields:
        tuple[str, int, str]: A tuple containing the message, max length, and expected truncated string.
    """
    return request.param


@pytest.fixture(params=[("Hello", "hello"), ("", "")])
def lower_first_char_data(request: Any) -> tuple[str, str]:
    """Provides data for testing lower_first_char function.

    Yields:
        tuple[str, str]: A tuple containing the input string and expected result.
    """
    return request.param


@pytest.fixture(params=[("hello", "Hello"), ("", "")])
def upper_first_char_data(request: Any) -> tuple[str, str]:
    """Provides data for testing upper_first_char function.

    Yields:
        tuple[str, str]: A tuple containing the input string and expected result.
    """
    return request.param


@pytest.fixture(params=[("https://example.com", True), ("not_a_url", False)])
def url_data(request: Any) -> tuple[str, bool]:
    """Provides data for testing is_url function.

    Yields:
        tuple[str, bool]: A tuple containing the URL string and the expected boolean result.
    """
    return request.param


@pytest.fixture(
    params=[
        ("camelCaseName", "Camel Case Name"),
    ]
)
def titleize_name_data(request: Any) -> tuple[str, str]:
    """Provides data for testing titleize_name function.

    Yields:
        tuple[str, str]: A tuple containing the input camelCase name and the expected TitleCase name.
    """
    return request.param


@pytest.fixture(
    params=[
        ("test_string", "test_", "string"),
        ("string", "test_", "string"),
        ("test_string", "", "test_string"),
    ]
)
def removeprefix_data(request: Any) -> tuple[str, str, str]:
    """Provides data for testing removeprefix function.

    Yields:
        tuple[str, str, str]: A tuple containing the input string, prefix, and expected result.
    """
    return request.param


@pytest.fixture(
    params=[
        ("test_string", "_string", "test"),
        ("test", "_string", "test"),
        ("test_string", "", "test_string"),
    ]
)
def removesuffix_data(request: Any) -> tuple[str, str, str]:
    """Provides data for testing removesuffix function.

    Yields:
        tuple[str, str, str]: A tuple containing the input string, suffix, and expected result.
    """
    return request.param


@pytest.mark.parametrize(
    ("input_value", "expected_output"),
    [
        ("simple string", "simple string"),  # String input
        (b"bytes data", "bytes data"),  # Bytes input
        (bytearray(b"bytes array data"), "bytes array data"),  # Bytearray input
        (memoryview(b"memoryview data"), "memoryview data"),  # Memoryview input
    ],
)
def test_bytestostr(
    input_value: str | memoryview | bytes | bytearray, expected_output: str
) -> None:
    """Tests converting various byte-like objects and strings into a UTF-8 decoded string.

    Args:
        input_value (str | memoryview | bytes | bytearray): The input value to convert to a string.
        expected_output (str): The expected UTF-8 decoded string.

    Asserts:
        The result of bytestostr matches the expected UTF-8 decoded string for valid inputs.
    """
    assert bytestostr(input_value) == expected_output


def test_bytestostr_invalid_bytes() -> None:
    """Tests handling of invalid byte sequences during conversion to string.

    Asserts:
        The bytestostr function raises a ConversionError when invalid bytes cannot be decoded.
    """
    invalid_bytes = b"\x80invalid"
    with pytest.raises(UnicodeDecodeError):
        bytestostr(invalid_bytes)


def test_sanitize_key(test_key: str, sanitized_key: str) -> None:
    """Tests sanitizing a key by removing invalid characters.

    Args:
        test_key (str): A sample key provided by the fixture.
        sanitized_key (str): The expected sanitized key provided by the fixture.

    Asserts:
        The result of sanitize_key matches the expected sanitized key.
    """
    assert sanitize_key(test_key) == sanitized_key


def test_truncate(truncate_data: tuple[str, int, str]) -> None:
    """Tests truncating a string to a specified length.

    Args:
        truncate_data (tuple[str, int, str]): A fixture providing the message, max length, and expected truncated string.

    Asserts:
        The result of truncate matches the expected truncated string.
    """
    msg, max_length, expected = truncate_data
    assert truncate(msg, max_length) == expected


def test_lower_first_char(lower_first_char_data: tuple[str, str]) -> None:
    """Tests converting the first character of a string to lowercase.

    Args:
        lower_first_char_data (tuple[str, str]): A fixture providing the input string and expected result.

    Asserts:
        The result of lower_first_char matches the expected string with the first character in lowercase.
    """
    inp, expected = lower_first_char_data
    assert lower_first_char(inp) == expected


def test_upper_first_char(upper_first_char_data: tuple[str, str]) -> None:
    """Tests converting the first character of a string to uppercase.

    Args:
        upper_first_char_data (tuple[str, str]): A fixture providing the input string and expected result.

    Asserts:
        The result of upper_first_char matches the expected string with the first character in uppercase.
    """
    inp, expected = upper_first_char_data
    assert upper_first_char(inp) == expected


def test_is_url(url_data: tuple[str, bool]) -> None:
    """Tests checking if a string is a valid URL.

    Args:
        url_data (tuple[str, bool]): A fixture providing the URL string and the expected boolean result.

    Asserts:
        The result of is_url is True for valid URLs and False for invalid URLs.
    """
    url, expected = url_data
    assert is_url(url) == expected


def test_titleize_name(titleize_name_data: tuple[str, str]) -> None:
    """Tests converting camelCase names to title case.

    Args:
        titleize_name_data (tuple[str, str]): A fixture providing the input camelCase name and the expected TitleCase name.

    Asserts:
        The result of titleize_name matches the expected title case string.
    """
    name, expected = titleize_name_data
    assert titleize_name(name) == expected


def test_removeprefix(removeprefix_data: tuple[str, str, str]) -> None:
    """Tests removing a prefix from a string.

    Args:
        removeprefix_data (tuple[str, str, str]): A fixture providing the input string, prefix, and expected result.

    Asserts:
        The result of removeprefix matches the expected string with the prefix removed.
    """
    string, prefix, expected = removeprefix_data
    assert removeprefix(string, prefix) == expected


def test_removesuffix(removesuffix_data: tuple[str, str, str]) -> None:
    """Tests removing a suffix from a string.

    Args:
        removesuffix_data (tuple[str, str, str]): A fixture providing the input string, suffix, and expected result.

    Asserts:
        The result of removesuffix matches the expected string with the suffix removed.
    """
    string, suffix, expected = removesuffix_data
    assert removesuffix(string, suffix) == expected
