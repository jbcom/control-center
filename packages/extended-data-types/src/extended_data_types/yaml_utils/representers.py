"""This module provides custom representers for YAML serialization.

It includes functions to represent tagged objects, YAML pairs, and strings.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from yaml import MappingNode, Node, SafeDumper, ScalarNode

from .tag_classes import LiteralScalarString, YamlPairs, YamlTagged


def yaml_represent_tagged(dumper: SafeDumper, data: YamlTagged) -> Node:
    """Represent a YAML tagged object.

    Args:
        dumper (SafeDumper): The YAML dumper.
        data (YamlTagged): The YAML tagged object.

    Returns:
        Node: The represented YAML node.
    """
    if not isinstance(data, YamlTagged):
        message = f"Expected YamlTagged, got {type(data).__name__}"
        raise TypeError(message)
    node = dumper.represent_data(data.__wrapped__)
    node.tag = data.tag
    return node


def yaml_represent_pairs(dumper: SafeDumper, data: YamlPairs) -> MappingNode:
    """Represent YAML pairs.

    Args:
        dumper (SafeDumper): The YAML dumper.
        data (YamlPairs): The YAML pairs object.

    Returns:
        MappingNode: The represented YAML node.
    """
    if not isinstance(data, YamlPairs):
        message = f"Expected YamlPairs, got {type(data).__name__}"
        raise TypeError(message)
    return dumper.represent_dict(data)


def yaml_str_representer(dumper: SafeDumper, data: str) -> ScalarNode:
    """Represent a YAML string.

    Args:
        dumper (SafeDumper): The YAML dumper.
        data (str): The string to represent.

    Returns:
        ScalarNode: The represented YAML node.
    """
    if "\n" in data or "||" in data or "&&" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    if any(char in data for char in ":{}[],&*#?|-><!%@`"):
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


def yaml_literal_str_representer(
    dumper: SafeDumper, data: LiteralScalarString
) -> ScalarNode:
    """Represent a LiteralScalarString as a literal block scalar in YAML.

    Args:
        dumper (SafeDumper): The YAML dumper.
        data (LiteralScalarString): The literal string to represent.

    Returns:
        ScalarNode: The represented YAML node with literal style.
    """
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data), style="|")
