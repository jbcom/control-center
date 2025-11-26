"""Type definitions for the logging module."""

from __future__ import annotations

import sys

from typing import Literal


if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

LogLevel: TypeAlias = Literal["debug", "info", "warning", "error", "fatal", "critical"]
"""A type alias representing the valid log levels used in the logging module.

Valid values are:
- "debug"
- "info"
- "warning"
- "error"
- "fatal"
- "critical"
"""
