"""This module provides classes for handling YAML tagged objects and pairs.

It includes a wrapper class for YAML tagged objects and a class to represent YAML pairs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import wrapt


if TYPE_CHECKING:
    from typing_extensions import TypeAlias

    _ObjectProxyBase: TypeAlias = "wrapt.ObjectProxy[Any]"
else:
    _ObjectProxyBase = wrapt.ObjectProxy


class YamlTagged(_ObjectProxyBase):
    """Wrapper class for YAML tagged objects."""

    def __init__(self, tag: str, wrapped: Any) -> None:
        """Initialize YamlTagged object.

        Args:
            tag (str): The tag for the YAML object.
            wrapped (Any): The original object to wrap.
        """
        super().__init__(wrapped)
        self._self_tag = tag

    def __repr__(self) -> str:
        """Represent the YamlTagged object as a string.

        Returns:
            str: String representation of the object.
        """
        return f"{type(self).__name__}({self._self_tag!r}, {self.__wrapped__!r})"

    @property
    def tag(self) -> str:
        """Get the tag of the YamlTagged object.

        Returns:
            str: The tag of the object.
        """
        return self._self_tag


class YamlPairs(list[Any]):
    """Class to represent YAML pairs."""

    def __repr__(self) -> str:
        """Represent the YamlPairs object as a string.

        Returns:
            str: String representation of the object.
        """
        return f"{type(self).__name__}({super().__repr__()})"


class LiteralScalarString(str):
    """String subclass that will be represented as a literal block scalar in YAML.

    This class is used to preserve multiline strings and command strings
    in YAML output using the literal block style (|).
    """

    __slots__ = ()

    def __repr__(self) -> str:
        """Represent the LiteralScalarString object as a string.

        Returns:
            str: String representation of the object.
        """
        return f"{type(self).__name__}({super().__repr__()})"
