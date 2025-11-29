"""Decorator-based input handling for DirectedInputsClass consumers.

This module provides two decorators:

1. ``@directed_inputs`` - class decorator that wires DirectedInputsClass style
   input loading (environment variables, stdin, explicit mappings) into plain
   Python classes without requiring inheritance.
2. ``@input_config`` - method decorator that allows fine-grained control over
   how individual parameters are resolved from the input context
   (renaming, decoding, required flags, etc.).

The decorated classes automatically receive lazily-evaluated input contexts and
runtime metadata that can be consumed by other packages (e.g.
python-terraform-bridge) to instantiate the classes safely.
"""

from __future__ import annotations

import functools
import inspect

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

from directed_inputs_class.__main__ import DirectedInputsClass


if TYPE_CHECKING:
    from collections.abc import Mapping, MutableMapping

__all__ = ["DirectedInputsMetadata", "InputConfig", "directed_inputs", "input_config"]

# Sentinel object used to differentiate between "no default provided" and
# "explicitly default to None".
_MISSING = object()

# Reserved keyword arguments consumed by the decorator wrapper. The names are
# intentionally obscure to avoid collisions with user-defined parameters.
_CONFIG_KWARG = "_directed_inputs_config"
_RUNTIME_LOGGING_KWARG = "_directed_inputs_runtime_logging"
_RUNTIME_SETTINGS_KWARG = "_directed_inputs_runtime_settings"

# Error messages
_ERR_CONTEXT_NOT_INITIALIZED = (
    "directed_inputs decorator not initialized on this instance"
)
_ERR_CONTEXT_MISSING = "directed_inputs context missing on instance"


@dataclass(frozen=True)
class InputConfig:
    """Configuration for resolving a single method parameter from inputs."""

    parameter_name: str
    source_name: str | None = None
    required: bool = False
    default: Any = _MISSING
    decode_from_json: bool = False
    decode_from_yaml: bool = False
    decode_from_base64: bool = False
    allow_none: bool = True
    is_bool: bool = False
    is_integer: bool = False
    is_float: bool = False
    is_path: bool = False
    is_datetime: bool = False

    def resolve(self, provider: DirectedInputsClass) -> Any | object:
        """Resolve a value from the provided DirectedInputsClass instance."""
        key = self.source_name or self.parameter_name
        default_value = None if self.default is _MISSING else self.default
        source_present = key in provider.inputs

        if self.decode_from_json or self.decode_from_yaml or self.decode_from_base64:
            value = provider.decode_input(
                key,
                default=default_value,
                required=self.required,
                decode_from_json=self.decode_from_json,
                decode_from_yaml=self.decode_from_yaml,
                decode_from_base64=self.decode_from_base64,
                allow_none=self.allow_none,
            )
        else:
            value = provider.get_input(
                key,
                default=default_value,
                required=self.required,
                is_bool=self.is_bool,
                is_integer=self.is_integer,
                is_float=self.is_float,
                is_path=self.is_path,
                is_datetime=self.is_datetime,
            )

        if (
            value is None
            and not source_present
            and self.default is _MISSING
            and not self.required
        ):
            return _MISSING

        return value


@dataclass(frozen=True)
class DirectedInputsMetadata:
    """Metadata exposed on decorated classes for runtime integrations."""

    options: dict[str, Any] = field(default_factory=dict)


class InputContext:
    """Lightweight wrapper around DirectedInputsClass instantiation."""

    def __init__(
        self,
        *,
        inputs: Mapping[str, Any] | None = None,
        from_environment: bool = True,
        from_stdin: bool = False,
        env_prefix: str | None = None,
        strip_env_prefix: bool = False,
    ):
        self._options: dict[str, Any] = {
            "inputs": dict(inputs) if inputs else None,
            "from_environment": from_environment,
            "from_stdin": from_stdin,
            "env_prefix": env_prefix,
            "strip_env_prefix": strip_env_prefix,
        }
        self._instance: DirectedInputsClass | None = None

    def refresh(self, **overrides: Any) -> None:
        """Refresh the context with new DirectedInputsClass options."""
        self._options.update(overrides)
        self._instance = None

    @property
    def options(self) -> dict[str, Any]:
        """Current configuration (copy) used for instantiation."""
        return dict(self._options)

    def resolve(self, config: InputConfig) -> Any | object:
        """Resolve a parameter value using the provided configuration."""
        return config.resolve(self._ensure_instance())

    @property
    def directed_inputs(self) -> DirectedInputsClass:
        """Return the lazily-instantiated DirectedInputsClass instance."""
        return self._ensure_instance()

    def _ensure_instance(self) -> DirectedInputsClass:
        if self._instance is None:
            kwargs = {k: v for k, v in self._options.items() if v is not None}
            self._instance = DirectedInputsClass(**kwargs)
        return self._instance


def input_config(
    parameter_name: str, **config_kwargs: Any
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Configure how a method parameter is populated from inputs."""
    default_value = config_kwargs.pop("default", _MISSING)

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        config_map: MutableMapping[str, InputConfig] = getattr(
            func, "_directed_inputs_configs", {}
        ).copy()
        config_map[parameter_name] = InputConfig(
            parameter_name=parameter_name,
            default=default_value,
            **config_kwargs,
        )
        func._directed_inputs_configs = config_map  # noqa: SLF001
        return func

    return decorator


def directed_inputs(
    *,
    inputs: Mapping[str, Any] | None = None,
    from_environment: bool = True,
    from_stdin: bool = False,
    env_prefix: str | None = None,
    strip_env_prefix: bool = False,
) -> Callable[[type[Any]], type[Any]]:
    """Class decorator that injects DirectedInputsClass behavior."""
    base_options = {
        "inputs": inputs,
        "from_environment": from_environment,
        "from_stdin": from_stdin,
        "env_prefix": env_prefix,
        "strip_env_prefix": strip_env_prefix,
    }

    def decorator(cls: type[Any]) -> type[Any]:
        if getattr(cls, "__directed_inputs_enabled__", False):
            return cls

        metadata = DirectedInputsMetadata(
            options={k: v for k, v in base_options.items() if v is not None}
        )
        cls.__directed_inputs_enabled__ = True
        cls.__directed_inputs_metadata__ = metadata

        original_init = cls.__init__

        @functools.wraps(original_init)
        def wrapped_init(self: Any, *args: Any, **kwargs: Any) -> None:
            runtime_logging = kwargs.pop(_RUNTIME_LOGGING_KWARG, None)
            runtime_settings = kwargs.pop(_RUNTIME_SETTINGS_KWARG, None)
            overrides = kwargs.pop(_CONFIG_KWARG, None) or {}

            merged_options = dict(base_options)
            merged_options.update({k: v for k, v in overrides.items() if v is not None})

            self._directed_inputs_context = InputContext(**merged_options)
            self._directed_inputs_runtime_settings = runtime_settings

            if runtime_logging and not hasattr(self, "logging"):
                self.logging = runtime_logging
                self.logger = runtime_logging.logger

            original_init(self, *args, **kwargs)

        cls.__init__ = wrapped_init  # type: ignore[assignment]

        _inject_proxies(cls)
        _wrap_instance_methods(cls)

        return cls

    return decorator


def _inject_proxies(cls: type[Any]) -> None:
    """Inject helper properties/methods for interacting with the context."""

    def _get_context(self: Any) -> InputContext:
        context = getattr(self, "_directed_inputs_context", None)
        if context is None:
            raise AttributeError(_ERR_CONTEXT_NOT_INITIALIZED)
        return context

    if not hasattr(cls, "directed_inputs"):

        @property
        def directed_inputs(self: Any) -> DirectedInputsClass:
            return _get_context(self).directed_inputs

        cls.directed_inputs = directed_inputs

    if not hasattr(cls, "refresh_inputs"):

        def refresh_inputs(self: Any, **overrides: Any) -> None:
            _get_context(self).refresh(**overrides)

        cls.refresh_inputs = refresh_inputs


def _wrap_instance_methods(cls: type[Any]) -> None:
    """Wrap instance methods so missing parameters are auto-populated."""
    for name, attribute in list(cls.__dict__.items()):
        if _should_skip_method(name, attribute):
            continue

        function = attribute
        configs = getattr(function, "_directed_inputs_configs", {})
        signature = inspect.signature(function)
        is_coroutine = inspect.iscoroutinefunction(function)

        def _create_wrapper(
            fn: Callable[..., Any],
            sig: inspect.Signature,
            fn_configs: dict[str, InputConfig],
            coroutine: bool,
        ) -> Callable[..., Any]:
            def _prepare_bound(
                instance: Any, args: tuple[Any, ...], kwargs: dict[str, Any]
            ) -> inspect.BoundArguments:
                bound = sig.bind_partial(instance, *args, **kwargs)
                for param_name, parameter in sig.parameters.items():
                    if param_name == "self" or param_name in bound.arguments:
                        continue
                    if parameter.kind in (
                        inspect.Parameter.VAR_POSITIONAL,
                        inspect.Parameter.VAR_KEYWORD,
                    ):
                        continue

                    config = fn_configs.get(param_name) or InputConfig(
                        parameter_name=param_name
                    )
                    context = getattr(instance, "_directed_inputs_context", None)
                    if context is None:
                        raise AttributeError(_ERR_CONTEXT_MISSING)
                    value = context.resolve(config)
                    if value is _MISSING:
                        continue
                    bound.arguments[param_name] = value

                bound.apply_defaults()
                return bound

            if coroutine:

                @functools.wraps(fn)
                async def async_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
                    bound = _prepare_bound(self, args, kwargs)
                    return await fn(*bound.args, **bound.kwargs)

                return async_wrapper

            @functools.wraps(fn)
            def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
                bound = _prepare_bound(self, args, kwargs)
                return fn(*bound.args, **bound.kwargs)

            return wrapper

        wrapped = _create_wrapper(function, signature, configs, is_coroutine)
        setattr(cls, name, wrapped)


def _should_skip_method(name: str, attribute: Any) -> bool:
    """Determine whether an attribute should be wrapped."""
    if name.startswith("_"):
        return True

    if isinstance(attribute, (staticmethod, classmethod, property)):
        return True

    return not inspect.isfunction(attribute)
