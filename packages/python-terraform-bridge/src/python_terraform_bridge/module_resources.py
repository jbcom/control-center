"""Terraform module resources generation.

This module provides the TerraformModuleResources class for generating
Terraform module JSON from Python class methods.
"""

from __future__ import annotations

import concurrent.futures
import json
import time
from copy import deepcopy
from pathlib import Path
from shlex import quote as shlex_quote
from shlex import split as shlex_split
from typing import Any

from extended_data_types import is_nothing, strtobool
from tssplit import tssplit

from python_terraform_bridge.parameter import TerraformModuleParameter


def get_json_export_for_chunk(chunk: str) -> tuple[str, Any]:
    """Parse a key:value chunk from docstring annotation."""
    try:
        # Split only on first colon to handle values like "hashicorp/aws"
        k, v = chunk.strip().strip('"').split(":", 1)
    except ValueError as exc:
        raise RuntimeError(f"Failed to get chunks for: {chunk}") from exc

    k = k.strip().strip('"')
    v = v.strip().strip('"')

    try:
        return k, json.loads(v)
    except json.JSONDecodeError:
        return k, v


def drop_empty_blocks(data_blocks: dict[str, Any]) -> dict[str, Any]:
    """Remove empty values from a dictionary."""
    return {k: v for k, v in data_blocks.items() if not is_nothing(v)}


class TerraformModuleResources:
    """Generate Terraform module resources from Python methods.

    This class parses docstring annotations to generate Terraform external_data
    and null_resource modules that call back to Python.

    Docstring format:
        '''Short description.

        generator=key: output_key, module_class: aws

        name: param1, required: true, type: string
        name: param2, required: false, type: string, default: "value"
        '''

    Attributes:
        module_name: Name of the Python method.
        module_type: Type of module (data_source or null_resource).
        docstring: The method's docstring with annotations.
    """

    # Default settings - can be overridden
    DEFAULT_MODULES_DIR = "terraform-modules"
    DEFAULT_NAME_DELIM = "-"
    DEFAULT_BINARY_NAME = "python -m python_terraform_bridge"

    def __init__(
        self,
        module_name: str,
        docstring: str | None,
        module_type: str | None = None,
        module_params: Any = None,
        terraform_modules_dir: str | None = None,
        terraform_modules_class: str | None = None,
        terraform_modules_name_delim: str | None = None,
        binary_name: str | None = None,
    ):
        """Initialize TerraformModuleResources.

        Args:
            module_name: Name of the method/module.
            docstring: Method docstring with annotations.
            module_type: Override module type (data_source, null_resource).
            module_params: Pre-parsed parameters.
            terraform_modules_dir: Output directory for modules.
            terraform_modules_class: Module class prefix.
            terraform_modules_name_delim: Delimiter for module names.
            binary_name: Command to invoke the Python runtime.
        """
        self.terraform_modules_dir = terraform_modules_dir or self.DEFAULT_MODULES_DIR
        self.terraform_modules_name_delim = terraform_modules_name_delim or self.DEFAULT_NAME_DELIM
        self.binary_name = binary_name or self.DEFAULT_BINARY_NAME

        if terraform_modules_class is None:
            terraform_modules_class = ""

        self.terraform_modules_class = terraform_modules_class.removesuffix(
            self.terraform_modules_name_delim
        )

        self.module_name = module_name
        self.module_type = module_type
        self.docstring = docstring
        self.descriptor: str | None = None
        self.module_parameters: list[TerraformModuleParameter] = []
        self.generator_parameters: dict[str, Any] = {}
        self.extra_outputs: dict[str, dict[str, Any]] = {}
        self.sub_keys: dict[str, dict[str, Any]] = {}

        # Environment variable definitions
        self.env_variables: dict[str, dict[str, Any]] = {}
        self.sensitive_env_variables: dict[str, dict[str, Any]] = {}

        self.required_providers: dict[str, dict[str, str]] = {
            "env": {
                "source": "tcarreira/env",
                "version": ">=0.2.0",
            }
        }

        self.copy_variables_to: list[dict[str, Any]] = []
        self.module_parameter_names: set[str] = set()
        self.foreach_modules: dict[Path, str] = {}
        self.foreach_iterator: TerraformModuleParameter | None = None
        self.foreach_from_file_path: TerraformModuleParameter | None = None
        self.foreach_keys: list[str] = []
        self.foreach_values: list[str] = []
        self.foreach_only: list[str] = []
        self.foreach_forbidden: list[str] = []
        self.generation_forbidden: bool = False
        self.foreach_bind_log_file_name_to_key: bool = False

        self._program_args = self._build_program_args()
        self.call = " ".join(shlex_quote(part) for part in self._program_args)

        self.get_module_config()
        self.set_module_params(module_params)
        self.set_required_module_params()

    def _build_program_args(self) -> list[str]:
        """Return a shell-safe argv list for invoking the runtime."""

        binary_parts = shlex_split(self.binary_name)
        return [*binary_parts, str(self.module_name)]

    def get_module_config(self) -> None:
        """Parse docstring to extract module configuration."""
        if self.docstring is None:
            return

        docstring = [line for line in self.docstring.splitlines() if line != ""]

        if len(docstring) == 0:
            return

        self.descriptor = docstring.pop(0)

        if len(docstring) == 0:
            return

        module_params: list[Any] = []

        def split_param(p: str) -> list[str]:
            return tssplit(
                p,
                quote='"',
                quote_keep=True,
                delimiter=",",
            )

        for param in docstring:
            try:
                param = param.strip()
                if is_nothing(param):
                    continue

                if param.startswith("#"):
                    comment = param.lstrip("#").strip().lower()
                    if comment == "noterraform":
                        self.generation_forbidden = True
                    continue

                if param.startswith("generator="):
                    chunks = split_param(param.removeprefix("generator="))
                    for chunk in chunks:
                        k, v = get_json_export_for_chunk(chunk)
                        if k == "plaintext_output":
                            self.generator_parameters[k] = strtobool(v)
                        else:
                            self.generator_parameters[k] = v
                    continue

                if param.startswith("env="):
                    chunks = split_param(param.removeprefix("env="))
                    processed_chunks: dict[str, Any] = {}
                    env_name = None
                    for chunk in chunks:
                        k, v = get_json_export_for_chunk(chunk)
                        if k == "name":
                            env_name = v
                        else:
                            processed_chunks[k] = strtobool(v) if k == "required" else v

                    if not env_name:
                        raise ValueError(f"Environment variable {param} is missing its name")
                    if processed_chunks.get("sensitive", False):
                        self.sensitive_env_variables[env_name] = processed_chunks
                    else:
                        self.env_variables[env_name] = processed_chunks
                    continue

                if param.startswith("extra_output="):
                    chunks = split_param(param.removeprefix("extra_output="))
                    extra_output: dict[str, Any] = {}
                    for chunk in chunks:
                        k, v = get_json_export_for_chunk(chunk)
                        extra_output[k] = v

                    extra_output_key = extra_output.pop("key", None)
                    if is_nothing(extra_output_key):
                        raise RuntimeError(f"Extra output missing key: {param}")

                    self.extra_outputs[extra_output_key] = extra_output
                    continue

                if param.startswith("sub_key="):
                    chunks = split_param(param.removeprefix("sub_key="))
                    sub_key: dict[str, Any] = {}
                    for chunk in chunks:
                        k, v = get_json_export_for_chunk(chunk)
                        sub_key[k] = v

                    sub_key_key = sub_key.pop("key", None)
                    if is_nothing(sub_key_key):
                        raise RuntimeError(f"Sub key missing key: {param}")

                    self.sub_keys[sub_key_key] = sub_key
                    continue

                if param.startswith("required_provider="):
                    chunks = split_param(param.removeprefix("required_provider="))
                    required_provider: dict[str, Any] = {}
                    for chunk in chunks:
                        k, v = get_json_export_for_chunk(chunk)
                        required_provider[k] = v

                    provider_name = required_provider.pop("name", None)
                    if is_nothing(provider_name):
                        raise RuntimeError(f"Required provider missing name: {param}")

                    self.required_providers[provider_name] = required_provider
                    continue

                if param.startswith("copy_variables_to="):
                    chunks = split_param(param.removeprefix("copy_variables_to="))
                    copy_variables_to: dict[str, Any] = {}
                    for chunk in chunks:
                        k, v = get_json_export_for_chunk(chunk)
                        copy_variables_to[k] = v

                    self.copy_variables_to.append(copy_variables_to)
                    continue

                if param.startswith("foreach="):
                    chunks = split_param(param.removeprefix("foreach="))
                    foreach_module_name = f"{self.module_name}s"
                    foreach_module_call = self.module_name
                    foreach_bind_log_file_name_to_key = False

                    for chunk in chunks:
                        k, v = get_json_export_for_chunk(chunk)
                        if k == "module_name":
                            foreach_module_name = v
                        elif k == "module_call":
                            foreach_module_call = v
                        elif k == "bind_log_file_name_to_key":
                            foreach_bind_log_file_name_to_key = strtobool(v)

                    foreach_module_path = self.get_module_path(module_name=foreach_module_name)
                    self.foreach_modules[foreach_module_path] = self.get_module_name(
                        module_name=foreach_module_call
                    )
                    self.foreach_bind_log_file_name_to_key = foreach_bind_log_file_name_to_key
                    continue

                # Parse regular parameter
                expanded_param: dict[str, Any] = {}
                chunks = split_param(param)

                found_foreach_iterator = False
                found_foreach_key = False
                found_foreach_value = False
                found_foreach_from_file_path = False
                foreach_only = False
                foreach_forbidden = False

                for chunk in chunks:
                    k, v = get_json_export_for_chunk(chunk)
                    if k == "foreach_iterator":
                        found_foreach_iterator = True
                    elif k == "foreach_from_file_path":
                        found_foreach_from_file_path = True
                    elif k == "foreach_key":
                        found_foreach_key = True
                    elif k == "foreach_value":
                        found_foreach_value = True
                    elif k == "foreach_only":
                        foreach_only = True
                    elif k == "foreach_forbidden":
                        foreach_forbidden = True
                    else:
                        expanded_param[k] = v

                try:
                    module_param = TerraformModuleParameter(**expanded_param)
                except TypeError as exc:
                    raise RuntimeError(f"Failed to generate parameter: {expanded_param}") from exc

                module_params.append(module_param)

                if found_foreach_iterator:
                    self.foreach_iterator = module_param
                if found_foreach_from_file_path:
                    self.foreach_from_file_path = module_param
                if found_foreach_key:
                    self.foreach_keys.append(module_param.name)
                if found_foreach_value:
                    self.foreach_values.append(module_param.name)
                if foreach_only:
                    self.foreach_only.append(module_param.name)
                    continue
                if foreach_forbidden:
                    self.foreach_forbidden.append(module_param.name)
                    continue

                module_params.append(expanded_param)

            except RuntimeError as exc:
                raise RuntimeError(f"Failed to parse docstring param: {param}") from exc

        self.set_module_params(module_params)

    def set_module_params(self, module_params: Any) -> None:
        """Set module parameters from parsed config."""
        if module_params is None:
            return

        for module_param in module_params:
            if not isinstance(module_param, TerraformModuleParameter):
                module_param = TerraformModuleParameter(**module_param)

            self.module_parameters.append(module_param)
            self.module_parameter_names.add(module_param.name)

    def set_required_module_params(self) -> None:
        """Add required standard parameters."""
        required_params = {
            "checksum": TerraformModuleParameter(
                name="checksum",
                default="",
                required=False,
                description="Optional checksum to use for triggering resource updates",
            ),
        }

        for param_name, module_param in required_params.items():
            if param_name not in self.module_parameter_names:
                self.module_parameters.append(module_param)
                self.module_parameter_names.add(param_name)

    def get_variables(
        self,
        filter_foreach_only: bool = True,
        filter_foreach_forbidden: bool = False,
    ) -> dict[str, dict[str, Any]]:
        """Generate Terraform variable blocks."""
        variables: dict[str, dict[str, Any]] = {}

        for param in self.module_parameters:
            if filter_foreach_only and param.name in self.foreach_only:
                continue
            if filter_foreach_forbidden and param.name in self.foreach_forbidden:
                continue

            variables[param.name] = param.get_variable()

        return variables

    def get_triggers(
        self,
        disable_encoding: bool = False,
        filter_foreach_only: bool = True,
        filter_foreach_forbidden: bool = False,
    ) -> dict[str, str]:
        """Generate Terraform trigger expressions."""
        triggers: dict[str, str] = {}

        for param in self.module_parameters:
            if filter_foreach_only and param.name in self.foreach_only:
                continue
            if filter_foreach_forbidden and param.name in self.foreach_forbidden:
                continue

            triggers[param.name] = param.get_trigger(disable_encoding)

        if strtobool(self.generator_parameters.get("always", False)):
            triggers["always"] = "${timestamp()}"

        return triggers

    def get_terraform(
        self,
        provider_type: str | None = None,
        provider_min_version: str | None = None,
        provider_organization: str = "hashicorp",
        terraform_min_version: str = "1.6",
    ) -> dict[str, Any]:
        """Generate terraform block with required providers."""
        terraform: dict[str, Any] = {
            "required_version": f">={terraform_min_version}",
        }

        terraform_providers = deepcopy(self.required_providers)

        if not is_nothing(provider_type):
            terraform_providers[provider_type] = {
                "source": f"{provider_organization}/{provider_type}",
            }
            if not is_nothing(provider_min_version):
                terraform_providers[provider_type]["version"] = f">={provider_min_version}"

        if not is_nothing(terraform_providers):
            terraform["required_providers"] = terraform_providers

        return terraform

    def get_external_data(
        self,
        key: str | None = None,
        output_description: str = "Data query results",
    ) -> dict[str, Any]:
        """Generate external_data Terraform module."""
        if key is None:
            key = self.generator_parameters.get("key")

        if is_nothing(key):
            raise RuntimeError("Cannot generate external data module without a data key")

        query = self.get_triggers()

        # Add environment variable references
        for env_name in self.env_variables:
            query[env_name] = f"${{data.env_var.{env_name}.value}}"
        for env_name in self.sensitive_env_variables:
            query[env_name] = f"${{data.env_sensitive.{env_name}.value}}"

        external_data = {"program": list(self._program_args), "query": query}

        data_blocks = drop_empty_blocks(
            {
                "external": {"default": external_data},
                "env_var": {
                    env_name: {"id": env_name, "required": env_data.get("required", False)}
                    for env_name, env_data in self.env_variables.items()
                },
                "env_sensitive": {
                    env_name: {"id": env_name, "required": env_data.get("required", False)}
                    for env_name, env_data in self.sensitive_env_variables.items()
                },
            }
        )

        # Determine output expression
        if self.generator_parameters.get("plaintext_output", False):
            results_expr = '${data.external.default.result["' + key + '"]}'
        else:
            results_expr = (
                '${jsondecode(base64decode(data.external.default.result["' + key + '"]))}'
            )

        tf_json = drop_empty_blocks(
            {
                "terraform": self.get_terraform("external", "2.3.1"),
                "variable": self.get_variables(),
                "data": data_blocks,
                "locals": {"results": results_expr},
                "output": {
                    key: {
                        "value": "${local.results}",
                        "description": output_description,
                    }
                },
            }
        )

        # Add extra outputs
        for extra_key, _extra_config in self.extra_outputs.items():
            tf_json["locals"][extra_key] = (
                '${jsondecode(base64decode(data.external.default.result["' + extra_key + '"]))}'
            )
            tf_json["output"][extra_key] = {
                "value": "${local." + extra_key + "}",
                "description": output_description,
            }

        # Add sub-key outputs
        for sub_key_key, sub_key_config in self.sub_keys.items():
            sub_key_value = f"local.results.{sub_key_key}"

            if sub_key_config.get("base64_encode", False):
                sub_key_value = "base64decode(" + sub_key_value + ")"
            if sub_key_config.get("json_encode", False):
                sub_key_value = "jsondecode(" + sub_key_value + ")"
            if sub_key_config.get("yaml_encode", False):
                sub_key_value = "yamlencode(" + sub_key_value + ")"

            sub_key_value = "${" + sub_key_value + "}"

            tf_json["output"][sub_key_key] = {
                "value": sub_key_value,
                "description": output_description,
            }

        return tf_json

    def get_null_resource(self, provisioner_type: str | None = None) -> dict[str, Any]:
        """Generate null_resource (terraform_data) Terraform module."""
        provisioner_type = provisioner_type or self.generator_parameters.get("provisioner_type")
        if provisioner_type is None:
            provisioner_type = "local-exec"

        triggers = self.get_triggers()

        environment = {
            name: "${self.triggers_replace." + name + "}" for name in triggers if name != "script"
        }

        # Add environment variable references
        for env_name in self.env_variables:
            environment[env_name] = f"${{data.env_var.{env_name}.value}}"
        for env_name in self.sensitive_env_variables:
            environment[env_name] = f"${{data.env_sensitive.{env_name}.value}}"

        provisioner = {"command": self.call, "environment": environment}
        provisioner_block = [{provisioner_type: provisioner}]

        null_resource = {
            "triggers_replace": triggers,
            "provisioner": provisioner_block,
        }

        data_blocks = drop_empty_blocks(
            {
                "env_var": {
                    env_name: {"id": env_name, "required": env_data.get("required", False)}
                    for env_name, env_data in self.env_variables.items()
                },
                "env_sensitive": {
                    env_name: {"id": env_name, "required": env_data.get("required", False)}
                    for env_name, env_data in self.sensitive_env_variables.items()
                },
            }
        )

        return drop_empty_blocks(
            {
                "terraform": self.get_terraform(),
                "variable": self.get_variables(),
                "resource": {"terraform_data": {"default": null_resource}},
                "data": data_blocks,
            }
        )

    def get_mixed(self, module_type: str | None = None, **kwargs: Any) -> dict[str, Any]:
        """Generate module based on type."""
        if module_type is None:
            module_type = self.module_type

        if module_type is None:
            module_type = self.generator_parameters.get("type", "data_source")

        if module_type == "data_source":
            return self.get_external_data(**kwargs)
        elif module_type == "null_resource":
            return self.get_null_resource(**kwargs)
        else:
            raise RuntimeError(f"Unknown module type: {module_type}")

    def get_module_class(self, module_class: str | None = None) -> str | None:
        """Get the module class for path construction."""
        import re

        if is_nothing(module_class):
            return self.generator_parameters.get("module_class", self.terraform_modules_class)

        if not module_class[:1].isalnum():
            first_alpha = re.search(r"[A-Za-z0-9]", module_class)
            if not first_alpha:
                return None

        return module_class

    def get_module_name(
        self,
        module_class: str | None = None,
        module_name: str | None = None,
    ) -> str:
        """Get the full module name."""
        module_class = self.get_module_class(module_class)

        if is_nothing(module_class) or strtobool(
            self.generator_parameters.get("no_class_in_module_name", False)
        ):
            chunks = []
        else:
            chunks = [module_class]

        if is_nothing(module_name):
            chunks.append(self.module_name)
        else:
            chunks.append(module_name)

        return self.terraform_modules_name_delim.join(chunks).replace(
            "_", self.terraform_modules_name_delim
        )

    def get_module_path(
        self,
        modules_dir: str | None = None,
        module_class: str | None = None,
        module_name: str | None = None,
        modules_file_name: str = "main.tf.json",
    ) -> Path:
        """Get the file path for the module."""
        if is_nothing(modules_dir):
            modules_dir = self.terraform_modules_dir

        modules_dir = Path(modules_dir)

        module_class = self.get_module_class(module_class=module_class)
        module_name = self.get_module_name(module_class=module_class, module_name=module_name)

        if module_class == module_name:
            return modules_dir.joinpath(module_name, modules_file_name)

        return modules_dir.joinpath(module_class, module_name, modules_file_name)

    @classmethod
    def get_all_resources(
        cls,
        terraform_modules: dict[str, str],
        **kwargs: Any,
    ) -> tuple[list[TerraformModuleResources], float]:
        """Generate resources for all modules in parallel.

        Args:
            terraform_modules: Dict mapping method names to docstrings.
            **kwargs: Additional arguments for TerraformModuleResources.

        Returns:
            Tuple of (list of resources, elapsed time).
        """
        resources: list[TerraformModuleResources] = []

        tic = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []

            for module_name, module_docs in terraform_modules.items():
                futures.append(
                    executor.submit(cls, module_name=module_name, docstring=module_docs, **kwargs)
                )

            for future in concurrent.futures.as_completed(futures):
                try:
                    resources.append(future.result())
                except Exception as exc:
                    executor.shutdown(wait=False, cancel_futures=True)
                    raise RuntimeError("Failed to get resources") from exc

        toc = time.perf_counter()
        return resources, toc - tic
