"""This module contains test functions for verifying the functionality of JSON encoding and decoding using the
`extended_data_types` package. It includes fixtures for simple JSON data and the corresponding dictionary,
and tests for decoding and encoding JSON data.

Fixtures:
    - simple_json: Provides a sample JSON string for testing.
    - simple_dict: Provides the expected dictionary representation of the sample JSON string.

Functions:
    - test_decode_json: Tests decoding of JSON data to a dictionary.
    - test_encode_json: Tests encoding of a dictionary to JSON format.
"""

from __future__ import annotations

import pytest

from extended_data_types.json_utils import decode_json, encode_json


@pytest.fixture
def simple_json() -> str:
    """Provides a sample JSON string for testing.

    Returns:
        str: A sample JSON string.
    """
    return """{
  "key1": "value1",
  "key2": {
    "subkey1": "subvalue1",
    "subkey2": "subvalue2"
  },
  "key3": [
    1,
    2,
    3
  ]
}"""


@pytest.fixture
def simple_dict() -> dict:
    """Provides the expected dictionary representation of the sample JSON string.

    Returns:
        dict: The expected dictionary.
    """
    return {
        "key1": "value1",
        "key2": {"subkey1": "subvalue1", "subkey2": "subvalue2"},
        "key3": [1, 2, 3],
    }


def test_decode_json(simple_json: str, simple_dict: dict) -> None:
    """Tests decoding of JSON data to a dictionary.

    Args:
        simple_json (str): A sample JSON string provided by the fixture.
        simple_dict (dict): The expected dictionary provided by the fixture.

    Asserts:
        The result of decode_json matches the expected dictionary.
    """
    result = decode_json(simple_json)
    assert result == simple_dict


def test_encode_json(simple_dict: dict, simple_json: str) -> None:
    """Tests encoding of a dictionary to JSON format.

    Args:
        simple_dict (dict): The dictionary to encode provided by the fixture.
        simple_json (str): The expected JSON string provided by the fixture.

    Asserts:
        The result of encode_json matches the expected JSON string after decoding to dict.
    """
    # Encode with pretty print to match the fixture formatting
    result = encode_json(simple_dict, indent_2=True)

    # Normalize both encoded result and expected string by decoding them back to dicts
    result_dict = decode_json(result)
    expected_dict = decode_json(simple_json)

    # Compare the decoded dictionaries
    assert result_dict == expected_dict


def test_encode_json_bytes_output(simple_dict: dict) -> None:
    """Tests encoding output of encode_json to ensure it is converted to a string from bytes.

    Args:
        simple_dict (dict): The dictionary to encode provided by the fixture.

    Asserts:
        The result of encode_json is a string.
    """
    result = encode_json(simple_dict)
    assert isinstance(result, str)
