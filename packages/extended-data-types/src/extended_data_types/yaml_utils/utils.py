"""This module provides utility functions for YAML encoding and decoding.

It includes functions to decode YAML strings, encode Python objects to YAML,
and check if data is a YAML tagged object.
"""

from __future__ import annotations

from typing import Any

import yaml

from extended_data_types.string_data_type import bytestostr

from .dumpers import PureDumper
from .loaders import PureLoader
from .tag_classes import YamlTagged


def decode_yaml(yaml_data: str | memoryview | bytes | bytearray) -> Any:
    """Decode YAML data into a Python object.

    Args:
        yaml_data (str | memoryview | bytes | bytearray): The YAML data to decode.

    Returns:
        Any: The decoded Python object.
    """
    try:
        yaml_data = bytestostr(yaml_data)
    except UnicodeDecodeError as exc:
        raise yaml.YAMLError(
            f"Failed to decode bytes to string: {yaml_data!r}"
        ) from exc
    return yaml.load(yaml_data, Loader=PureLoader)  # noqa: S506


def encode_yaml(raw_data: Any) -> str:
    """Encode a Python object into a YAML string.

    Args:
        raw_data (Any): The Python object to encode.

    Returns:
        str: The encoded YAML string.
    """
    return yaml.dump(raw_data, Dumper=PureDumper, allow_unicode=True, sort_keys=False)


def is_yaml_data(data: Any) -> bool:
    """Check if the data is a YAML tagged object.

    Args:
        data (Any): The data to check.

    Returns:
        bool: True if the data is a YAML tagged object, False otherwise.
    """
    if isinstance(data, YamlTagged):
        return True
    if isinstance(data, dict):
        for value in data.values():
            if is_yaml_data(value):
                return True
    if isinstance(data, list):
        for item in data:
            if is_yaml_data(item):
                return True
    return False
