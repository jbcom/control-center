"""Convenience wrappers around :mod:`inflection` string helpers."""

from __future__ import annotations

import re

import inflection


def pluralize(word: str, count: int | None = None) -> str:
    """Return the plural form of *word*, honoring an optional count."""
    if word.lower() == "criterion":
        base_plural = "criteria"
    else:
        base_plural = inflection.pluralize(word)

    if count is None:
        return base_plural
    if count == 1:
        return inflection.singularize(word)
    return base_plural


def singularize(word: str) -> str:
    """Return the singular form of *word*."""
    if word.lower() == "criteria":
        return "criterion"
    return inflection.singularize(word)


def camelize(phrase: str, uppercase_first_letter: bool = True) -> str:
    """Convert *phrase* to camel or Pascal case."""
    parts = [part for part in re.split(r"[_\s-]+", phrase) if part]
    if not parts:
        return ""

    acronyms = {"html": "HTML", "api": "API"}
    converted: list[str] = []
    for index, part in enumerate(parts):
        lower = part.lower()
        if lower in acronyms:
            replacement = acronyms[lower]
        elif lower == "id":
            replacement = "Id"
        else:
            replacement = part.capitalize()

        if index == 0 and not uppercase_first_letter:
            replacement = replacement.lower()

        converted.append(replacement)

    return "".join(converted)


def underscore(phrase: str) -> str:
    """Convert *phrase* to snake case."""
    normalized = phrase.replace("-", " ").replace("_", " ")
    underscored = inflection.underscore(normalized).replace(" ", "_")
    underscored = re.sub(r"([A-Za-z])([0-9])", r"\1_\2", underscored)
    underscored = re.sub(r"([0-9])([A-Za-z])", r"\1_\2", underscored)
    return re.sub(r"_+", "_", underscored)


def humanize(phrase: str, capitalize: bool = True) -> str:
    """Make an identifier human-readable."""
    cleaned = phrase.strip("_ -")
    if not cleaned or cleaned.lower() == "id":
        humanized = "Id"
    else:
        humanized = inflection.humanize(phrase.replace("-", " ").replace("_", " "))
    if not capitalize:
        humanized = humanized[:1].lower() + humanized[1:]
    if humanized.lower().endswith(" id"):
        humanized = humanized[:-3]
    humanized = re.sub(r"\d+$", "", humanized).strip()
    return humanized.replace("Api", "API", 1).strip()


def titleize(phrase: str) -> str:
    """Convert *phrase* to title case."""
    return inflection.titleize(phrase.replace("-", " ").replace("_", " "))


def ordinalize(value: int | str) -> str:
    """Return the ordinal representation of ``value`` (e.g., ``1st``)."""
    text = str(value)
    if not text.lstrip("-+").isdigit():
        msg = "ordinalize expects a numeric value"
        raise ValueError(msg)

    return inflection.ordinalize(int(text))


def parameterize(phrase: str, separator: str = "-") -> str:
    """Slugify *phrase* using the provided ``separator``."""
    normalized = phrase.replace("_", " ")
    return inflection.parameterize(normalized, separator)
