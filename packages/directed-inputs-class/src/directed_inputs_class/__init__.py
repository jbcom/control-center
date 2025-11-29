"""Directed Inputs Class.

This package provides tools for managing and processing directed inputs from
various sources like environment variables, stdin, and predefined dictionaries.

Two APIs are provided:

1. **Decorator-based (recommended)**:
   ```python
   from directed_inputs_class import directed_inputs, input_config

   @directed_inputs(from_stdin=True)
   class MyService:
       def list_users(self, domain: str | None = None) -> dict:
           # domain is automatically populated from stdin/env
           return {"users": [...]}
   ```

2. **Inheritance-based (legacy)**:
   ```python
   from directed_inputs_class import DirectedInputsClass

   class MyService(DirectedInputsClass):
       def list_users(self, domain: str = None) -> dict:
           domain = self.get_input("domain", domain)
           return {"users": [...]}
   ```
"""

from __future__ import annotations

from .__main__ import DirectedInputsClass
from .decorators import InputConfig, InputContext, directed_inputs, input_config


__version__ = "202511.6.0"

__all__ = [
    "DirectedInputsClass",
    "InputConfig",
    "InputContext",
    "directed_inputs",
    "input_config",
]
