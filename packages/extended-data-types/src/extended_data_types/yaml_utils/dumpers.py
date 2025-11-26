"""This module provides custom YAML dumpers for serializing Python objects to YAML.

It includes a custom YAML dumper class that handles special types such as date, datetime,
and pathlib.Path.
"""

from __future__ import annotations

import datetime
import pathlib

from typing import Any

from yaml import SafeDumper

from .representers import (
    yaml_literal_str_representer,
    yaml_represent_pairs,
    yaml_represent_tagged,
    yaml_str_representer,
)
from .tag_classes import LiteralScalarString, YamlPairs, YamlTagged


class PureDumper(SafeDumper):
    """Custom YAML dumper."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the custom YAML dumper with additional representers.

        Args:
            args (Any): Variable length argument list.
            kwargs (Any): Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.add_representer(str, yaml_str_representer)
        self.add_representer(LiteralScalarString, yaml_literal_str_representer)
        self.add_multi_representer(YamlTagged, yaml_represent_tagged)
        self.add_multi_representer(YamlPairs, yaml_represent_pairs)
        self.add_representer(
            datetime.date,
            lambda dumper, data: dumper.represent_scalar(
                "tag:yaml.org,2002:timestamp",
                data.isoformat(),
            ),
        )
        self.add_representer(
            datetime.datetime,
            lambda dumper, data: dumper.represent_scalar(
                "tag:yaml.org,2002:timestamp",
                data.isoformat(),
            ),
        )
        self.add_representer(
            pathlib.Path,
            lambda dumper, data: dumper.represent_scalar(
                "tag:yaml.org,2002:str",
                str(data),
            ),
        )

    def ignore_aliases(self, data: Any) -> bool:  # noqa: ARG002
        """Ignore aliases for the given data.

        Args:
            data (Any): The data to check for aliases.

        Returns:
            bool: Always returns True.
        """
        return True
