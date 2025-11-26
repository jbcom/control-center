"""Number transformation utilities.

This module provides functions for converting numbers to/from words,
Roman numerals, and various formatting operations.
"""

from __future__ import annotations

from typing import Final

from num2words import CONVERTER_CLASSES, num2words


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


def _normalize_language_code(lang: str) -> str:
    """Return the concrete num2words language key or raise ValueError."""
    normalized = lang.strip()
    if not normalized:
        msg = "Language code must be a non-empty string."
        raise ValueError(msg)

    if normalized in CONVERTER_CLASSES:
        return normalized

    fallback = normalized[:2]
    if fallback in CONVERTER_CLASSES:
        return fallback

    msg = f"Language '{lang}' is not supported by num2words."
    raise ValueError(msg)


def _validate_currency_code(currency: str, lang_code: str) -> str:
    """Validate the provided currency for the resolved language code."""
    normalized = currency.strip().upper()
    if not normalized:
        msg = "Currency code must be a non-empty string."
        raise ValueError(msg)

    converter = CONVERTER_CLASSES[lang_code]
    currency_forms = getattr(converter, "CURRENCY_FORMS", {}) or {}
    if not currency_forms:
        msg = f"Language '{lang_code}' does not define currency conversions."
        raise ValueError(msg)

    if normalized not in currency_forms:
        msg = f"Currency '{currency}' is not supported for language '{lang_code}'."
        raise ValueError(msg)

    return normalized


_MAX_ROMAN_VALUE: Final[int] = 3999


def to_roman(number: int) -> str:
    """Convert integer to Roman numerals.

    Args:
        number: Integer between 1 and 3999

    Returns:
        Roman numeral string

    Example:
        >>> to_roman(42)
        'XLII'
    """
    if not isinstance(number, int):
        msg = "Number must be an integer"
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
    return "".join(result)


def from_roman(numeral: str) -> int:
    """Convert Roman numerals to integer.

    Args:
        numeral: Roman numeral string

    Returns:
        Integer value

    Example:
        >>> from_roman('XLII')
        42
    """
    normalized = numeral.upper().strip()
    if not normalized:
        msg = "Roman numeral must be a non-empty string."
        raise ValueError(msg)

    result = 0
    i = 0
    while i < len(normalized):
        # Check for two-character combo
        if i + 1 < len(normalized) and normalized[i : i + 2] in _ROMAN_VALUES:
            result += _ROMAN_VALUES[normalized[i : i + 2]]
            i += 2
        elif normalized[i] in _ROMAN_VALUES:
            result += _ROMAN_VALUES[normalized[i]]
            i += 1
        else:
            msg = f"Invalid Roman numeral: {numeral}"
            raise ValueError(msg)

    if not 1 <= result <= _MAX_ROMAN_VALUE or to_roman(result) != normalized:
        msg = f"Invalid or non-canonical Roman numeral: {numeral}"
        raise ValueError(msg)

    return result


def number_to_words(number: int | float, lang: str = "en") -> str:
    """Convert integers or floats to their word representation.

    Supports both integers and floats. Floats are converted using "point" notation.

    Args:
        number: Integer or float to convert
        lang: Language code (default: 'en'). Supported languages include 'en', 'es',
              'fr', 'de', and many others (see num2words documentation)

    Returns:
        Number as words

    Raises:
        ValueError: If the specified language is empty or not supported by num2words

    Examples:
        >>> number_to_words(42)
        'forty-two'
        >>> number_to_words(42.5)
        'forty-two point five'
    """
    lang_code = _normalize_language_code(lang)
    try:
        return num2words(number, lang=lang_code)
    except NotImplementedError as exc:  # pragma: no cover
        raise ValueError(f"Language '{lang}' is not supported by num2words.") from exc


def number_to_ordinal(number: int, lang: str = "en") -> str:
    """Convert number to ordinal words.

    Args:
        number: Integer to convert
        lang: Language code (default: 'en'). Supported languages include 'en', 'es',
              'fr', 'de', and many others (see num2words documentation)

    Returns:
        Ordinal as words

    Raises:
        ValueError: If the specified language is empty or not supported by num2words

    Example:
        >>> number_to_ordinal(42)
        'forty-second'
    """
    lang_code = _normalize_language_code(lang)
    try:
        return num2words(number, ordinal=True, lang=lang_code)
    except NotImplementedError as exc:  # pragma: no cover
        raise ValueError(f"Language '{lang}' is not supported by num2words.") from exc


def number_to_currency(amount: float, currency: str = "USD", lang: str = "en") -> str:
    """Convert number to currency words.

    Args:
        amount: Amount to convert
        currency: Currency code (default: 'USD'). Common codes include 'USD', 'EUR',
                  'GBP', etc. Supported currencies vary by language. The code is
                  treated case-insensitively.
        lang: Language code (default: 'en'). Supported languages include 'en', 'es',
              'fr', 'de', and many others (see num2words documentation)

    Returns:
        Currency as words

    Raises:
        ValueError: If the specified language or currency code is empty or not
            supported by num2words for the given language

    Example:
        >>> number_to_currency(42.50)
        'forty-two dollars and fifty cents'
    """
    lang_code = _normalize_language_code(lang)
    currency_code = _validate_currency_code(currency, lang_code)
    try:
        return num2words(amount, to="currency", currency=currency_code, lang=lang_code)
    except NotImplementedError as exc:  # pragma: no cover
        raise ValueError(
            f"Currency '{currency}' is not supported for language '{lang_code}'."
        ) from exc
