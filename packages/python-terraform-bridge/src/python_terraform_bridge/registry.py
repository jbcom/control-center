"""Terraform method registry with decorator-based registration.

This module provides a modern decorator-based approach for registering
methods as Terraform data sources or null resources.

Example:
    from python_terraform_bridge import TerraformRegistry, data_source

    registry = TerraformRegistry()

    class MyService(DirectedInputsClass):
        @registry.data_source(key="users", module_class="myservice")
        def list_users(self, domain: str = None) -> dict:
            '''List all users in the organization.'''
            return {"user1": {...}, "user2": {...}}

    # Generate Terraform modules
    registry.generate_modules("./terraform-modules")
"""

from __future__ import annotations

import functools
import inspect
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path  # noqa: TC003 - used at runtime for Path.open()
from typing import Any, TypeVar

from python_terraform_bridge.module_resources import TerraformModuleResources
from python_terraform_bridge.parameter import TerraformModuleParameter

F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class TerraformMethodConfig:
    """Configuration for a registered Terraform method.

    Attributes:
        method: The original method.
        method_name: Name of the method.
        module_type: Type of Terraform module (data_source, null_resource).
        key: Output key name.
        module_class: Module class/namespace prefix.
        description: Short description.
        parameters: List of parameter definitions.
        env_variables: Environment variables to read.
        sensitive_env_variables: Sensitive environment variables.
        extra_outputs: Additional output keys.
        required_providers: Additional Terraform providers.
        generation_forbidden: Whether to skip module generation.
        always_run: Whether to always trigger execution.
        plaintext_output: Whether output is plaintext (vs base64 JSON).
    """

    method: Callable[..., Any]
    method_name: str
    module_type: str = "data_source"
    key: str | None = None
    module_class: str | None = None
    description: str | None = None
    parameters: list[TerraformModuleParameter] = field(default_factory=list)
    env_variables: dict[str, dict[str, Any]] = field(default_factory=dict)
    sensitive_env_variables: dict[str, dict[str, Any]] = field(default_factory=dict)
    extra_outputs: dict[str, dict[str, Any]] = field(default_factory=dict)
    required_providers: dict[str, dict[str, str]] = field(default_factory=dict)
    generation_forbidden: bool = False
    always_run: bool = False
    plaintext_output: bool = False

    def __post_init__(self) -> None:
        """Extract description from docstring if not provided."""
        if self.description is None and self.method.__doc__:
            # First line of docstring
            self.description = self.method.__doc__.strip().split("\n")[0]

        if self.key is None:
            self.key = self.method_name

    def to_module_resources(
        self,
        terraform_modules_dir: str = "terraform-modules",
        binary_name: str = "python -m python_terraform_bridge",
    ) -> TerraformModuleResources:
        """Convert to TerraformModuleResources.

        Args:
            terraform_modules_dir: Output directory for modules.
            binary_name: Command to invoke the Python runtime.

        Returns:
            TerraformModuleResources instance.
        """
        # Build generator parameters
        generator_params = {
            "key": self.key,
            "type": self.module_type,
            "plaintext_output": self.plaintext_output,
        }
        if self.always_run:
            generator_params["always"] = True

        # Build docstring for compatibility
        docstring_lines = [self.description or ""]
        docstring_lines.append(
            f"generator=key: {self.key}, type: {self.module_type}"
            + (f", module_class: {self.module_class}" if self.module_class else "")
        )

        for param in self.parameters:
            parts = [f"name: {param.name}"]
            if param.type:
                parts.append(f"type: {param.type}")
            if not param.required:
                parts.append("required: false")
                if param.default is not None:
                    parts.append(f'default: "{param.default}"')
            if param.description:
                parts.append(f'description: "{param.description}"')
            if param.sensitive:
                parts.append("sensitive: true")
            docstring_lines.append(", ".join(parts))

        for env_name, env_config in self.env_variables.items():
            parts = [f"name: {env_name}"]
            if env_config.get("required"):
                parts.append("required: true")
            docstring_lines.append("env=" + ", ".join(parts))

        for env_name, env_config in self.sensitive_env_variables.items():
            parts = [f"name: {env_name}", "sensitive: true"]
            if env_config.get("required"):
                parts.append("required: true")
            docstring_lines.append("env=" + ", ".join(parts))

        docstring = "\n".join(docstring_lines)

        resources = TerraformModuleResources(
            module_name=self.method_name,
            docstring=docstring,
            module_type=self.module_type,
            terraform_modules_dir=terraform_modules_dir,
            terraform_modules_class=self.module_class,
            binary_name=binary_name,
        )

        # Override with explicit settings
        resources.generator_parameters.update(generator_params)
        resources.extra_outputs.update(self.extra_outputs)
        resources.required_providers.update(self.required_providers)
        resources.generation_forbidden = self.generation_forbidden

        return resources


class TerraformRegistry:
    """Registry for Terraform-enabled methods.

    This class maintains a registry of methods that can be exposed as
    Terraform external data sources or null resources.

    Example:
        registry = TerraformRegistry()

        class MyService(DirectedInputsClass):
            @registry.data_source(key="users")
            def list_users(self) -> dict:
                return {}

        # Generate modules
        registry.generate_modules("./modules")

        # Or run as CLI
        registry.run()
    """

    def __init__(self, name: str = "default") -> None:
        """Initialize the registry.

        Args:
            name: Registry name for identification.
        """
        self.name = name
        self._methods: dict[str, TerraformMethodConfig] = {}

    def register(
        self,
        method_name: str | None = None,
        module_type: str = "data_source",
        key: str | None = None,
        module_class: str | None = None,
        description: str | None = None,
        parameters: list[TerraformModuleParameter] | None = None,
        env_variables: dict[str, dict[str, Any]] | None = None,
        sensitive_env_variables: dict[str, dict[str, Any]] | None = None,
        extra_outputs: dict[str, dict[str, Any]] | None = None,
        required_providers: dict[str, dict[str, str]] | None = None,
        generation_forbidden: bool = False,
        always_run: bool = False,
        plaintext_output: bool = False,
    ) -> Callable[[F], F]:
        """Register a method with the Terraform bridge.

        Args:
            method_name: Override method name.
            module_type: Type of module (data_source, null_resource).
            key: Output key name.
            module_class: Module class prefix.
            description: Short description.
            parameters: Parameter definitions (auto-inferred if None).
            env_variables: Environment variables.
            sensitive_env_variables: Sensitive environment variables.
            extra_outputs: Additional outputs.
            required_providers: Additional providers.
            generation_forbidden: Skip module generation.
            always_run: Always trigger execution.
            plaintext_output: Output as plaintext.

        Returns:
            Decorator function.
        """

        def decorator(func: F) -> F:
            nonlocal method_name, parameters

            if method_name is None:
                method_name = func.__name__

            # Auto-infer parameters from signature
            if parameters is None:
                parameters = self._infer_parameters(func)

            config = TerraformMethodConfig(
                method=func,
                method_name=method_name,
                module_type=module_type,
                key=key or method_name,
                module_class=module_class,
                description=description,
                parameters=parameters or [],
                env_variables=env_variables or {},
                sensitive_env_variables=sensitive_env_variables or {},
                extra_outputs=extra_outputs or {},
                required_providers=required_providers or {},
                generation_forbidden=generation_forbidden,
                always_run=always_run,
                plaintext_output=plaintext_output,
            )

            self._methods[method_name] = config

            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                return func(*args, **kwargs)

            # Attach registry info to wrapper
            wrapper._terraform_config = config  # type: ignore
            return wrapper  # type: ignore

        return decorator

    def data_source(
        self,
        key: str | None = None,
        module_class: str | None = None,
        **kwargs: Any,
    ) -> Callable[[F], F]:
        """Register a method as a Terraform data source.

        Args:
            key: Output key name.
            module_class: Module class prefix.
            **kwargs: Additional registration options.

        Returns:
            Decorator function.
        """
        return self.register(
            module_type="data_source",
            key=key,
            module_class=module_class,
            **kwargs,
        )

    def null_resource(
        self,
        module_class: str | None = None,
        **kwargs: Any,
    ) -> Callable[[F], F]:
        """Register a method as a Terraform null_resource.

        Args:
            module_class: Module class prefix.
            **kwargs: Additional registration options.

        Returns:
            Decorator function.
        """
        return self.register(
            module_type="null_resource",
            module_class=module_class,
            **kwargs,
        )

    def _infer_parameters(
        self,
        func: Callable[..., Any],
    ) -> list[TerraformModuleParameter]:
        """Infer Terraform parameters from function signature.

        Args:
            func: Function to inspect.

        Returns:
            List of inferred parameters.
        """
        sig = inspect.signature(func)
        hints = getattr(func, "__annotations__", {})
        parameters = []

        for name, param in sig.parameters.items():
            if name in ("self", "cls"):
                continue

            type_hint = hints.get(name, str)

            parameters.append(
                TerraformModuleParameter.from_type_hint(
                    name=name,
                    type_hint=type_hint,
                    default=param.default,
                )
            )

        return parameters

    def get_method(self, method_name: str) -> TerraformMethodConfig | None:
        """Get a registered method by name.

        Args:
            method_name: Name of the method.

        Returns:
            Method configuration or None.
        """
        return self._methods.get(method_name)

    def list_methods(self) -> dict[str, str]:
        """List all registered methods with descriptions.

        Returns:
            Dict mapping method names to descriptions.
        """
        return {name: config.description or "" for name, config in self._methods.items()}

    def generate_modules(
        self,
        output_dir: str = "terraform-modules",
        binary_name: str = "python -m python_terraform_bridge",
    ) -> dict[str, Path]:
        """Generate Terraform modules for all registered methods.

        Args:
            output_dir: Directory to write modules.
            binary_name: Command to invoke the runtime.

        Returns:
            Dict mapping method names to generated module paths.
        """
        generated: dict[str, Path] = {}

        for name, config in self._methods.items():
            if config.generation_forbidden:
                continue

            resources = config.to_module_resources(
                terraform_modules_dir=output_dir,
                binary_name=binary_name,
            )

            module_path = resources.get_module_path()
            module_json = resources.get_mixed()

            # Ensure directory exists
            module_path.parent.mkdir(parents=True, exist_ok=True)

            # Write module
            with module_path.open("w") as f:
                json.dump(module_json, f, indent=2)

            generated[name] = module_path

        return generated

    def get_all_resources(
        self,
        terraform_modules_dir: str = "terraform-modules",
        binary_name: str = "python -m python_terraform_bridge",
    ) -> list[TerraformModuleResources]:
        """Get TerraformModuleResources for all registered methods.

        Args:
            terraform_modules_dir: Output directory for modules.
            binary_name: Command to invoke the runtime.

        Returns:
            List of TerraformModuleResources instances.
        """
        return [
            config.to_module_resources(terraform_modules_dir, binary_name)
            for config in self._methods.values()
        ]


# Global default registry
_default_registry = TerraformRegistry("global")


def data_source(
    key: str | None = None,
    module_class: str | None = None,
    **kwargs: Any,
) -> Callable[[F], F]:
    """Register a method as a Terraform data source on the global registry.

    Args:
        key: Output key name.
        module_class: Module class prefix.
        **kwargs: Additional options.

    Returns:
        Decorator function.
    """
    return _default_registry.data_source(key=key, module_class=module_class, **kwargs)


def null_resource(
    module_class: str | None = None,
    **kwargs: Any,
) -> Callable[[F], F]:
    """Register a method as a Terraform null_resource on the global registry.

    Args:
        module_class: Module class prefix.
        **kwargs: Additional options.

    Returns:
        Decorator function.
    """
    return _default_registry.null_resource(module_class=module_class, **kwargs)


def get_global_registry() -> TerraformRegistry:
    """Get the global default registry.

    Returns:
        The global TerraformRegistry instance.
    """
    return _default_registry
