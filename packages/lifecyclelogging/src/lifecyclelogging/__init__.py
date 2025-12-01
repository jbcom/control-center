"""Lifecycle logging package for comprehensive application logging.

This package provides utilities for managing application lifecycle logs, including
configurable logging for console and file outputs, and clean exit functionality.
"""

__version__ = "202511.8.0"

from .logging import ExitRunError, KeyTransform, Logging


__all__ = ["ExitRunError", "KeyTransform", "Logging"]
