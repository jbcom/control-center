"""Tests for string inflection operations."""

from __future__ import annotations

import pytest

from extended_data_types.transformations.strings.inflection import (
    camelize,
    humanize,
    ordinalize,
    parameterize,
    pluralize,
    singularize,
    titleize,
    underscore,
)


def test_pluralize() -> None:
    """Test pluralization."""
    assert pluralize("book") == "books"
    assert pluralize("child") == "children"
    assert pluralize("person") == "people"
    assert pluralize("sheep") == "sheep"

    # Test with count
    assert pluralize("book", 1) == "book"
    assert pluralize("book", 2) == "books"

    # Test with irregular plurals
    assert pluralize("criterion") == "criteria"
    assert pluralize("bacterium") == "bacteria"

    # Test already plural
    assert pluralize("books") == "books"
    assert pluralize("people") == "people"


def test_singularize() -> None:
    """Test singularization."""
    assert singularize("books") == "book"
    assert singularize("children") == "child"
    assert singularize("people") == "person"
    assert singularize("sheep") == "sheep"

    # Test with irregular plurals
    assert singularize("criteria") == "criterion"
    assert singularize("bacteria") == "bacterium"

    # Test already singular
    assert singularize("book") == "book"
    assert singularize("person") == "person"


def test_camelize() -> None:
    """Test camelization."""
    assert camelize("hello_world") == "HelloWorld"
    assert camelize("hello_world", False) == "helloWorld"
    assert camelize("hello world") == "HelloWorld"
    assert camelize("Hello World") == "HelloWorld"

    # Test with acronyms
    assert camelize("html_parser") == "HTMLParser"
    assert camelize("html_parser", False) == "htmlParser"

    # Test with numbers
    assert camelize("user_id_123") == "UserId123"
    assert camelize("user_id_123", False) == "userId123"


def test_underscore() -> None:
    """Test underscoring."""
    assert underscore("HelloWorld") == "hello_world"
    assert underscore("helloWorld") == "hello_world"
    assert underscore("Hello World") == "hello_world"
    assert underscore("hello-world") == "hello_world"

    # Test with acronyms
    assert underscore("HTMLParser") == "html_parser"
    assert underscore("PDFLoader") == "pdf_loader"

    # Test with numbers
    assert underscore("UserId123") == "user_id_123"
    assert underscore("userId123") == "user_id_123"


def test_humanize() -> None:
    """Test humanization."""
    assert humanize("employee_salary") == "Employee salary"
    assert humanize("author_id") == "Author"
    assert humanize("user_name") == "User name"
    assert humanize("_id") == "Id"

    # Test with numbers
    assert humanize("user123") == "User"

    # Test with capitalization
    assert humanize("user_name", capitalize=False) == "user name"

    # Test with special characters
    assert humanize("hello-world") == "Hello world"
    assert humanize("hello_world_123") == "Hello world"


def test_titleize() -> None:
    """Test titleization."""
    assert titleize("hello_world") == "Hello World"
    assert titleize("hello-world") == "Hello World"
    assert titleize("hello world") == "Hello World"

    # Test with acronyms
    assert titleize("html_parser") == "Html Parser"
    assert titleize("PDF_reader") == "Pdf Reader"

    # Test with numbers
    assert titleize("chapter_1") == "Chapter 1"
    assert titleize("page-123") == "Page 123"


def test_ordinalize() -> None:
    """Test ordinalization."""
    assert ordinalize(1) == "1st"
    assert ordinalize(2) == "2nd"
    assert ordinalize(3) == "3rd"
    assert ordinalize(4) == "4th"
    assert ordinalize(11) == "11th"
    assert ordinalize(12) == "12th"
    assert ordinalize(13) == "13th"
    assert ordinalize(21) == "21st"

    # Test with string numbers
    assert ordinalize("1") == "1st"
    assert ordinalize("22") == "22nd"

    # Test with invalid input
    with pytest.raises(ValueError):
        ordinalize("abc")


def test_parameterize() -> None:
    """Test parameterization."""
    assert parameterize("Hello World") == "hello-world"
    assert parameterize("Hello_World") == "hello-world"
    assert parameterize("hello.world") == "hello-world"

    # Test with custom separator
    assert parameterize("hello world", "_") == "hello_world"

    # Test with special characters
    assert parameterize("héllo wörld") == "hello-world"
    assert parameterize("hello!!!world") == "hello-world"

    # Test with numbers
    assert parameterize("hello 123 world") == "hello-123-world"
    assert parameterize("file_v1.2.3") == "file-v1-2-3"
