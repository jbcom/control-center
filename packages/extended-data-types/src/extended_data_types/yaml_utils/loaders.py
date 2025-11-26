"""This module provides custom YAML loaders for deserializing YAML content into Python objects.

It includes a custom YAML loader class that handles special tags and constructors.
"""

from __future__ import annotations

from typing import Any

from yaml import SafeLoader

from .constructors import yaml_construct_pairs, yaml_construct_undefined


class PureLoader(SafeLoader):
    """Custom YAML loader."""

    def __init__(self, stream: Any) -> None:
        """Initialize the custom YAML loader with additional constructors.

        Args:
            stream (Any): The input stream containing YAML data.
        """
        super().__init__(stream)
        self.add_constructor("!CustomTag", yaml_construct_undefined)
        self.add_constructor("!Ref", yaml_construct_undefined)
        self.add_constructor("!Sub", yaml_construct_undefined)
        self.add_constructor("tag:yaml.org,2002:map", yaml_construct_pairs)
