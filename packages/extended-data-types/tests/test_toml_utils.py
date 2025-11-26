"""Test Suite for TOML Utilities.

This module contains test functions for verifying the functionality of TOML decoding
using the `extended_data_types` package. It specifically tests the behavior of the
`decode_toml` function when dealing with invalid TOML formats.

Functions:
    - test_decode_toml_invalid_format: Tests decoding of TOML with syntax errors.
"""

from __future__ import annotations

import pytest
import tomlkit

from extended_data_types.toml_utils import decode_toml


def test_decode_toml_invalid_format() -> None:
    """Tests the `decode_toml` function with an invalid TOML format.

    This test checks whether the `decode_toml` function raises a `ParseError`
    when provided with a malformed TOML string, specifically one that contains
    an unclosed quote.

    Asserts:
        The function raises `tomlkit.exceptions.ParseError` when decoding
        the invalid TOML string.
    """
    invalid_toml = "title = 'Unclosed quote"
    with pytest.raises(tomlkit.exceptions.ParseError):
        decode_toml(invalid_toml)
