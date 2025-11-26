"""This module provides utilities for handling YAML data.

It includes custom loaders, dumpers, and utility functions for working with YAML.
"""

from .constructors import yaml_construct_pairs, yaml_construct_undefined
from .dumpers import PureDumper
from .loaders import PureLoader
from .representers import (
    yaml_literal_str_representer,
    yaml_represent_pairs,
    yaml_represent_tagged,
    yaml_str_representer,
)
from .tag_classes import LiteralScalarString, YamlPairs, YamlTagged
from .utils import decode_yaml, encode_yaml, is_yaml_data


__all__ = [
    "LiteralScalarString",
    "PureDumper",
    "PureLoader",
    "YamlPairs",
    "YamlTagged",
    "decode_yaml",
    "encode_yaml",
    "is_yaml_data",
    "yaml_construct_pairs",
    "yaml_construct_undefined",
    "yaml_literal_str_representer",
    "yaml_represent_pairs",
    "yaml_represent_tagged",
    "yaml_str_representer",
]
