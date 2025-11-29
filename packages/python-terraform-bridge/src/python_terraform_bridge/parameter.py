"""Terraform module parameter definition.

This module provides the TerraformModuleParameter class for defining
input parameters for Terraform modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TerraformModuleParameter:
    """Represents a parameter for a Terraform module.

    This class handles the translation between Python function parameters
    and Terraform variable definitions.

    Attributes:
        name: Parameter name.
        json_encode: Whether to JSON encode the value in triggers.
        base64_encode: Whether to base64 encode the value in triggers.
        default: Default value for the parameter.
        required: Whether the parameter is required.
        description: Human-readable description.
        sensitive: Whether the value is sensitive (masked in logs).
        type: Terraform type (string, bool, number, any, map, list).
        trigger: Custom trigger expression override.
    """

    name: str
    json_encode: bool = field(default=False)
    base64_encode: bool = field(default=False)
    default: Any = field(default=None)
    required: bool = field(default=True)
    description: str | None = field(default=None)
    sensitive: bool = field(default=False)
    type: str | None = field(default=None)
    trigger: str | None = field(default=None)

    def __post_init__(self) -> None:
        """Infer type from default value if not specified."""
        if self.type is not None:
            return

        if isinstance(self.default, str) or self.name.endswith("id"):
            self.type = "string"
        elif isinstance(self.default, bool):
            self.type = "bool"
        elif isinstance(self.default, int):
            self.type = "number"
        elif isinstance(self.default, list):
            self.type = "list(any)"
        elif isinstance(self.default, dict):
            self.type = "map(any)"
        else:
            self.type = "any"

    def get_variable(self) -> dict[str, Any]:
        """Generate Terraform variable block.

        Returns:
            Dictionary suitable for Terraform JSON variable definition.
        """
        variable: dict[str, Any] = {"type": self.type}

        if not self.required:
            variable["default"] = self.default

        if self.description is not None:
            variable["description"] = self.description

        if self.sensitive:
            variable["sensitive"] = True

        return variable

    def get_trigger(self, disable_encoding: bool = False) -> str:
        """Generate Terraform trigger expression.

        Args:
            disable_encoding: Skip JSON/base64 encoding.

        Returns:
            Terraform expression string for use in triggers.
        """
        if self.trigger is not None:
            return self.trigger

        trigger = f"var.{self.name}"

        if self.json_encode and not disable_encoding:
            trigger = f"jsonencode({trigger})"

        if self.base64_encode and not disable_encoding:
            trigger = f"base64encode({trigger})"

        return "${try(nonsensitive(" + trigger + "), " + trigger + ")}"

    @classmethod
    def from_type_hint(
        cls,
        name: str,
        type_hint: Any,
        default: Any = None,
        description: str | None = None,
    ) -> TerraformModuleParameter:
        """Create parameter from Python type hint.

        Args:
            name: Parameter name.
            type_hint: Python type annotation.
            default: Default value.
            description: Parameter description.

        Returns:
            TerraformModuleParameter instance.
        """
        import inspect
        from typing import get_origin

        # Determine if required based on default
        required = default is inspect.Parameter.empty

        # Infer encoding from type hints
        json_encode = False
        base64_encode = False
        tf_type = "any"

        origin = get_origin(type_hint)

        # Handle basic types
        if type_hint is str:
            tf_type = "string"
        elif type_hint is bool:
            tf_type = "bool"
        elif type_hint is int or type_hint is float:
            tf_type = "number"
        # Handle generic types (List[x], Dict[k,v], etc.)
        elif origin is list:
            tf_type = "list(any)"
        elif origin is dict:
            tf_type = "map(any)"
            json_encode = True
            base64_encode = True
        # Handle bare list/dict without generics
        elif type_hint is list:
            tf_type = "list(any)"
        elif type_hint is dict:
            tf_type = "map(any)"
            json_encode = True
            base64_encode = True

        return cls(
            name=name,
            json_encode=json_encode,
            base64_encode=base64_encode,
            default=None if required else default,
            required=required,
            description=description,
            type=tf_type,
        )
