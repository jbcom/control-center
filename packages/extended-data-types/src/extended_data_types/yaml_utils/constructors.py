"""This module provides constructors for custom YAML tags and types.

It includes functions to construct undefined YAML tags and YAML pairs.
"""

from __future__ import annotations

from typing import Any

from yaml import MappingNode, SafeLoader, ScalarNode, SequenceNode

from .tag_classes import YamlPairs, YamlTagged


def yaml_construct_undefined(
    loader: SafeLoader,
    node: ScalarNode | SequenceNode | MappingNode,
) -> YamlTagged:
    """Construct a YAML tagged object for undefined tags.

    Args:
        loader (SafeLoader): The YAML loader.
        node (ScalarNode | SequenceNode | MappingNode): The YAML node.

    Returns:
        YamlTagged: The constructed YAML tagged object.
    """
    value: Any
    if isinstance(node, ScalarNode):
        value = loader.construct_scalar(node)
    elif isinstance(node, SequenceNode):
        value = loader.construct_sequence(node)
    elif isinstance(node, MappingNode):
        value = loader.construct_mapping(node)
    else:
        node_type = type(node).__name__
        raise TypeError(f"Unexpected node type: {node_type}")
    return YamlTagged(node.tag, value)


def yaml_construct_pairs(
    loader: SafeLoader,
    node: MappingNode,
) -> dict[Any, Any] | YamlPairs:
    """Construct YAML pairs.

    Args:
        loader (SafeLoader): The YAML loader.
        node (MappingNode): The YAML mapping node.

    Returns:
        Union[Dict[Any, Any], YamlPairs]: The constructed YAML pairs.
    """
    value: list[tuple[Any, Any]] = loader.construct_pairs(node)  # type: ignore[no-untyped-call]
    try:
        return dict(value)
    except TypeError:
        return YamlPairs(value)
