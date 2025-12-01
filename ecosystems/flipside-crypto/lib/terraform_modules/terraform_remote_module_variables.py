import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional

from terraform_modules import utils
from terraform_modules.utils import Utils


def variable_marked_for_removal(variable_data: any):
    return utils.strtobool(variable_data.get("remove", False))


class TerraformRemoteModuleVariables(Utils):
    def __init__(
        self,
        repository_name: str,
        repository_tag: str,
        variable_files: List[str],
        local_module_source: Optional[str] = None,
        defaults: Optional[Dict[str, Dict[str, Any]]] = None,
        overrides: Optional[Dict[str, Dict[str, Any]]] = None,
        parameter_generators: Optional[Dict[str, Any]] = None,
        map_name_to: Optional[Dict[str, Any]] = None,
        map_sanitized_name_to: Optional[Dict[str, Any]] = None,
        requires_github_authentication: Optional[bool] = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.repository_name = repository_name
        self.repository_tag = repository_tag
        self.variable_files = variable_files
        self.local_module_source = local_module_source
        self.defaults = defaults or {}
        self.overrides = overrides or {}
        self.parameter_generators = parameter_generators or {}
        self.map_name_to = map_name_to or {}
        self.map_sanitized_name_to = map_sanitized_name_to or {}
        self.requires_github_authentication = requires_github_authentication

        self.defaults_config = {}
        self.variables_config = {}
        self.descriptions_config = {}

        self.log_results(self.defaults, "Defaults")
        self.log_results(self.overrides, "Overrides")
        self.log_results(self.parameter_generators, "Parameter Generators")
        self.log_results(self.map_name_to, "Map Name To")
        self.log_results(self.map_sanitized_name_to, "Map Sanitized Name To")

    def get_config_from_variables(self, variable_data: Any, source_path: str) -> Dict[str, Dict[str, Any]]:
        variables = {}

        if isinstance(variable_data, list):
            for nested_variable_data in variable_data:
                variables = self.merger.merge(
                    variables,
                    self.get_config_from_variables(nested_variable_data, source_path),
                )

            return variables

        for key, params in variable_data.items():
            self.logged_statement(f"Raw parameters for key {key}", json_data=params, active_marker=key)

            variable_type = self.decode_type_param(params["type"], key)
            self.logged_statement(f"For key {key}, decoded variable type", json_data=variable_type)

            default = self.compact_default_for_variable_type(
                variable_type=variable_type, default=params.get("default"), key=key
            )

            description = params.get("description", "")
            if isinstance(description, list):
                if len(description) == 0:
                    self.logged_statement(f"For key {key}, description is an empty list, nullifying the description")
                    description = ""
                else:
                    self.logged_statement(
                        f"For key {key}, description: '{description}' is inside a list, getting it out"
                    )
                    description = description[0]

            defaults = self.defaults.get(key, {})
            overrides = self.overrides.get(key, {})

            variable_required = utils.strtobool(overrides.get("required", defaults.get("required", False)))
            if variable_required and variable_type.startswith("optional("):
                self.logged_statement(
                    f"Ensuring that required variable {key} type '{variable_type}' is not set as optional"
                )
                variable_type = variable_type.removeprefix("optional(").removesuffix(")")
            elif not variable_required and not variable_type.startswith("optional("):
                self.logged_statement(
                    f"Ensuring that required variable {key} type '{variable_type}' is set as optional"
                )
                variable_type = f"optional({variable_type})"

            self.logged_statement(f"For {key}, type is '{variable_type}'")

            parameters = {
                "type": variable_type,
                "source": Path(source_path).name,
                "default_value": overrides.get("default_value", defaults.get("default_value", default)),
                "default_generator": overrides.get("default_generator", defaults.get("default_generator")),
                "override_value": overrides.get("override_value", defaults.get("override_value")),
                "required": overrides.get("required", defaults.get("required", False)),
                "description": description,
                "internal": False,
                "parameter_generator": self.parameter_generators.get(
                    key,
                    overrides.get("parameter_generator", defaults.get("parameter_generator")),
                ),
            }

            self.logged_statement(f"Parameters for {key}", json_data=parameters)

            variables[key] = parameters

        return variables

    def get_variables(self) -> Dict[str, Dict[str, Any]]:
        self.logger.info(f"Processing variable files: {self.variable_files}")

        headers = {}
        if self.requires_github_authentication:
            headers["Authorization"] = f"token {self.GITHUB_TOKEN}"

        if utils.is_nothing(self.local_module_source):
            self.logged_statement(f"Getting variables from Git repository {self.repository_name}/{self.repository_tag}")
            module_source = f"https://raw.githubusercontent.com/{self.repository_name}/{self.repository_tag}"
        else:
            self.logged_statement(f"Getting variables from local module source: {self.local_module_source}")
            module_source = self.local_module_source

        self.logger.info(f"Getting variables from {module_source}")

        variables = {}

        for file_name in self.variable_files:
            variable_file = self.get_file(
                file_path=f"{module_source}/{file_name}",
                charset="ascii",
                errors="ignore",
                headers=headers,
            )
            self.log_results(variable_file, f"variable file {file_name}")

            if utils.is_nothing(variable_file) or "variable" not in variable_file:
                raise RuntimeError(f"Variable file {file_name} empty or missing variable data:\n{variable_file}")

            variables = self.merger.merge(
                variables,
                self.get_config_from_variables(variable_file["variable"], module_source),
            )
            self.log_results(variables, f"variables {file_name}")

        return variables

    def convert(self):
        variables = self.get_variables()

        for variable_name, variable_data in self.defaults.items():
            if variable_marked_for_removal(variable_data):
                self.logger.info(
                    f"Variable '{variable_name}' from defaults is flagged for removal, removing it from variables if it exists and skipping it"
                )
                if variable_name in variables:
                    del variables[variable_name]

                continue

            if variable_name not in variables:
                self.logger.info(f"{variable_name} from defaults not in variables, injecting it")
                variables[variable_name] = variable_data
            else:
                for k, v in variable_data.items():
                    if k not in variables[variable_name]:
                        self.logger.info(f"{variable_name} missing parameter '{k}', using '{v}' from defaults")
                        variables[variable_name][k] = v

        self.log_results(variables, "Results after merging in missing defaults")

        for variable_name, variable_data in self.overrides.items():
            if utils.strtobool(variable_data.get("remove", False)) and variable_name in variables:
                self.logger.info(
                    f"Variable '{variable_name}' from overrides is flagged for removal, removing it from variables"
                )
                del variables[variable_name]
                continue

            if variable_name not in variables:
                self.logger.info(f"{variable_name} from overrides not in results, injecting it")
                variables[variable_name] = variable_data
            else:
                for k, v in variable_data.items():
                    self.logger.info(f"Overriding '{k}' for {variable_name} with '{v}' from overrides")
                    variables[variable_name][k] = v

        self.log_results(variables, "Results after merging in missing overrides")

        base_variable_data = {
            "source": None,
            "override_value": None,
            "default_generator": None,
            "parameter_generator": None,
            "internal": False,
            "required": False,
        }

        for variable_name, variable_data in deepcopy(variables).items():
            self.logged_statement(
                f"Raw variable data after defaults and overrides",
                json_data=variable_data,
                active_marker=variable_name,
            )

            if variable_marked_for_removal(variable_data):
                self.logger.info(f"Variable '{variable_name}' is flagged for removal, removing it from variables")
                del variables[variable_name]
                continue

            default_generator = self.map_sanitized_name_to.get(
                variable_name,
                self.map_name_to.get(variable_name, variable_data.get("default_generator")),
            )

            variables[variable_name]["default_generator"] = default_generator

            variable_type = variable_data.get("type")
            if utils.is_nothing(variable_type):
                raise RuntimeError(f"Variable {variable_name} has no type set")

            self.logged_statement(f"Type for {variable_name} is {variable_type}")

            if utils.is_nothing(default_generator):
                variable_default_value = variable_data.get("default_value")

                if utils.is_nothing(variable_default_value):
                    self.logged_statement(f"Calculating default value for variable {variable_name}")
                    if variable_type.startswith("optional(list") or variable_type.startswith("list"):
                        self.logged_statement(f"Defaulting {variable_name} to an empty list")
                        variable_default_value = []
                    elif "any" in variable_type:
                        self.logged_statement(f"Defaulting {variable_name} to an empty map")
                        variable_default_value = {}

                    self.logged_statement(
                        f"No default generator for {variable_name}, default value is: '{variable_default_value}'"
                    )
                else:
                    self.logged_statement(
                        f"No default generator for {variable_name}, default value is: '{variable_default_value}'"
                    )

                    variable_default_value = self.compact_default_for_variable_type(
                        variable_type=variable_type,
                        default=variable_default_value,
                        key=variable_name,
                    )

                    self.logged_statement(f"Compacted default value for {variable_name} to: '{variable_default_value}'")

                variables[variable_name]["default_value"] = variable_default_value
            else:
                self.logged_statement(
                    f"Default generator for {variable_name}",
                    json_data=default_generator,
                )
                variables[variable_name]["default_value"] = default_generator

            if isinstance(variables[variable_name]["default_value"], list):
                self.logged_statement(f"Finding all non-empty defaults for the {variable_name} list default")
                variables[variable_name]["default_value"] = utils.all_non_empty(
                    *variables[variable_name]["default_value"]
                )

            for k, v in base_variable_data.items():
                if k not in variable_data:
                    self.logged_statement(f"Variable '{variable_name}' missing '{k}', setting it to '{v}'")
                    variables[variable_name][k] = v

            self.logged_statement(f"Variable data for {variable_name}", json_data=variables[variable_name])

        self.log_results(variables, "Results after applying base variable data")

        return variables

    def decode_type_param(self, variable_type: Optional[str | List[str]], key: str):
        if utils.is_nothing(variable_type):
            raise RuntimeError(f"No type set for key {key}")

        if isinstance(variable_type, list):
            self.logged_statement(f"For key {key}, variable type {variable_type} is in a list, extracting it")
            variable_type = variable_type[0]

        parts = re.findall(r"(?<={).+?(?=})", variable_type)

        self.logged_statement(f"Parts for key {key}", json_data=parts)

        if len(parts) == 0:
            raise RuntimeError(f"No type found parsing {variable_type} for key {key}")

        first_part = parts[0].replace("set", "list")

        if "object" in first_part:
            self.logged_statement(
                f"Refusing to transform complex object type '{variable_type}' for key {key}, returning 'any' instead"
            )
            return "any"

        if "(" not in first_part:
            self.logged_statement(f"First part '{first_part}' of key {key} stands alone, returning it")
            return first_part

        if ")" not in first_part:
            self.logged_statement(f"First part '{first_part} of key{key} has an opened parenthesis, closing it")
            raise RuntimeError(f"{first_part})")

        self.logged_statement(
            f"Returning the first part of the variable type '{variable_type}' for key {key}, {first_part}"
        )
        return first_part

    def compact_default_for_variable_type(self, variable_type: str, default: any, key: str):
        if (variable_type.startswith("list(") or variable_type.startswith("optional(list(")) and not isinstance(
            default, list
        ):
            self.logged_statement(
                f"For key {key}, type: {variable_type} is a list and default: '{default}' isn't, putting it inside of one"
            )
            return [default]

        if not (variable_type.startswith("list(") or variable_type.startswith("optional(list(")) and isinstance(
            default, list
        ):
            if len(default) == 0:
                self.logged_statement(
                    f"For key {key}, type: {variable_type} is not a list and default: '{default}' is an empty list, nullifying the default"
                )
                return None

            return default[0]

        return default
