"""Decorator-based input handling for Python classes.

This module provides a modern, composable approach to input handling
using decorators instead of inheritance.

Example:
    from directed_inputs_class import directed_inputs

    @directed_inputs(from_stdin=True)
    class MyService:
        def list_users(self, domain: str | None = None) -> dict:
            # domain is automatically populated from stdin/env
            return {"users": [...]}

    # Or with explicit configuration:
    @directed_inputs
    class MyService:
        @input_config(source="env", name="API_DOMAIN", required=True)
        def list_users(self, domain: str) -> dict:
            return {"users": [...]}
"""

from __future__ import annotations

import functools
import inspect
import json
import os
import sys
import types
import typing

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar, Union, get_args, get_origin, overload

from case_insensitive_dict import CaseInsensitiveDict
from deepmerge import Merger
from extended_data_types import (
    base64_decode,
    decode_json,
    decode_yaml,
    is_nothing,
    strtobool,
    strtodatetime,
    strtofloat,
    strtoint,
    strtopath,
)


if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

C = TypeVar("C", bound=type)
F = TypeVar("F", bound="Callable[..., Any]")

STDIN_MAX_BYTES = 1024 * 1024  # 1 MiB safety limit for stdin ingestion


@dataclass
class InputConfig:
    """Configuration for a single input parameter.

    Attributes:
        name: The parameter name.
        source_name: Name to look up in inputs (defaults to parameter name).
        aliases: Alternative names to search for.
        required: Whether the input is required.
        default: Default value if not found.
        decode_base64: Decode from base64.
        decode_json: Parse as JSON.
        decode_yaml: Parse as YAML.
        coerce_type: Target type for coercion (inferred from type hint).
    """

    name: str
    source_name: str | None = None
    aliases: list[str] = field(default_factory=list)
    required: bool = False
    default: Any = None
    decode_base64: bool = False
    decode_json: bool = False
    decode_yaml: bool = False
    coerce_type: type | None = None


@dataclass
class InputContext:
    """Runtime context for input handling.

    This is attached to decorated class instances and manages
    the input dictionary and configuration.
    """

    inputs: CaseInsensitiveDict[str, Any] = field(
        default_factory=lambda: CaseInsensitiveDict()
    )
    frozen_inputs: CaseInsensitiveDict[str, Any] = field(
        default_factory=lambda: CaseInsensitiveDict()
    )
    from_stdin: bool = False
    from_env: bool = True
    env_prefix: str | None = None
    strip_env_prefix: bool = False

    _merger: Merger = field(
        default_factory=lambda: Merger(
            [(list, ["append"]), (dict, ["merge"]), (set, ["union"])],
            ["override"],
            ["override"],
        )
    )

    def get(
        self,
        key: str,
        default: Any = None,
        aliases: list[str] | None = None,
        required: bool = False,
    ) -> Any:
        """Get a value from inputs, checking aliases."""
        keys_to_check = [key]
        if aliases:
            keys_to_check.extend(aliases)

        for k in keys_to_check:
            value = self.inputs.get(k)
            if not is_nothing(value):
                return value

        if required and is_nothing(default):
            msg = f"Required input '{key}' not found in inputs"
            raise ValueError(msg)

        return default

    def merge(self, new_inputs: Mapping[str, Any]) -> None:
        """Merge new inputs into current inputs."""
        merged = self._merger.merge(dict(self.inputs), dict(new_inputs))
        self.inputs = CaseInsensitiveDict(merged)


_UNION_TYPE = getattr(types, "UnionType", None)

_STRING_TYPE_ALIASES: dict[str, type] = {
    "str": str,
    "builtins.str": str,
    "int": int,
    "builtins.int": int,
    "float": float,
    "builtins.float": float,
    "bool": bool,
    "builtins.bool": bool,
    "dict": dict,
    "Dict": dict,
    "typing.Dict": dict,
    "list": list,
    "List": list,
    "typing.List": list,
    "Path": Path,
    "pathlib.Path": Path,
    "datetime": datetime,
    "datetime.datetime": datetime,
}


def _normalize_string_type(type_str: str) -> type | None:
    """Best-effort resolution of type hints represented as strings.

    Python 3.9 stores annotations as strings when using
    `from __future__ import annotations`, and evaluating expressions like
    ``str | None`` raises TypeError before 3.10. This helper extracts the
    underlying concrete type so downstream coercion logic can operate.
    """
    cleaned = type_str.strip().strip("\"'")
    if not cleaned or cleaned in {"None", "NoneType", "type(None)"}:
        return None

    lowered = cleaned.lower()
    if lowered.startswith(("typing.optional[", "optional[")):
        inner = cleaned.split("[", 1)[1].rsplit("]", 1)[0]
        return _normalize_string_type(inner)

    if "|" in cleaned:
        parts = [part.strip() for part in cleaned.split("|")]
        for part in parts:
            resolved = _normalize_string_type(part)
            if resolved is not None:
                return resolved
        return None

    if "[" in cleaned:
        cleaned = cleaned.split("[", 1)[0].strip()

    if cleaned in _STRING_TYPE_ALIASES:
        return _STRING_TYPE_ALIASES[cleaned]

    if "." in cleaned:
        suffix = cleaned.split(".")[-1]
        return _STRING_TYPE_ALIASES.get(suffix)

    return None


def _resolve_type_hint(target_type: Any) -> type | None:
    """Resolve various typing representations to a concrete Python type."""
    if target_type is None or target_type is type(None):
        return None

    if isinstance(target_type, str):
        return _normalize_string_type(target_type)

    forward_ref = getattr(typing, "ForwardRef", None)
    if forward_ref is not None and isinstance(target_type, forward_ref):
        return _normalize_string_type(target_type.__forward_arg__)  # type: ignore[attr-defined]

    origin = get_origin(target_type)
    if origin is Union or (_UNION_TYPE is not None and origin is _UNION_TYPE):
        for arg in get_args(target_type):
            resolved = _resolve_type_hint(arg)
            if resolved is not None:
                return resolved
        return None

    if _UNION_TYPE is not None and isinstance(target_type, _UNION_TYPE):
        for arg in getattr(target_type, "__args__", ()):
            resolved = _resolve_type_hint(arg)
            if resolved is not None:
                return resolved
        return None

    return target_type


def _load_stdin() -> dict[str, Any]:
    """Load inputs from stdin as JSON.

    Limited to STDIN_MAX_BYTES to prevent denial-of-service attacks.
    """
    if strtobool(os.getenv("OVERRIDE_STDIN", "False")):
        return {}

    try:
        # Read exactly the limit
        stdin_data = sys.stdin.read(STDIN_MAX_BYTES)
        if is_nothing(stdin_data):
            return {}

        # Check if there's more data - peek one more byte
        extra = sys.stdin.read(1)
        if extra:
            msg = f"Stdin input exceeds maximum size limit ({STDIN_MAX_BYTES} bytes)"
            raise ValueError(msg)

        return json.loads(stdin_data)
    except (OSError, json.JSONDecodeError):
        return {}


def _load_env(prefix: str | None = None, strip_prefix: bool = False) -> dict[str, str]:
    """Load inputs from environment variables."""
    env = dict(os.environ)
    if prefix is None:
        return env

    return {
        (k[len(prefix) :] if strip_prefix else k): v
        for k, v in env.items()
        if k.startswith(prefix)
    }


def _coerce_value(value: Any, target_type: type | None) -> Any:
    """Coerce a value to the target type."""
    # _resolve_type_hint handles Union types and returns the first non-None type
    target_type = _resolve_type_hint(target_type)
    if target_type is None or value is None:
        return value

    # Type coercion - do this BEFORE isinstance check to handle string -> other type
    # Wrap in try/except to handle conversion failures gracefully
    try:
        if target_type is bool and not isinstance(value, bool):
            return strtobool(value)
        if target_type is int and not isinstance(value, int):
            return strtoint(value)
        if target_type is float and not isinstance(value, float):
            return strtofloat(str(value))
        if target_type is Path and not isinstance(value, Path):
            return strtopath(str(value))
        if target_type is datetime and not isinstance(value, datetime):
            return strtodatetime(str(value))
        if target_type is dict and isinstance(value, str):
            return decode_json(value)
        if target_type is list and isinstance(value, str):
            return decode_json(value)
    except (ValueError, TypeError):
        # Coercion failed, return original value
        return value

    # Now check if already correct type (safely)
    try:
        if isinstance(value, target_type):
            return value
    except TypeError:
        # target_type isn't a valid type for isinstance, skip
        pass

    # Final fallback - try to coerce to string if that's the target
    if target_type is str:
        return str(value)

    return value


def _decode_value(
    value: Any,
    *,
    decode_base64: bool = False,
    decode_from_json: bool = False,
    decode_from_yaml: bool = False,
) -> Any:
    """Decode a value from various formats."""
    if value is None or not isinstance(value, str):
        return value

    if decode_base64:
        value = base64_decode(
            value,
            unwrap_raw_data=decode_from_json or decode_from_yaml,
            encoding="json"
            if decode_from_json
            else ("yaml" if decode_from_yaml else None),
        )

    if decode_from_yaml:
        value = decode_yaml(value)
    elif decode_from_json:
        value = decode_json(value)

    return value


def _get_param_config(
    param: inspect.Parameter,
    type_hints: dict[str, Any],
    method_configs: dict[str, InputConfig],
) -> InputConfig:
    """Build InputConfig for a parameter from hints and explicit config."""
    name = param.name

    # Check for explicit configuration
    if name in method_configs:
        config = method_configs[name]
        # Fill in type from hints if not set
        if config.coerce_type is None and name in type_hints:
            config.coerce_type = type_hints[name]
        return config

    # Build from type hints and defaults
    type_hint = type_hints.get(name)
    has_default = param.default is not inspect.Parameter.empty
    default = param.default if has_default else None

    return InputConfig(
        name=name,
        required=not has_default,
        default=default,
        coerce_type=type_hint,
    )


def _wrap_method(
    method: Callable[..., Any],
    method_configs: dict[str, InputConfig],
) -> Callable[..., Any]:
    """Wrap a method to auto-populate arguments from inputs."""
    sig = inspect.signature(method)

    # Use get_type_hints to properly resolve string annotations
    try:
        type_hints = typing.get_type_hints(method)
    except (NameError, AttributeError, TypeError):
        # Fallback to raw annotations if get_type_hints fails
        type_hints = getattr(method, "__annotations__", {})

    @functools.wraps(method)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        # Get the input context from the instance
        ctx: InputContext = getattr(self, "_input_context", None)
        if ctx is None:
            # No context, call method directly
            return method(self, *args, **kwargs)

        # Build kwargs from inputs for parameters not already provided
        bound = sig.bind_partial(self, *args, **kwargs)
        bound.apply_defaults()

        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            if param_name in bound.arguments and param_name in kwargs:
                # Explicitly provided - skip
                continue

            config = _get_param_config(param, type_hints, method_configs)

            # Get value from inputs
            value = ctx.get(
                config.source_name or config.name,
                default=config.default,
                aliases=config.aliases,
                required=False,  # We'll check required after coercion
            )

            # Decode if configured
            if value is not None:
                value = _decode_value(
                    value,
                    decode_base64=config.decode_base64,
                    decode_from_json=config.decode_json,
                    decode_from_yaml=config.decode_yaml,
                )

            # Coerce to target type
            value = _coerce_value(value, config.coerce_type)

            # Check required after coercion
            if config.required and is_nothing(value):
                msg = f"Required input '{config.name}' not found"
                raise ValueError(msg)

            # Only set if we got a value (or it's required)
            if value is not None or config.required:
                bound.arguments[param_name] = value

        return method(*bound.args, **bound.kwargs)

    # Preserve original for introspection
    wrapper.__wrapped__ = method  # type: ignore[attr-defined]
    return wrapper


# Storage for method-level configurations
_METHOD_CONFIGS: dict[int, dict[str, InputConfig]] = {}


def input_config(
    name: str | None = None,
    *,
    source_name: str | None = None,
    aliases: list[str] | None = None,
    required: bool = False,
    default: Any = None,
    decode_base64: bool = False,
    decode_json: bool = False,
    decode_yaml: bool = False,
) -> Callable[[F], F]:
    """Decorator to configure input handling for a specific parameter.

    Can be stacked multiple times for different parameters.

    Args:
        name: Parameter name to configure. If None, applies to first parameter.
        source_name: Name to look up in inputs.
        aliases: Alternative names to search for.
        required: Whether the input is required.
        default: Default value.
        decode_base64: Decode from base64.
        decode_json: Parse as JSON.
        decode_yaml: Parse as YAML.

    Example:
        @input_config("domain", source_name="API_DOMAIN", required=True)
        @input_config("limit", default=100)
        def list_users(self, domain: str, limit: int = 100) -> dict:
            ...
    """

    def decorator(func: F) -> F:
        method_id = id(func)
        if method_id not in _METHOD_CONFIGS:
            _METHOD_CONFIGS[method_id] = {}

        # If no name specified, we'll resolve it later
        param_name = name or "_default_"
        _METHOD_CONFIGS[method_id][param_name] = InputConfig(
            name=param_name,
            source_name=source_name,
            aliases=aliases or [],
            required=required,
            default=default,
            decode_base64=decode_base64,
            decode_json=decode_json,
            decode_yaml=decode_yaml,
        )

        return func

    return decorator


@overload
def directed_inputs(cls: C) -> C: ...


@overload
def directed_inputs(
    *,
    from_stdin: bool = False,
    from_env: bool = True,
    env_prefix: str | None = None,
    strip_env_prefix: bool = False,
) -> Callable[[C], C]: ...


def directed_inputs(
    cls: C | None = None,
    *,
    from_stdin: bool = False,
    from_env: bool = True,
    env_prefix: str | None = None,
    strip_env_prefix: bool = False,
) -> C | Callable[[C], C]:
    """Class decorator that enables automatic input handling.

    When applied to a class, all methods automatically receive their
    arguments populated from stdin/environment variables based on
    parameter names and type hints.

    Args:
        cls: The class to decorate (when used without parentheses).
        from_stdin: Load inputs from stdin (JSON).
        from_env: Load inputs from environment variables.
        env_prefix: Only load env vars with this prefix.
        strip_env_prefix: Remove prefix from env var names.

    Returns:
        Decorated class with automatic input handling.

    Example:
        @directed_inputs(from_stdin=True)
        class MyService:
            def list_users(self, domain: str | None = None) -> dict:
                # domain is auto-populated from inputs
                return {}

        # Use without parentheses for defaults
        @directed_inputs
        class MyService:
            ...
    """

    def decorator(cls: C) -> C:
        original_init = cls.__init__

        @functools.wraps(original_init)
        def new_init(self: Any, *args: Any, **kwargs: Any) -> None:
            # Create input context
            inputs: dict[str, Any] = {}

            if from_env:
                inputs.update(_load_env(env_prefix, strip_env_prefix))

            if from_stdin:
                inputs.update(_load_stdin())

            # Allow passing inputs directly
            if "inputs" in kwargs:
                extra_inputs = kwargs.pop("inputs")
                if extra_inputs:
                    inputs.update(extra_inputs)

            ctx = InputContext(
                inputs=CaseInsensitiveDict(inputs),
                from_stdin=from_stdin,
                from_env=from_env,
                env_prefix=env_prefix,
                strip_env_prefix=strip_env_prefix,
            )
            self._input_context = ctx

            # Call original init
            original_init(self, *args, **kwargs)

        cls.__init__ = new_init  # type: ignore[method-assign]

        # Wrap all public methods
        for attr_name in dir(cls):
            if attr_name.startswith("_"):
                continue

            attr = getattr(cls, attr_name)
            if not callable(attr) or isinstance(attr, type):
                continue

            # Get method-level configs
            method_id = id(attr)
            method_configs = _METHOD_CONFIGS.get(method_id, {})

            # Wrap the method
            wrapped = _wrap_method(attr, method_configs)
            setattr(cls, attr_name, wrapped)

        return cls

    if cls is not None:
        # Called without parentheses: @directed_inputs
        return decorator(cls)

    # Called with parentheses: @directed_inputs(...)
    return decorator


# Convenience re-exports
__all__ = [
    "InputConfig",
    "InputContext",
    "directed_inputs",
    "input_config",
]
