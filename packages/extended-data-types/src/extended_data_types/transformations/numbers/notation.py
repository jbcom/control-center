"""Helpers for converting numbers between common notations."""

from __future__ import annotations

from fractions import Fraction
from typing import Final

from num2words import num2words

from . import words as words_module


_ROMAN_VALUES: Final[dict[str, int]] = {
    "M": 1000,
    "CM": 900,
    "D": 500,
    "CD": 400,
    "C": 100,
    "XC": 90,
    "L": 50,
    "XL": 40,
    "X": 10,
    "IX": 9,
    "V": 5,
    "IV": 4,
    "I": 1,
}

_MAX_ROMAN_VALUE: Final[int] = 3999


def to_roman(number: int, *, upper: bool = True) -> str:
    """Convert an integer between 1 and 3999 to Roman numerals."""
    if not isinstance(number, int):
        msg = "Roman numerals require an integer input"
        raise TypeError(msg)
    if not 1 <= number <= _MAX_ROMAN_VALUE:
        msg = f"Number must be between 1 and {_MAX_ROMAN_VALUE}"
        raise ValueError(msg)

    roman_pairs = [
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    ]

    result = []
    remaining = number
    for value, symbol in roman_pairs:
        count, remaining = divmod(remaining, value)
        result.append(symbol * count)

    numeral = "".join(result)
    return numeral.upper() if upper else numeral.lower()


def from_roman(numeral: str) -> int:
    """Convert a Roman numeral string to an integer."""
    normalized = numeral.upper().strip()
    if not normalized:
        msg = "Roman numeral must be a non-empty string"
        raise ValueError(msg)

    result = 0
    index = 0
    while index < len(normalized):
        if (
            index + 1 < len(normalized)
            and normalized[index : index + 2] in _ROMAN_VALUES
        ):
            result += _ROMAN_VALUES[normalized[index : index + 2]]
            index += 2
        elif normalized[index] in _ROMAN_VALUES:
            result += _ROMAN_VALUES[normalized[index]]
            index += 1
        else:
            msg = f"Invalid Roman numeral: {numeral}"
            raise ValueError(msg)

    if not 1 <= result <= _MAX_ROMAN_VALUE or to_roman(result) != normalized:
        msg = f"Invalid or non-canonical Roman numeral: {numeral}"
        raise ValueError(msg)

    return result


def to_ordinal(number: int, *, words: bool = False) -> str:
    """Convert an integer to an ordinal representation."""
    if not isinstance(number, int):
        msg = "Ordinal conversion requires an integer"
        raise TypeError(msg)
    if number <= 0:
        msg = "Ordinal must be positive"
        raise ValueError(msg)

    if words:
        return words_module.ordinal_to_words(number)
    return num2words(number, to="ordinal_num")


def from_ordinal(text: str) -> int:
    """Convert an ordinal string (numeric or word form) to an integer."""
    cleaned = text.strip()
    if not cleaned:
        msg = "Ordinal value must be a non-empty string"
        raise ValueError(msg)

    suffixes = ("st", "nd", "rd", "th")
    lowered = cleaned.lower()
    for suffix in suffixes:
        if lowered.endswith(suffix) and lowered[: -len(suffix)].lstrip("+-").isdigit():
            value = int(lowered[: -len(suffix)])
            if to_ordinal(value).lower() != lowered:
                msg = "Invalid ordinal suffix"
                raise ValueError(msg)
            return value

    return words_module.words_to_ordinal(cleaned)


def to_words(
    number: int | float, *, capitalize: bool = False, conjunction: str = " and "
) -> str:
    """Expose :func:`number_to_words` via the notation namespace."""
    return words_module.number_to_words(
        number, capitalize=capitalize, conjunction=conjunction
    )


def from_words(text: str) -> float:
    """Expose :func:`words_to_number` via the notation namespace."""
    return words_module.words_to_number(text)


def to_fraction(
    number: float, *, mixed: bool = False, precision: int | None = None
) -> str:
    """Convert a float to a fractional string representation."""
    if not isinstance(number, (int, float)):
        msg = "Fraction conversion expects a real number"
        raise TypeError(msg)
    if number != number or number in {float("inf"), -float("inf")}:
        msg = "Cannot convert non-finite numbers"
        raise ValueError(msg)

    if precision is not None:
        multiplier = 10**precision
        fraction = Fraction(round(number * multiplier), multiplier)
    else:
        fraction = Fraction(number).limit_denominator()

    sign = "-" if fraction < 0 else ""
    fraction = abs(fraction)

    if mixed and fraction.numerator >= fraction.denominator:
        whole = fraction.numerator // fraction.denominator
        remainder = Fraction(
            fraction.numerator % fraction.denominator, fraction.denominator
        )
        if remainder.numerator == 0:
            return f"{sign}{whole}"
        return f"{sign}{whole} {remainder.numerator}/{remainder.denominator}"

    return f"{sign}{fraction.numerator}/{fraction.denominator}"


def from_fraction(value: str) -> float:
    """Convert a fractional string (including mixed numbers) back to float."""
    fraction = words_module._parse_fraction_string(value)
    return float(fraction)


__all__ = [
    "from_fraction",
    "from_ordinal",
    "from_roman",
    "from_words",
    "to_fraction",
    "to_ordinal",
    "to_roman",
    "to_words",
]
