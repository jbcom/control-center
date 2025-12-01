import concurrent.futures
import json
import re
import time
from copy import deepcopy
from pathlib import Path
from shlex import split as shlex_split
from typing import Any, Dict, Optional

from terraform_modules import settings, utils
from terraform_modules.terraform_module_environment_variable import TerraformModuleEnvironmentVariable
from terraform_modules.terraform_module_parameter import TerraformModuleParameter
from tssplit import tssplit


def get_json_export_for_chunk(chunk):
    try:
        k, v = chunk.strip().strip('"').split(":")
    except ValueError as exc:
        raise RuntimeError(f"Failed to get chunks for: {chunk}") from exc

    k = k.strip().strip('"')
    v = v.strip().strip('"')

    try:
        return k, json.loads(v)
    except json.JSONDecodeError:
        return k, v


def drop_empty_blocks(data_blocks: dict[str, Any]):
    return {k: v for k, v in data_blocks.items() if not utils.is_nothing(v)}


class TerraformModuleResources:
    def __init__(
        self,
        module_name: str,
        docstring: str,
        module_type: Optional[str] = None,
        module_params: Any = None,
        terraform_modules_dir: Optional[str] = settings.TERRAFORM_MODULES_DIR,
        terraform_modules_class: Optional[str] = None,
        terraform_modules_name_delim: Optional[str] = settings.TERRAFORM_MODULES_NAME_DELIM,
    ):
        self.terraform_modules_dir = terraform_modules_dir
        self.terraform_modules_name_delim = terraform_modules_name_delim

        if terraform_modules_class is None:
            terraform_modules_class = ""

        self.terraform_modules_class = terraform_modules_class.removesuffix(self.terraform_modules_name_delim)

        self.module_name = module_name
        self.module_type = module_type
        self.docstring = docstring
        self.descriptor = None
        self.module_parameters = []
        self.generator_parameters = {}
        self.extra_outputs = {}
        self.sub_keys = {}

        # For lines in the docstring formatted as env=name: GITHUB_TOKEN, required: true, sensitive: true
        self.from_env = {}

        self.required_providers = {
            "env": {
                "source": "tcarreira/env",
                "version": ">=0.2.0",
            }
        }
        self.copy_variables_to = []
        self.module_parameter_names = set()
        self.foreach_modules = {}
        self.foreach_iterator = None
        self.foreach_from_file_path = None
        self.foreach_keys = []
        self.foreach_values = []
        self.foreach_only = []
        self.foreach_forbidden = []
        self.generation_forbidden = False
        self.env_variables = {}  # Store env variables
        self.sensitive_env_variables = {}  # Store sensitive env variables

        self.call = f"{settings.TERRAFORM_MODULES_BINARY_NAME} {self.module_name}"
        self.foreach_bind_log_file_name_to_key = False

        self.get_module_config()
        self.set_module_params(module_params)
        self.set_required_module_params()

    def get_module_config(self):
        if self.docstring is None:
            return

        docstring = [line for line in self.docstring.splitlines() if line != ""]

        if len(docstring) == 0:
            return

        self.descriptor = docstring.pop(0)

        if len(docstring) == 0:
            return

        module_params = []

        def split_param(p: str):
            return tssplit(
                p,
                quote='"',
                quote_keep=True,
                delimiter=",",
            )

        for param in docstring:
            try:
                param = param.strip()
                if utils.is_nothing(param):
                    continue

                if param.startswith("#"):
                    comment = param.lstrip("#").strip().lower()

                    match comment:
                        case "noterraform":
                            self.generation_forbidden = True

                    continue

                if param.startswith("generator="):
                    chunks = split_param(param.removeprefix("generator="))
                    for chunk in chunks:
                        k, v = get_json_export_for_chunk(chunk)

                        if k == "plaintext_output":
                            self.generator_parameters[k] = utils.strtobool(v)
                        else:
                            self.generator_parameters[k] = v

                    continue

                if param.startswith("env="):
                    chunks = split_param(param.removeprefix("env="))
                    processed_chunks = {}
                    env_name = None
                    for chunk in chunks:
                        k, v = get_json_export_for_chunk(chunk)
                        if k == "name":
                            env_name = v
                        else:
                            processed_chunks[k] = utils.strtobool(v) if k == "required" else v

                    if not env_name:
                        raise ValueError(f"Environment variable {param} is missing its name")
                    if processed_chunks.get("sensitive", False):
                        self.sensitive_env_variables[env_name] = processed_chunks
                    else:
                        self.env_variables[env_name] = processed_chunks
                    continue

                if param.startswith("extra_output="):
                    chunks = split_param(param.removeprefix("extra_output="))
                    extra_output = {}
                    for chunk in chunks:
                        k, v = get_json_export_for_chunk(chunk)
                        extra_output[k] = v

                    extra_output_key = extra_output.pop("key", None)

                    if utils.is_nothing(extra_output_key):
                        raise RuntimeError(f"Extra output from Terraform module is missing key: {param}")

                    self.extra_outputs[extra_output_key] = extra_output

                    continue

                if param.startswith("env="):
                    # Process each env= statement into a TerraformModuleEnvironmentVariable format
                    chunks = split_param(param.removeprefix("env="))
                    for chunk in chunks:
                        k, v = get_json_export_for_chunk(chunk)

                        if k != "name":
                            self.from_env[k] = utils.strtobool(v)
                        else:
                            self.from_env[k] = v

                    continue

                if param.startswith("sub_key="):
                    chunks = split_param(param.removeprefix("sub_key="))
                    sub_key = {}
                    for chunk in chunks:
                        k, v = get_json_export_for_chunk(chunk)
                        sub_key[k] = v

                    sub_key_key = sub_key.pop("key", None)

                    if utils.is_nothing(sub_key_key):
                        raise RuntimeError(f"Sub key from Terraform module is missing key: {param}")

                    self.sub_keys[sub_key_key] = sub_key

                    continue

                if param.startswith("required_provider="):
                    chunks = split_param(param.removeprefix("required_provider="))
                    required_provider = {}
                    for chunk in chunks:
                        k, v = get_json_export_for_chunk(chunk)
                        required_provider[k] = v

                    provider_name = required_provider.pop("name", None)

                    if utils.is_nothing(provider_name):
                        raise RuntimeError(f"Required provider from Terraform module is missing provider name: {param}")

                    self.required_providers[provider_name] = required_provider

                    continue

                if param.startswith("copy_variables_to="):
                    chunks = split_param(param.removeprefix("copy_variables_to="))
                    copy_variables_to = {}
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

                        match k:
                            case "module_name":
                                foreach_module_name = v
                            case "module_call":
                                foreach_module_call = v
                            case "bind_log_file_name_to_key":
                                foreach_bind_log_file_name_to_key = utils.strtobool(v)

                    foreach_module_path = self.get_module_path(module_name=foreach_module_name)

                    self.foreach_modules[foreach_module_path] = self.get_module_name(module_name=foreach_module_call)

                    self.foreach_bind_log_file_name_to_key = foreach_bind_log_file_name_to_key

                    continue

                expanded_param = {}

                chunks = split_param(param)

                found_foreach_iterator = False
                found_foreach_key = False
                found_foreach_value = False
                found_foreach_from_file_path = False

                foreach_only = False
                foreach_forbidden = False

                for chunk in chunks:
                    k, v = get_json_export_for_chunk(chunk)

                    match k:
                        case "foreach_iterator":
                            found_foreach_iterator = True
                        case "foreach_from_file_path":
                            found_foreach_from_file_path = True
                        case "foreach_key":
                            found_foreach_key = True
                        case "foreach_value":
                            found_foreach_value = True
                        case "foreach_only":
                            foreach_only = True
                        case "foreach_forbidden":
                            foreach_forbidden = True
                        case _:
                            expanded_param[k] = v

                try:
                    module_param = TerraformModuleParameter(**expanded_param)
                except TypeError as exc:
                    raise RuntimeError(
                        f"Failed to generate module parameter for expanded parameter: {expanded_param}"
                    ) from exc

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

    def set_module_params(self, module_params):
        if module_params is None:
            return None

        for module_param in module_params:
            if not isinstance(module_param, TerraformModuleParameter):
                module_param = TerraformModuleParameter(**module_param)

            self.module_parameters.append(module_param)
            self.module_parameter_names.add(module_param.name)

    def set_required_module_params(self):
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

    def get_variables(self, filter_foreach_only: bool = True, filter_foreach_forbidden: bool = False):
        variables = {}
        data_blocks = {}

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
    ):
        triggers = {}

        for param in self.module_parameters:
            if filter_foreach_only and param.name in self.foreach_only:
                continue

            if filter_foreach_forbidden and param.name in self.foreach_forbidden:
                continue

            triggers[param.name] = param.get_trigger(disable_encoding)

        if utils.strtobool(self.generator_parameters.get("always", False)):
            triggers["always"] = "${timestamp()}"

        return triggers

    def get_terraform(
        self,
        provider_type: Optional[str] = None,
        provider_min_version: Optional[str] = None,
        provider_organization: str = "hashicorp",
        terraform_min_version: str = "1.6",
    ):
        terraform = {
            "required_version": f">={terraform_min_version}",
        }

        terraform_providers = deepcopy(self.required_providers)

        if not utils.is_nothing(provider_type):
            terraform_providers[provider_type] = {
                "source": f"{provider_organization}/{provider_type}",
            }

            if not utils.is_nothing(provider_min_version):
                terraform_providers[provider_type]["version"] = f">={provider_min_version}"

        if not utils.is_nothing(terraform_providers):
            terraform["required_providers"] = terraform_providers

        return terraform

    def get_null_resource(self, provisioner_type=None):
        provisioner_type = provisioner_type or self.generator_parameters.get(provisioner_type)

        if provisioner_type is None:
            provisioner_type = "local-exec"

        triggers = self.get_triggers()

        environment = {name: "${self.triggers_replace." + name + "}" for name in triggers.keys() if name != "script"}

        # Include references to env_variables and sensitive_env_variables
        for env_name, env_data in self.env_variables.items():
            environment[env_name] = f"${{data.env_var.{env_name}.value}}"

        for env_name, env_data in self.sensitive_env_variables.items():
            environment[env_name] = f"${{data.env_sensitive.{env_name}.value}}"

        provisioner = {"command": self.call, "environment": environment}

        provisioner = [{provisioner_type: provisioner}]

        null_resource = {
            "triggers_replace": triggers,
            "provisioner": provisioner,
        }

        # Create the data blocks for env_variables and sensitive_env_variables
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

    def get_external_data(
        self,
        key: Optional[str] = None,
        output_description="Data query results",
    ):
        if key is None:
            key = self.generator_parameters.get("key")

        if utils.is_nothing(key):
            raise RuntimeError(f"Cannot generate an external data Terraform module without a data key")

        query = self.get_triggers()
        for env_name, env_data in self.env_variables.items():
            query[env_name] = f"${{data.env_var.{env_name}.value}}"
        for env_name, env_data in self.sensitive_env_variables.items():
            query[env_name] = f"${{data.env_sensitive.{env_name}.value}}"

        external_data = {"program": shlex_split(self.call), "query": query}

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

        tf_json = drop_empty_blocks(
            {
                "terraform": self.get_terraform("external", "2.3.1"),
                "variable": self.get_variables(),
                "data": data_blocks,
                "locals": {
                    "results": (
                        '${data.external.default.result["' + key + '"]}'
                        if self.generator_parameters.get("plaintext_output", False)
                        else '${jsondecode(base64decode(data.external.default.result["' + key + '"]))}'
                    )
                },
                "output": {
                    key: {
                        "value": "${local.results}",
                        "description": output_description,
                    }
                },
            }
        )

        for extra_output_key, extra_output_config in self.extra_outputs.items():
            tf_json["locals"][extra_output_key] = (
                '${jsondecode(base64decode(data.external.default.result["' + extra_output_key + '"]))}'
            )
            tf_json["output"][extra_output_key] = {
                "value": "${local." + extra_output_key + "}",
                "description": output_description,
            }

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

    def get_foreach(self, key=None, foreach_key=None, output_description="Data query results"):
        foreach_iterator: TerraformModuleParameter = self.foreach_iterator
        foreach_from_file_path: TerraformModuleParameter = self.foreach_from_file_path
        module_iterators = []

        if foreach_iterator is None and foreach_from_file_path is None:
            return None

        variables = {}

        if foreach_iterator is not None:
            iterator_name = foreach_iterator.name
            variables[iterator_name] = foreach_iterator.get_variable()
            module_iterators.append("try(nonsensitive(var." + iterator_name + "), var." + iterator_name + ")")

        if foreach_from_file_path is not None:
            iterator_from_file_path_name = f"{foreach_from_file_path.name}_file"
            variables[iterator_from_file_path_name] = foreach_from_file_path.get_variable()
            module_iterators.append("try(jsondecode(file(var." + iterator_from_file_path_name + ")), {})")

        if len(module_iterators) == 1:
            module_iterator = module_iterators[0]
        else:
            module_iterator = ",".join(module_iterators)
            module_iterator = "merge(" + module_iterator + ")"

        module_iterator = "${" + module_iterator + "}"

        for name, variable in self.get_variables(filter_foreach_only=False, filter_foreach_forbidden=True).items():
            if name in variables or name in self.foreach_keys or name in self.foreach_values:
                continue

            if name == "log_file_name" and self.foreach_bind_log_file_name_to_key:
                continue

            variables[name] = variable

        triggers = {
            name: trigger
            for name, trigger in self.get_triggers(disable_encoding=True, filter_foreach_forbidden=True).items()
            if name != "always"
        }

        if self.foreach_bind_log_file_name_to_key:
            triggers["log_file_name"] = '${replace(each.key, " ", "_")}.log'

        for name in self.foreach_keys:
            triggers[name] = "${each.key}"

        for name in self.foreach_values:
            triggers[name] = "${each.value}"

        if key is None:
            key = self.generator_parameters.get("key")

        if foreach_key is None:
            foreach_key = self.generator_parameters.get("foreach_key", key)

        for module_path, module_call in self.foreach_modules.items():
            module = {
                "for_each": module_iterator,
                "source": f"../{module_call}",
            } | triggers

            js = {
                "variable": variables,
                "module": {
                    "default": module,
                },
            }

            if key is not None:
                foreach_value = "${{for id, data in module.default : id => data." + key + "}}"

                js["output"] = {
                    foreach_key: {
                        "value": foreach_value,
                        "description": output_description,
                    }
                }

            yield module_path, js

    def get_entity_constructor(self, blueprint_id: str = None):
        if blueprint_id is None:
            blueprint_id = self.module_name

        if blueprint_id is None:
            raise RuntimeError(f"Cannot generate an entity constructor module without a blueprint ID")

    def get_mixed(self, module_type=None, **kwargs):
        if module_type is None:
            module_type = self.module_type

        if module_type is None:
            module_type = self.generator_parameters.get("type")

        match module_type:
            case "data_source":
                return self.get_external_data(**kwargs)
            case "null_resource":
                return self.get_null_resource(**kwargs)
            case _:
                raise RuntimeError(f"Cannot process a mixed Terraform module for type: {module_type}")

    def get_modules_to_copy_variables_to(self):
        for copy_variables_to in self.copy_variables_to:
            if "module_name" not in copy_variables_to:
                raise RuntimeError(f"Cannot process a copy of variables without a module name: {copy_variables_to}")

            if "modules_file_name" not in copy_variables_to:
                copy_variables_to["modules_file_name"] = "variables.tf.json"

            module_path = self.get_module_path(**copy_variables_to)

            js = {
                "variable": self.get_variables(filter_foreach_only=True),
            }

            yield module_path, js

    def get_module_class(self, module_class: Optional[str] = None):
        if utils.is_nothing(module_class):
            return self.generator_parameters.get("module_class", self.terraform_modules_class)

        if not module_class[:1].isalnum():
            first_alpha = re.search(r"[A-Za-z0-9]", module_class)
            if not first_alpha:
                return None

        return module_class

    def get_module_name(self, module_class: Optional[str] = None, module_name: Optional[str] = None):
        module_class = self.get_module_class(module_class)
        if utils.is_nothing(module_class) or utils.strtobool(
            self.generator_parameters.get("no_class_in_module_name", False)
        ):
            chunks = []
        else:
            chunks = [module_class]

        if utils.is_nothing(module_name):
            chunks.append(self.module_name)
        else:
            chunks.append(module_name)

        return self.terraform_modules_name_delim.join(chunks).replace("_", self.terraform_modules_name_delim)

    def get_module_path(
        self,
        modules_dir: Optional[str] = None,
        module_class: Optional[str] = None,
        module_name: Optional[str] = None,
        modules_file_name: str = "main.tf.json",
    ):
        if utils.is_nothing(modules_dir):
            modules_dir = self.terraform_modules_dir

        modules_dir = Path(modules_dir)

        module_class = self.get_module_class(module_class=module_class)
        module_name = self.get_module_name(module_class=module_class, module_name=module_name)

        if module_class == module_name:
            return modules_dir.joinpath(module_name, modules_file_name)

        return modules_dir.joinpath(module_class, module_name, modules_file_name)

    @classmethod
    def get_all_resources(cls, terraform_modules: Dict[str, str], **kwargs):
        resources = []

        tic = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []

            for module_name, module_docs in terraform_modules.items():
                futures.append(executor.submit(cls, module_name=module_name, docstring=module_docs, **kwargs))

            for future in concurrent.futures.as_completed(futures):
                try:
                    resources.append(future.result())
                except Exception as exc:
                    executor.shutdown(wait=False, cancel_futures=True)
                    raise RuntimeError(f"Failed to get resources") from exc

        toc = time.perf_counter()
        return resources, toc - tic
