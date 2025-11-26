"""This module provides utilities for inspecting the call stack and methods of classes.

It includes functions to get the caller's name, filter methods, and retrieve available
methods and their docstrings for a class.
"""

from __future__ import annotations

import re
import sys

from inspect import getmembers, isfunction
from typing import Any


def get_caller() -> str:
    """Gets the name of the caller function.

    Returns:
        str: The name of the caller function.
    """
    return sys._getframe(2).f_code.co_name  # noqa: SLF001


def get_unique_signature(obj: Any, delim: str = "/") -> str:
    """Generate a unique signature for an object based on its class and module.

    Args:
        obj (Any): The object to generate a signature for.
        delim (str): The delimiter to use between the module and class names. Defaults to "/".

    Returns:
        str: A unique signature string for the object.
    """
    return str(obj.__class__.__module__) + delim + str(obj.__class__.__name__)


def filter_methods(methods: list[str]) -> list[str]:
    """Filters out private methods from a list of method names.

    Args:
        methods (list[str]): The list of method names to filter.

    Returns:
        list[str]: The filtered list of method names.
    """
    return [method for method in methods if not method.startswith("_")]


def get_available_methods(cls: type[Any]) -> dict[str, str | None]:
    """Gets available methods and their docstrings for a class.

    An "available method" is a public method that:
    - Does not contain '__' in its name.
    - Belongs to the same module as the class.
    - Does not have 'NOPARSE' in its docstring.

    Args:
        cls (type[Any]): The class to inspect.

    Returns:
        dict[str, str | None]: A dictionary of method names and their docstrings.
    """
    module_name = cls.__module__
    methods = getmembers(cls, isfunction)

    return {
        method_name: method_signature.__doc__
        for method_name, method_signature in methods
        if "__" not in method_name
        and method_signature.__module__ == module_name
        and "NOPARSE" not in (method_signature.__doc__ or "")
    }


def get_inputs_from_docstring(docstring: str) -> dict[str, dict[str, str]]:
    """Extract existing input details from a method's docstring.

    This function parses a docstring to identify inputs defined with specific properties:
    name, required, and sensitive. The extraction is case-insensitive, and the results
    are returned as a dictionary with input names as keys (lowercase) and their properties
    as values.

    Args:
        docstring (str): The docstring to parse for input definitions.

    Returns:
        A dictionary where each key is an input name (in lowercase),
        and the value is another dictionary containing:

        - "required": Whether the input is required ("true" or "false")
        - "sensitive": Whether the input is sensitive ("true" or "false")

    Example:
        For a docstring containing::

            env=name: API_KEY, required: true, sensitive: false
            env=name: DB_PASSWORD, required: true, sensitive: true

        The output will be::

            {
                "api_key": {"required": "true", "sensitive": "false"},
                "db_password": {"required": "true", "sensitive": "true"}
            }
    """
    input_pattern = r"name: (\w+), required: (true|false), sensitive: (true|false)"
    matches = re.findall(input_pattern, docstring or "")
    return {
        name.lower(): {"required": required, "sensitive": sensitive}
        for name, required, sensitive in matches
    }


def update_docstring(
    original_docstring: str, new_inputs: dict[str, dict[str, str]]
) -> str:
    """Update the docstring with new input definitions.

    Args:
        original_docstring (str): The original docstring to update.
        new_inputs (dict[str, dict[str, str]]): A dictionary of new inputs to add to the docstring.

    Returns:
        str: The updated docstring with new inputs.
    """
    # Split into lines and get indentation from first non-empty line
    lines = original_docstring.splitlines()
    base_indent = ""
    for line in lines:
        if line.strip():
            base_indent = " " * (len(line) - len(line.lstrip()))
            break

    # Track existing entries to avoid duplicates
    existing_entries: set[str] = set()
    result_lines: list[str] = []

    # Process existing lines
    for line in lines:
        stripped = line.strip()
        if not stripped and not result_lines:
            result_lines.append(line)
            continue

        if stripped.startswith("env=name:"):
            entry_name = stripped.split(",")[0].split(":")[1].strip()
            existing_entries.add(entry_name)
            result_lines.append(line)
        elif stripped:  # Keep non-empty, non-env lines
            result_lines.append(line)

    # Add new entries if they don't already exist
    for key, attributes in new_inputs.items():
        if key not in existing_entries:
            line = f"{base_indent}env=name: {key}, required: {attributes['required']}, sensitive: {attributes['sensitive']}"
            result_lines.append(line)

    return "\n".join(result_lines)


def current_python_version_is_at_least(minor: int, major: int = 3) -> bool:
    """Checks if the current Python version is at least the specified version.

    Args:
        minor (int): The minimum minor version.
        major (int, optional): The minimum major version. Defaults to 3.

    Returns:
        bool: True if the current Python version is at least the specified version, False otherwise.
    """
    return (sys.version_info.major > major) or (
        sys.version_info.major == major and sys.version_info.minor >= minor
    )
