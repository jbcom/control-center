"""Tests for number transformation utilities."""

from __future__ import annotations

import pytest

from extended_data_types.number_transformations import (
    from_roman,
    number_to_currency,
    number_to_ordinal,
    number_to_words,
    to_roman,
)


def test_to_roman() -> None:
    """Test conversion to Roman numerals."""
    assert to_roman(1) == "I"
    assert to_roman(4) == "IV"
    assert to_roman(9) == "IX"
    assert to_roman(42) == "XLII"
    assert to_roman(99) == "XCIX"
    assert to_roman(499) == "CDXCIX"
    assert to_roman(999) == "CMXCIX"
    assert to_roman(3999) == "MMMCMXCIX"

    # Test invalid input
    with pytest.raises(ValueError):
        to_roman(0)
    with pytest.raises(ValueError):
        to_roman(4000)


def test_from_roman() -> None:
    """Test conversion from Roman numerals."""
    assert from_roman("I") == 1
    assert from_roman("IV") == 4
    assert from_roman("IX") == 9
    assert from_roman("XLII") == 42
    assert from_roman("XCIX") == 99
    assert from_roman("CDXCIX") == 499
    assert from_roman("CMXCIX") == 999
    assert from_roman("MMMCMXCIX") == 3999

    # Test with lower case
    assert from_roman("xlii") == 42

    # Test invalid input
    with pytest.raises(ValueError):
        from_roman("ABC")
    with pytest.raises(ValueError):
        from_roman("")


def test_number_to_words() -> None:
    """Test conversion to words."""
    assert number_to_words(0) == "zero"
    assert number_to_words(1) == "one"
    assert number_to_words(42) == "forty-two"
    assert number_to_words(100) == "one hundred"
    assert number_to_words(1000) == "one thousand"


def test_number_to_words_invalid_language() -> None:
    """Unsupported languages should raise a ValueError."""
    with pytest.raises(ValueError):
        number_to_words(1, lang="zz")


def test_number_to_ordinal() -> None:
    """Test conversion to ordinal words."""
    assert number_to_ordinal(1) == "first"
    assert number_to_ordinal(2) == "second"
    assert number_to_ordinal(3) == "third"
    assert number_to_ordinal(4) == "fourth"
    assert number_to_ordinal(21) == "twenty-first"
    assert number_to_ordinal(42) == "forty-second"


def test_number_to_ordinal_invalid_language() -> None:
    """Unsupported languages for ordinals should raise a ValueError."""
    with pytest.raises(ValueError):
        number_to_ordinal(1, lang="zz")


def test_number_to_currency() -> None:
    """Test conversion to currency words."""
    result = number_to_currency(42.50)
    assert "forty-two" in result.lower()
    assert "fifty" in result.lower()

    result = number_to_currency(100.00)
    assert "one hundred" in result.lower()


def test_number_to_currency_invalid_language() -> None:
    """Unsupported currency languages should raise a ValueError."""
    with pytest.raises(ValueError):
        number_to_currency(1.0, lang="zz")


def test_number_to_currency_invalid_currency_code() -> None:
    """Unknown currency codes should raise a ValueError."""
    with pytest.raises(ValueError):
        number_to_currency(1.0, currency="zzz")


def test_number_to_currency_case_insensitive_currency() -> None:
    """Currency codes are treated case-insensitively."""
    lower_result = number_to_currency(1.25, currency="usd")
    upper_result = number_to_currency(1.25, currency="USD")
    assert lower_result == upper_result


def test_round_trip_roman() -> None:
    """Test round-trip conversion for Roman numerals."""
    for num in [1, 5, 10, 42, 99, 500, 1000, 1984, 3999]:
        assert from_roman(to_roman(num)) == num


def test_from_roman_rejects_non_canonical_forms() -> None:
    """Non-canonical numerals should raise a ValueError."""
    with pytest.raises(ValueError):
        from_roman("IM")
