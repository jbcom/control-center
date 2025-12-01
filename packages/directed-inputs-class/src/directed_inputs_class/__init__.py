"""Directed Inputs Class.

This package provides tools for managing and processing directed inputs from
various sources like environment variables, stdin, and predefined dictionaries.
"""

from __future__ import annotations

from .__main__ import DirectedInputsClass
from .decorators import directed_inputs, input_config


__version__ = "202511.9.0"

__all__ = ["DirectedInputsClass", "directed_inputs", "input_config"]
