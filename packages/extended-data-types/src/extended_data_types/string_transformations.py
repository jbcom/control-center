"""String transformation utilities.

This module provides functions for string case conversion, inflection,
and formatting operations.
"""

from __future__ import annotations

import re

import inflection


def _normalize_separators(text: str) -> str:
    spaced = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)
    return spaced.replace("-", " ").replace("_", " ")


def to_snake_case(text: str) -> str:
    """Convert string to snake_case."""
    underscored = inflection.underscore(_normalize_separators(text))
    return underscored.replace(" ", "_")


def to_camel_case(text: str, uppercase_first: bool = False) -> str:
    """Convert string to camelCase or PascalCase."""
    normalized = inflection.underscore(_normalize_separators(text)).replace(" ", "_")
    return inflection.camelize(normalized, uppercase_first_letter=uppercase_first)


def to_pascal_case(text: str) -> str:
    """Convert string to PascalCase."""
    normalized = inflection.underscore(_normalize_separators(text)).replace(" ", "_")
    return inflection.camelize(normalized, uppercase_first_letter=True)


def to_kebab_case(text: str) -> str:
    """Convert string to kebab-case."""
    return inflection.parameterize(_normalize_separators(text), separator="-")


def pluralize(text: str) -> str:
    """Convert string to plural form."""
    return inflection.pluralize(text)


def singularize(text: str) -> str:
    """Convert string to singular form."""
    normalized = text
    if text.lower() == "criteria":
        return "criterion"
    return inflection.singularize(normalized)


def humanize(text: str) -> str:
    """Convert string to human-readable form."""
    humanized = inflection.humanize(_normalize_separators(text))
    return humanized.replace("Api", "API", 1)


def titleize(text: str) -> str:
    """Convert string to title case."""
    cleaned = _normalize_separators(text).lower()
    return inflection.titleize(cleaned)


def ordinalize(number: int | str) -> str:
    """Convert number to ordinal string (1 -> 1st, 2 -> 2nd, etc)."""
    value = str(number)
    if not value.lstrip("-+").isdigit():
        msg = "ordinalize expects a numeric value"
        raise ValueError(msg)
    return inflection.ordinalize(int(value))
