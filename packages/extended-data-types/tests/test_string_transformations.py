"""Tests for string transformation utilities."""

from __future__ import annotations

from extended_data_types.string_transformations import (
    humanize,
    ordinalize,
    pluralize,
    singularize,
    titleize,
    to_camel_case,
    to_kebab_case,
    to_pascal_case,
    to_snake_case,
)


def test_pluralize() -> None:
    """Test pluralization."""
    assert pluralize("book") == "books"
    assert pluralize("child") == "children"
    assert pluralize("person") == "people"
    assert pluralize("sheep") == "sheep"


def test_singularize() -> None:
    """Test singularization."""
    assert singularize("books") == "book"
    assert singularize("children") == "child"
    assert singularize("people") == "person"
    assert singularize("sheep") == "sheep"


def test_to_snake_case() -> None:
    """Test snake_case conversion."""
    assert to_snake_case("HelloWorld") == "hello_world"
    assert to_snake_case("helloWorld") == "hello_world"
    assert to_snake_case("hello-world") == "hello_world"
    assert to_snake_case("hello world") == "hello_world"


def test_to_camel_case() -> None:
    """Test camelCase conversion."""
    assert to_camel_case("hello_world") == "helloWorld"
    assert to_camel_case("hello-world") == "helloWorld"
    assert to_camel_case("hello world") == "helloWorld"
    assert to_camel_case("HelloWorld") == "helloWorld"


def test_to_pascal_case() -> None:
    """Test PascalCase conversion."""
    assert to_pascal_case("hello_world") == "HelloWorld"
    assert to_pascal_case("hello-world") == "HelloWorld"
    assert to_pascal_case("hello world") == "HelloWorld"
    assert to_pascal_case("helloWorld") == "HelloWorld"


def test_to_kebab_case() -> None:
    """Test kebab-case conversion."""
    assert to_kebab_case("hello_world") == "hello-world"
    assert to_kebab_case("helloWorld") == "hello-world"
    assert to_kebab_case("HelloWorld") == "hello-world"


def test_humanize() -> None:
    """Test humanization."""
    assert humanize("hello_world") == "Hello world"
    assert humanize("user_name") == "User name"
    assert humanize("api_key") == "API key"


def test_titleize() -> None:
    """Test titleization."""
    assert titleize("hello world") == "Hello World"
    assert titleize("hello_world") == "Hello World"
    assert titleize("HELLO WORLD") == "Hello World"


def test_ordinalize() -> None:
    """Test ordinalization."""
    assert ordinalize(1) == "1st"
    assert ordinalize(2) == "2nd"
    assert ordinalize(3) == "3rd"
    assert ordinalize(4) == "4th"
    assert ordinalize(11) == "11th"
    assert ordinalize(21) == "21st"
    assert ordinalize("42") == "42nd"
