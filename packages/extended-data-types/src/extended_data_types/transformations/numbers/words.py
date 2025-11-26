"""Convert between numeric values, words, and fractional strings."""

from __future__ import annotations

from collections.abc import Iterable
from fractions import Fraction

from num2words import num2words


_UNIT_MAP: dict[str, int] = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
}

_TENS_MAP: dict[str, int] = {
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}

_SCALE_MAP: dict[str, int] = {"hundred": 100, "thousand": 1000, "million": 1_000_000}

_ORDINAL_UNIT_MAP: dict[str, str] = {
    "first": "one",
    "second": "two",
    "third": "three",
    "fourth": "four",
    "fifth": "five",
    "sixth": "six",
    "seventh": "seven",
    "eighth": "eight",
    "ninth": "nine",
    "tenth": "ten",
    "eleventh": "eleven",
    "twelfth": "twelve",
    "thirteenth": "thirteen",
    "fourteenth": "fourteen",
    "fifteenth": "fifteen",
    "sixteenth": "sixteen",
    "seventeenth": "seventeen",
    "eighteenth": "eighteen",
    "nineteenth": "nineteen",
}

_ORDINAL_TENS_MAP: dict[str, str] = {
    "twentieth": "twenty",
    "thirtieth": "thirty",
    "fortieth": "forty",
    "fiftieth": "fifty",
    "sixtieth": "sixty",
    "seventieth": "seventy",
    "eightieth": "eighty",
    "ninetieth": "ninety",
}

_ORDINAL_SCALE_MAP: dict[str, str] = {
    "hundredth": "hundred",
    "thousandth": "thousand",
    "millionth": "million",
}

_DIGIT_WORDS: dict[str, int] = {
    word: value
    for value, word in enumerate(
        ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
    )
}


class _NumberParser:
    """Helper for turning English number words into numeric values."""

    def __init__(self, tokens: Iterable[str]):
        self.tokens = [token for token in tokens if token != "and"]

    def _convert_integer_tokens(self, tokens: list[str]) -> int:
        if not tokens:
            return 0

        total = 0
        current = 0
        for token in tokens:
            if token in _UNIT_MAP:
                current += _UNIT_MAP[token]
            elif token in _TENS_MAP:
                current += _TENS_MAP[token]
            elif token == "hundred":
                if current == 0:
                    current = 1
                current *= _SCALE_MAP[token]
            elif token in _SCALE_MAP:
                if current == 0:
                    current = 1
                total += current * _SCALE_MAP[token]
                current = 0
            else:
                msg = f"Unrecognized number word: {token}"
                raise ValueError(msg)

        return total + current

    def integer(self) -> int:
        return self._convert_integer_tokens(self.tokens)

    def number(self) -> float:
        if not self.tokens:
            msg = "Number words must be a non-empty string"
            raise ValueError(msg)

        if "point" not in self.tokens:
            return float(self.integer())

        point_index = self.tokens.index("point")
        whole = self._convert_integer_tokens(self.tokens[:point_index])
        decimal_tokens = self.tokens[point_index + 1 :]
        if not decimal_tokens:
            msg = "Decimal point must be followed by digits"
            raise ValueError(msg)

        decimal_digits: list[str] = []
        for token in decimal_tokens:
            if token not in _DIGIT_WORDS:
                msg = f"Invalid decimal digit: {token}"
                raise ValueError(msg)
            decimal_digits.append(str(_DIGIT_WORDS[token]))

        return float(f"{whole}.{''.join(decimal_digits)}")


def _tokenize(text: str) -> list[str]:
    normalized = text.replace("-", " ").lower().strip()
    tokens = normalized.split()
    if not tokens:
        msg = "Input text must be a non-empty string"
        raise ValueError(msg)
    return tokens


def number_to_words(
    number: int | float, *, capitalize: bool = False, conjunction: str = " and "
) -> str:
    """Convert numbers to English words."""
    if isinstance(number, float) and (
        number != number or number in {float("inf"), -float("inf")}
    ):
        msg = "Cannot convert non-finite numbers"
        raise ValueError(msg)

    sign = "minus " if number < 0 else ""
    words = num2words(abs(number), lang="en")
    if conjunction == "":
        words = words.replace(" and ", " ")
    elif conjunction != " and ":
        words = words.replace(" and ", f" {conjunction} ")
    if capitalize:
        words = words[:1].upper() + words[1:]
    return f"{sign}{words}".strip()


def words_to_number(text: str) -> float:
    """Convert English number words to a numeric value."""
    tokens = _tokenize(text)
    negative = tokens[0] == "minus"
    if negative:
        tokens = tokens[1:]
        if not tokens:
            msg = "Number words must contain digits after 'minus'"
            raise ValueError(msg)

    parser = _NumberParser(tokens)
    value = parser.number()
    return -value if negative else value


def ordinal_to_words(number: int, *, capitalize: bool = False) -> str:
    """Convert positive integers to ordinal words."""
    if not isinstance(number, int):
        msg = "Ordinal conversion requires an integer"
        raise TypeError(msg)
    if number <= 0:
        msg = "Ordinal must be a positive integer"
        raise ValueError(msg)

    words = num2words(number, to="ordinal", lang="en")
    if capitalize:
        words = words[:1].upper() + words[1:]
    return words


def _replace_ordinals_with_cardinals(tokens: list[str]) -> list[str]:
    converted: list[str] = []
    for token in tokens:
        if token in _ORDINAL_UNIT_MAP:
            converted.append(_ORDINAL_UNIT_MAP[token])
        elif token in _ORDINAL_TENS_MAP:
            converted.append(_ORDINAL_TENS_MAP[token])
        elif token in _ORDINAL_SCALE_MAP:
            converted.append(_ORDINAL_SCALE_MAP[token])
        else:
            stripped = token.rstrip("s")
            if stripped in _ORDINAL_UNIT_MAP:
                converted.append(_ORDINAL_UNIT_MAP[stripped])
            elif stripped in _ORDINAL_TENS_MAP:
                converted.append(_ORDINAL_TENS_MAP[stripped])
            elif stripped in _ORDINAL_SCALE_MAP:
                converted.append(_ORDINAL_SCALE_MAP[stripped])
            else:
                converted.append(token)
    return converted


def words_to_ordinal(text: str) -> int:
    """Convert ordinal words to their integer value."""
    tokens = _tokenize(text)
    negative = tokens[0] == "minus"
    if negative:
        msg = "Ordinals cannot be negative"
        raise ValueError(msg)

    converted_tokens = _replace_ordinals_with_cardinals(tokens)
    value = int(_NumberParser(converted_tokens).number())
    if value <= 0:
        msg = "Ordinal must represent a positive integer"
        raise ValueError(msg)
    return value


def fraction_to_words(fraction: str, *, capitalize: bool = False) -> str:
    """Convert fraction strings (e.g., ``"3/4"``) to words."""
    frac = _parse_fraction_string(fraction)
    sign = "minus " if frac < 0 else ""
    frac = abs(frac)

    whole = frac.numerator // frac.denominator
    remainder = Fraction(frac.numerator % frac.denominator, frac.denominator)

    parts: list[str] = []
    if whole:
        parts.append(num2words(whole, lang="en"))
    if remainder.numerator:
        if whole:
            parts.append("and")
        use_article = (
            remainder.numerator == 1 and remainder.denominator == 2 and whole > 0
        )
        numerator_words = (
            "a" if use_article else num2words(remainder.numerator, lang="en")
        )
        plural = remainder.numerator != 1
        denom_word = _denominator_word(remainder.denominator, plural)
        parts.append(f"{numerator_words} {denom_word}")

    if not parts:
        parts.append("zero")

    words = f"{sign}{' '.join(parts)}"
    words = words.strip()
    if capitalize:
        words = words[:1].upper() + words[1:]
    return words


def words_to_fraction(text: str) -> str:
    """Convert fraction words (e.g., ``"three quarters"``) to a fraction string."""
    tokens = _tokenize(text)
    negative = False
    if tokens[0] == "minus":
        negative = True
        tokens = tokens[1:]
        if not tokens:
            msg = "Fraction words must contain a value after 'minus'"
            raise ValueError(msg)

    whole = 0
    if "and" in tokens:
        and_index = tokens.index("and")
        whole_tokens = tokens[:and_index]
        fraction_tokens = tokens[and_index + 1 :]
        if not fraction_tokens:
            msg = "Fraction words must include a fractional part"
            raise ValueError(msg)
        whole = int(_NumberParser(whole_tokens).number()) if whole_tokens else 0
    else:
        fraction_tokens = tokens

    if not fraction_tokens:
        msg = "Fraction words must include a fractional part"
        raise ValueError(msg)

    numerator_tokens = fraction_tokens[:-1]
    denom_word = fraction_tokens[-1]

    if numerator_tokens and numerator_tokens[0] == "a" and len(numerator_tokens) == 1:
        numerator = 1
    elif numerator_tokens:
        numerator = int(_NumberParser(numerator_tokens).number())
    else:
        numerator = 1

    denominator = _denominator_from_word(denom_word)
    if denominator <= 0:
        msg = "Denominator must be positive"
        raise ValueError(msg)

    frac = Fraction(numerator, denominator)
    if whole:
        frac += whole
    if negative:
        frac *= -1

    whole_part = frac.numerator // frac.denominator
    remainder = Fraction(abs(frac.numerator % frac.denominator), frac.denominator)
    sign = "-" if frac < 0 else ""

    if remainder.numerator == 0:
        return f"{sign}{whole_part}"
    if whole_part:
        return f"{sign}{whole_part} {remainder.numerator}/{remainder.denominator}"
    return f"{sign}{remainder.numerator}/{remainder.denominator}"


def _denominator_word(denominator: int, plural: bool) -> str:
    if denominator == 2:
        return "halves" if plural else "half"
    if denominator == 4:
        return "quarters" if plural else "quarter"

    word = num2words(denominator, to="ordinal", lang="en")
    if plural and not word.endswith("s"):
        word = f"{word}s"
    return word


def _denominator_from_word(word: str) -> int:
    normalized = word.rstrip("s")
    if normalized in ("halve", "half"):
        return 2
    if normalized == "quarter":
        return 4
    try:
        return words_to_ordinal(normalized)
    except ValueError as exc:
        msg = f"Unrecognized denominator word: {word}"
        raise ValueError(msg) from exc


def _parse_fraction_string(value: str) -> Fraction:
    if not isinstance(value, str):
        msg = "Fraction value must be a string"
        raise TypeError(msg)

    cleaned = value.strip()
    if not cleaned:
        msg = "Fraction value must be a non-empty string"
        raise ValueError(msg)

    sign = -1 if cleaned.startswith("-") else 1
    cleaned = cleaned.lstrip("+-").strip()

    whole = 0
    tokens = cleaned.split()

    if len(tokens) == 2 and "/" in tokens[1]:
        whole = int(tokens[0])
        frac_str = tokens[1]
    elif len(tokens) == 3 and tokens[1] == "/":
        frac_str = f"{tokens[0]}/{tokens[2]}"
    else:
        frac_str = cleaned.replace(" ", "")

    if "/" not in frac_str:
        msg = "Fraction must contain a '/' separator"
        raise ValueError(msg)

    numerator_str, denominator_str = (part.strip() for part in frac_str.split("/", 1))
    numerator = int(numerator_str)
    denominator = int(denominator_str)
    if denominator == 0:
        msg = "Denominator cannot be zero"
        raise ValueError(msg)

    fraction = Fraction(numerator, denominator)
    if whole:
        fraction += whole
    return fraction * sign


__all__ = [
    "fraction_to_words",
    "number_to_words",
    "ordinal_to_words",
    "words_to_fraction",
    "words_to_number",
    "words_to_ordinal",
]
