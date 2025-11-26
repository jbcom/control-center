"""Tests for number notation operations."""

from __future__ import annotations

import pytest

from extended_data_types.transformations.numbers.notation import (
    from_fraction,
    from_ordinal,
    from_roman,
    from_words,
    to_fraction,
    to_ordinal,
    to_roman,
    to_words,
)


def test_to_roman() -> None:
    """Test conversion to Roman numerals."""
    assert to_roman(1) == "I"
    assert to_roman(4) == "IV"
    assert to_roman(9) == "IX"
    assert to_roman(49) == "XLIX"
    assert to_roman(99) == "XCIX"
    assert to_roman(499) == "CDXCIX"
    assert to_roman(999) == "CMXCIX"
    assert to_roman(3999) == "MMMCMXCIX"

    # Test with lower case
    assert to_roman(42, upper=False) == "xlii"

    # Test invalid input
    with pytest.raises(ValueError):
        to_roman(0)
    with pytest.raises(ValueError):
        to_roman(4000)
    with pytest.raises(TypeError):
        to_roman(1.5)


def test_from_roman() -> None:
    """Test conversion from Roman numerals."""
    assert from_roman("I") == 1
    assert from_roman("IV") == 4
    assert from_roman("IX") == 9
    assert from_roman("XLIX") == 49
    assert from_roman("XCIX") == 99
    assert from_roman("CDXCIX") == 499
    assert from_roman("CMXCIX") == 999
    assert from_roman("MMMCMXCIX") == 3999

    # Test with lower case
    assert from_roman("xlii") == 42

    # Test invalid input
    with pytest.raises(ValueError):
        from_roman("IIII")
    with pytest.raises(ValueError):
        from_roman("ABC")
    with pytest.raises(ValueError):
        from_roman("")


def test_to_ordinal() -> None:
    """Test conversion to ordinal numbers."""
    assert to_ordinal(1) == "1st"
    assert to_ordinal(2) == "2nd"
    assert to_ordinal(3) == "3rd"
    assert to_ordinal(4) == "4th"
    assert to_ordinal(11) == "11th"
    assert to_ordinal(12) == "12th"
    assert to_ordinal(13) == "13th"
    assert to_ordinal(21) == "21st"
    assert to_ordinal(102) == "102nd"
    assert to_ordinal(1003) == "1003rd"

    # Test with words
    assert to_ordinal(1, words=True) == "first"
    assert to_ordinal(2, words=True) == "second"
    assert to_ordinal(3, words=True) == "third"
    assert to_ordinal(11, words=True) == "eleventh"

    # Test invalid input
    with pytest.raises(ValueError):
        to_ordinal(0)
    with pytest.raises(TypeError):
        to_ordinal(1.5)


def test_from_ordinal() -> None:
    """Test conversion from ordinal numbers."""
    assert from_ordinal("1st") == 1
    assert from_ordinal("2nd") == 2
    assert from_ordinal("3rd") == 3
    assert from_ordinal("4th") == 4
    assert from_ordinal("11th") == 11
    assert from_ordinal("21st") == 21
    assert from_ordinal("102nd") == 102

    # Test with words
    assert from_ordinal("first") == 1
    assert from_ordinal("second") == 2
    assert from_ordinal("third") == 3
    assert from_ordinal("eleventh") == 11

    # Test invalid input
    with pytest.raises(ValueError):
        from_ordinal("1rd")
    with pytest.raises(ValueError):
        from_ordinal("zeroth")
    with pytest.raises(ValueError):
        from_ordinal("")


def test_to_words() -> None:
    """Test conversion to words."""
    assert to_words(0) == "zero"
    assert to_words(9) == "nine"
    assert to_words(10) == "ten"
    assert to_words(21) == "twenty-one"
    assert to_words(100) == "one hundred"
    assert to_words(101) == "one hundred and one"
    assert to_words(999) == "nine hundred and ninety-nine"

    # Test with capitals
    assert to_words(42, capitalize=True) == "Forty-two"

    # Test with decimals
    assert to_words(3.14) == "three point one four"
    assert to_words(0.001) == "zero point zero zero one"

    # Test with negative numbers
    assert to_words(-42) == "minus forty-two"


def test_from_words() -> None:
    """Test conversion from words."""
    assert from_words("zero") == 0
    assert from_words("nine") == 9
    assert from_words("ten") == 10
    assert from_words("twenty-one") == 21
    assert from_words("one hundred") == 100
    assert from_words("one hundred and one") == 101
    assert from_words("nine hundred and ninety-nine") == 999

    # Test with capitals
    assert from_words("Forty-two") == 42

    # Test with decimals
    assert from_words("three point one four") == 3.14
    assert from_words("zero point zero zero one") == 0.001

    # Test with negative numbers
    assert from_words("minus forty-two") == -42

    # Test invalid input
    with pytest.raises(ValueError):
        from_words("invalid")
    with pytest.raises(ValueError):
        from_words("")


def test_to_fraction() -> None:
    """Test conversion to fractions."""
    assert to_fraction(0.5) == "1/2"
    assert to_fraction(0.25) == "1/4"
    assert to_fraction(0.75) == "3/4"
    assert to_fraction(1.5) == "3/2"

    # Test with mixed numbers
    assert to_fraction(1.5, mixed=True) == "1 1/2"
    assert to_fraction(2.75, mixed=True) == "2 3/4"

    # Test with reduced fractions
    assert to_fraction(0.6666666666666666) == "2/3"
    assert to_fraction(0.3333333333333333) == "1/3"

    # Test with precision
    assert to_fraction(0.3333, precision=2) == "33/100"

    # Test invalid input
    with pytest.raises(ValueError):
        to_fraction(float("inf"))


def test_from_fraction() -> None:
    """Test conversion from fractions."""
    assert from_fraction("1/2") == 0.5
    assert from_fraction("1/4") == 0.25
    assert from_fraction("3/4") == 0.75
    assert from_fraction("3/2") == 1.5

    # Test with mixed numbers
    assert from_fraction("1 1/2") == 1.5
    assert from_fraction("2 3/4") == 2.75

    # Test with spaces
    assert from_fraction(" 1 / 2 ") == 0.5

    # Test invalid input
    with pytest.raises(ValueError):
        from_fraction("1/0")
    with pytest.raises(ValueError):
        from_fraction("invalid")
    with pytest.raises(ValueError):
        from_fraction("")
