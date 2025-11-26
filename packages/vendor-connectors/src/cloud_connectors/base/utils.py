import base64
import binascii
import datetime
import inspect
import json
import logging
import logging.config
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import uuid
from collections import defaultdict
from collections.abc import MutableMapping
from copy import copy, deepcopy
from inspect import getmembers, getsource, isfunction
from pathlib import Path
from shlex import split as shlex_split
from typing import Any, Dict, List, Literal, Mapping, Optional, Union, Tuple, Type

import hcl2
import inflection
import lark.exceptions
import numpy as np
import orjson
import requests
import validators
from case_insensitive_dict import CaseInsensitiveDict
from deepmerge import Merger
from filelock import FileLock, Timeout
from git import Repo, InvalidGitRepositoryError, NoSuchPathError, GitCommandError
from more_itertools import split_before
from ruamel.yaml import YAML, StringIO, YAMLError, scalarstring
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.constructor import SafeConstructor
from sortedcontainers import SortedDict

try:
    from dopplersdk import DopplerSDK
except ImportError:
    DopplerSDK = None

from cloud_connectors.base.settings import (
    DEFAULT_LOG_LEVEL,
    DOPPLER_CONFIG,
    DOPPLER_PROJECT,
    LOG_FILE_NAME,
    MAX_DESCRIPTION_LENGTH,
    MAX_FILE_LOCK_WAIT,
    VERBOSITY,
    VERBOSE,
)
from cloud_connectors.base.errors import FormattingError
from cloud_connectors.base.logging import Logging

FilePath = Union[str, bytes, os.PathLike]


def get_caller():
    return sys._getframe().f_back.f_code.co_name


def is_url(url: FilePath) -> bool:
    if validators.url(str(url).strip()) is True:
        return True

    return False


def titleize_name(name: str):
    proper_name = []

    for n in ["".join(i) for i in split_before(name, pred=lambda s: s.isupper())]:
        proper_name.append(n.title())

    return "".join(proper_name)


def zipmap(a: List[str], b: List[str]):
    zipped = {}

    for idx, val in enumerate(a):
        if idx >= len(b):
            break

        zipped[val] = b[idx]

    return zipped


def filter_methods(methods):
    filtered = []

    for method in methods:
        if method.startswith("_"):
            continue

        filtered.append(method)

    return filtered


# Static dictionary mapping client getters to their inputs
CLIENT_INPUTS = {
    "get_aws_resource": {
        "EXECUTION_ROLE_ARN": {"required": "false", "sensitive": "false"},
        "ROLE_SESSION_NAME": {"required": "false", "sensitive": "false"}
    },
    "get_aws_client": {
        "EXECUTION_ROLE_ARN": {"required": "false", "sensitive": "false"},
        "ROLE_SESSION_NAME": {"required": "false", "sensitive": "false"}
    },
    "get_aws_session": {
        "EXECUTION_ROLE_ARN": {"required": "false", "sensitive": "false"},
        "ROLE_SESSION_NAME": {"required": "false", "sensitive": "false"}
    },
    "get_github_client": {
        "GITHUB_ACTIONS": {"required": "false", "sensitive": "false"},
        "ACTIONS_ID_TOKEN_REQUEST_URL": {"required": "false", "sensitive": "false"},
        "ACTIONS_ID_TOKEN_REQUEST_TOKEN": {"required": "false", "sensitive": "true"},
        "GITHUB_OWNER": {"required": "false", "sensitive": "false"},
        "GITHUB_REPO": {"required": "false", "sensitive": "false"},
        "GITHUB_BRANCH": {"required": "false", "sensitive": "false"},
        "GITHUB_TOKEN": {"required": "true", "sensitive": "true"}
    },
    "get_git_repository": {
        "GITHUB_OWNER": {"required": "false", "sensitive": "false"},
        "GITHUB_REPO": {"required": "false", "sensitive": "false"},
        "GITHUB_BRANCH": {"required": "false", "sensitive": "false"},
        "GITHUB_TOKEN": {"required": "true", "sensitive": "true"}
    },
    "get_google_client": {
        "GOOGLE_SERVICE_ACCOUNT": {"required": "true", "sensitive": "true"}
    },
    "get_slack_client": {
        "SLACK_TOKEN": {"required": "true", "sensitive": "true"},
        "SLACK_BOT_TOKEN": {"required": "true", "sensitive": "true"}
    },
    "get_vault_client": {
        "GITHUB_ACTIONS": {"required": "false", "sensitive": "false"},
        "ACTIONS_ID_TOKEN_REQUEST_URL": {"required": "false", "sensitive": "false"},
        "ACTIONS_ID_TOKEN_REQUEST_TOKEN": {"required": "false", "sensitive": "true"},
        "VAULT_ADDR": {"required": "false", "sensitive": "false"},
        "VAULT_NAMESPACE": {"required": "false", "sensitive": "false"},
        "VAULT_TOKEN": {"required": "false", "sensitive": "true"},
    },
    "get_zoom_client": {
        "ZOOM_CLIENT_ID": {"required": "true", "sensitive": "true"},
        "ZOOM_CLIENT_SECRET": {"required": "true", "sensitive": "true"},
        "ZOOM_ACCOUNT_ID": {"required": "true", "sensitive": "true"}
    }
}


def get_inputs_from_docstring(docstring: str) -> Dict[str, Dict[str, str]]:
    """
    Extracts existing inputs from a method's docstring (case-insensitive).
    """
    input_pattern = r"name: (\w+), required: (true|false), sensitive: (true|false)"
    matches = re.findall(input_pattern, docstring or "")
    return {name.lower(): {"required": required, "sensitive": sensitive} for name, required, sensitive in matches}


def update_docstring(docstring: str, inputs: Dict[str, Dict[str, str]]) -> str:
    """
    Updates a docstring with new inputs, ensuring idempotency.
    New inputs are added only if they are not already present (case-insensitive).
    """
    existing_inputs = get_inputs_from_docstring(docstring)
    updated_docstring = docstring or ""
    for name, props in inputs.items():
        if name.lower() not in existing_inputs:  # Compare using lowercase
            updated_docstring += f"\nenv=name: {name}, required: {props['required']}, sensitive: {props['sensitive']}"
    return updated_docstring


def get_available_methods(cls):
    """
    Processes the methods of a class and adds client inputs to their docstrings
    if the clients are called in the method body.
    """
    module_name = cls.__module__
    methods = getmembers(cls, isfunction)
    unique_methods = {}

    for method_name, method_signature in methods:
        # Skip methods that are dunder, not from the same module, or marked with NOPARSE
        if (
                "__" in method_name
                or method_signature.__module__ != module_name
                or (method_signature.__doc__ and "NOPARSE" in method_signature.__doc__)
        ):
            continue

        # Retrieve the source code of the method
        try:
            source_code = getsource(method_signature)
        except (OSError, TypeError):
            # Skip methods whose source code can't be retrieved
            continue

        # Check which client getters are called in the method
        inputs_to_add = {}
        for client_getter, client_inputs in CLIENT_INPUTS.items():
            if client_getter in source_code:
                inputs_to_add.update(client_inputs)

        # Update the docstring with new inputs
        original_docstring = method_signature.__doc__ or ""
        updated_docstring = update_docstring(original_docstring, inputs_to_add)

        # Add the method to unique_methods
        unique_methods[method_name] = updated_docstring

    return unique_methods


def get_process_output(cmd):
    try:
        results = subprocess.run(shlex_split(cmd), capture_output=True, text=True)
    except FileNotFoundError:
        return None, None
    return results.stdout, results.stderr


def get_parent_repository(file_path: FilePath | None = None, search_parent_directories: bool = True) -> Repo | None:
    """
    Retrieves the Git repository object for a given path.

    Args:
        file_path (FilePath | None): The path to a file or directory within the repository.
            If None, defaults to the current working directory.
        search_parent_directories (bool): Whether to search parent directories for the Git repository.
            Defaults to True.

    Returns:
        Repo | None: The Git repository object if found, otherwise None if the path is not a Git repository.
    """
    directory = file_path if file_path else Path.cwd()

    try:
        return Repo(directory, search_parent_directories=search_parent_directories)
    except (InvalidGitRepositoryError, NoSuchPathError):
        return None


def get_repository_name(repo: Repo) -> str | None:
    """
    Retrieves the name of the Git repository.

    Args:
        repo (Repo): The Git repository object.

    Returns:
        str | None: The name of the repository if found, otherwise None.
    """
    try:
        # Get the remote URL (assuming the first remote, typically 'origin')
        remote_url = next(repo.remotes[0].urls)
        # Extract the repository name from the URL
        repo_name = Path(remote_url).stem
        return repo_name
    except (IndexError, ValueError):
        # Handle cases where the remote URL is not available
        return None


def clone_repository_to_temp(repo_owner: str, repo_name: str, github_token: str, branch: str | None = None) -> Tuple[Path, Repo]:
    """
    Clones a Git repository to a temporary directory for file operations.

    Args:
        repo_owner (str): The owner of the GitHub repository.
        repo_name (str): The name of the GitHub repository to clone.
        github_token (str): The GitHub token to access the repository.
        branch (str | None): The branch to clone. If None, the default branch is cloned.

    Returns:
        Path | None: The path to the cloned repository's top-level directory, or None if cloning fails.

    Raises:
        EnvironmentError: If errors occur while trying to clone a Git repository.
    """
    # Construct the repository URL with authentication
    repo_url = f"https://{github_token}:x-oauth-basic@github.com/{repo_owner}/{repo_name}.git"

    try:
        # Create a temporary directory
        temp_dir = Path(tempfile.mkdtemp())

        # Clone the repository to the temporary directory
        repo = Repo.clone_from(repo_url, temp_dir, branch=branch if branch else None)

        # Return the path to the top-level directory of the cloned repository
        return temp_dir, repo

    except GitCommandError as e:
        raise EnvironmentError("Git command error occurred") from e
    except InvalidGitRepositoryError as e:
        raise EnvironmentError("The repository is invalid or corrupt.") from e
    except NoSuchPathError as e:
        raise EnvironmentError("The specified path does not exist.") from e
    except PermissionError as e:
        raise EnvironmentError("Permission denied: Check your GitHub token and repository access permissions.") from e


def get_tld(file_path: FilePath | None = None, search_parent_directories: bool = True) -> Path | None:
    """
    Retrieves the top-level directory of a Git repository.

    Args:
        file_path (FilePath | None): The path to a file or directory within the repository.
            If None, defaults to the current working directory.
        search_parent_directories (bool): Whether to search parent directories for the Git repository.
            Defaults to True.

    Returns:
        Path | None: The resolved top-level directory of the Git repository if found,
        otherwise None if the path is not a Git repository.
    """
    repo = get_parent_repository(file_path, search_parent_directories=search_parent_directories)
    if not repo:
        return None

    return Path(repo.working_tree_dir)


def lower_first_char(inp: str):
    return inp[:1].lower() + inp[1:] if inp else ""


def upper_first_char(inp: str):
    return inp[:1].upper() + inp[1:] if inp else ""


def get_cloud_call_params(
        max_results: Optional[int] = 10,
        no_max_results: bool = False,
        reject_null: bool = True,
        first_letter_to_lower: bool = False,
        first_letter_to_upper: bool = False,
        **kwargs,
):
    params = {k: v for k, v in kwargs.items() if not is_nothing(v) or not reject_null}

    if max_results and not no_max_results:
        params["MaxResults"] = max_results

    if not first_letter_to_lower and not first_letter_to_upper:
        return params

    if first_letter_to_lower:
        params = {lower_first_char(k): v for k, v in params.items()}

    if first_letter_to_upper:
        params = {upper_first_char(k): v for k, v in params.items()}

    return params


def get_aws_call_params(max_results: Optional[int] = 100, **kwargs):
    return get_cloud_call_params(
        max_results=max_results, first_letter_to_upper=True, **kwargs
    )


def get_google_call_params(max_results: Optional[int] = 200, no_max_results: bool = False, **kwargs):
    return get_cloud_call_params(
        max_results=max_results, no_max_results=no_max_results, first_letter_to_lower=True, **kwargs
    )


def strtobool(val, raise_on_error=False):
    if val is True or val is False or val is None:
        return val

    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
    elif val in ("n", "no", "f", "false", "off", "0"):
        return False
    elif raise_on_error:
        raise ValueError("invalid truth value %r" % (val,))
    else:
        return val


def truncate(msg, max_length, ender="..."):
    max_length -= len(ender)

    if len(msg) >= max_length:
        return msg[:max_length] + ender

    return msg


def is_nothing(v: Any):
    if v in [None, "", {}, []]:
        return True

    if str(v) == "" or str(v).isspace():
        return True

    if isinstance(v, list | set):
        v = [vv for vv in v if vv not in [None, "", {}, []]]
        if len(v) == 0:
            return True

    return False


def is_partial_match(
        a: Optional[str], b: Optional[str], check_prefix_only: bool = False
):
    if is_nothing(a) or is_nothing(b):
        return False

    a = a.lower()
    b = b.lower()

    if check_prefix_only:
        return a.startswith(b) or b.startswith(a)

    return a in b or b in a


def is_non_empty_match(a: Any, b: Any):
    if is_nothing(a) or is_nothing(b):
        return False

    if type(a) != type(b):
        return False

    if isinstance(a, str):
        a = a.lower()
        b = b.lower()
    elif isinstance(a, Mapping):
        a = orjson.dumps(a, default=str, option=orjson.OPT_SORT_KEYS).decode("utf-8")
        b = orjson.dumps(b, default=str, option=orjson.OPT_SORT_KEYS).decode("utf-8")
    elif isinstance(a, list):
        a.sort()
        b.sort()

    if a != b:
        return False

    return True


def all_non_empty(*vals):
    return [val for val in vals if not is_nothing(val)]


def are_nothing(*vals):
    if len(all_non_empty(*vals)) > 0:
        return False

    return True


def first_non_empty(*vals):
    non_empty_vals = all_non_empty(*vals)
    if len(non_empty_vals) == 0:
        return None

    return non_empty_vals[0]


def any_non_empty(m: Mapping, *keys):
    for k in keys:
        v = m.get(k)
        if not is_nothing(v):
            return {k: v}


def yield_non_empty(m: Mapping, *keys):
    for k in keys:
        v = m.get(k)
        if not is_nothing(v):
            yield {k: v}


def first_non_empty_value_from_map(m: Mapping, *keys):
    try:
        _, val = next(yield_non_empty(m, keys))
        return val
    except StopIteration:
        return None


def make_raw_data_export_safe(raw_data: Any, export_to_yaml: bool = False):
    if isinstance(raw_data, Mapping):
        return {
            k: make_raw_data_export_safe(v, export_to_yaml=export_to_yaml)
            for k, v in raw_data.items()
        }
    elif isinstance(raw_data, (set, list)):
        return [
            make_raw_data_export_safe(v, export_to_yaml=export_to_yaml)
            for v in raw_data
        ]

    exported_data = copy(raw_data)
    if isinstance(exported_data, (datetime.date, datetime.datetime)):
        exported_data = exported_data.isoformat()
    elif isinstance(exported_data, pathlib.Path):
        exported_data = str(exported_data)

    if not export_to_yaml or not isinstance(exported_data, str):
        return exported_data

    exported_data = exported_data.replace("${{ ", "${{").replace(" }}", "}}")
    if (
            len(exported_data.splitlines()) > 1
            or "||" in exported_data
            or "&&" in exported_data
    ):
        return scalarstring.LiteralScalarString(exported_data)

    return exported_data


def deduplicate_map(m: Mapping):
    deduplicated_map = make_raw_data_export_safe(m)

    for k, v in m.items():
        if isinstance(v, list):
            deduplicated_map[k] = []

            for elem in v:
                if elem in deduplicated_map[k]:
                    continue

                deduplicated_map[k].append(elem)

            continue

        if isinstance(v, Mapping):
            deduplicated_map[k] = deduplicate_map(v)
            continue

        if k not in deduplicated_map:
            deduplicated_map[k] = v

    return deduplicated_map


def all_values_from_map(m: Mapping):
    values = []

    for v in m.values():
        if isinstance(v, Mapping):
            values.extend(all_values_from_map(v))
            continue

        values.append(v)

    return values


def flatten_map(dictionary, parent_key=False, separator="."):
    """
    https://stackoverflow.com/questions/6027558/flatten-nested-dictionaries-compressing-keys
    Turn a nested dictionary into a flattened dictionary
    :param dictionary: The dictionary to flatten
    :param parent_key: The string to prepend to dictionary's keys
    :param separator: The string used to separate flattened keys
    :return: A flattened dictionary
    """

    items = []
    for key, value in dictionary.items():
        new_key = str(parent_key) + separator + key if parent_key else key
        if isinstance(value, MutableMapping):
            items.extend(flatten_map(value, new_key, separator).items())
        elif isinstance(value, list):
            for k, v in enumerate(value):
                items.extend(flatten_map({str(k): v}, new_key).items())
        else:
            items.append((new_key, value))
    return dict(items)


def flatten_list(matrix: List[Any]):
    array = np.array(matrix)
    return list(array.flatten())


def match_file_extensions(
        p: FilePath,
        allowed_extensions: Optional[List[str]],
        denied_extensions: Optional[List[str]] = None,
):
    if allowed_extensions is None:
        allowed_extensions = []

    if denied_extensions is None:
        denied_extensions = []

    allowed_extensions = [ext.removeprefix(".") for ext in allowed_extensions]
    denied_extensions = [ext.removeprefix(".") for ext in denied_extensions]

    p = Path(p)
    if p.name.startswith("."):
        suffix = p.name.removeprefix(".")
    else:
        suffix = p.suffix.removeprefix(".")

    if (
            len(allowed_extensions) > 0 and suffix not in allowed_extensions
    ) or suffix in denied_extensions:
        return False

    return True


def export_raw_data_to_json(raw_data: Any, **format_opts: Dict[str, Any]) -> str:
    format_opts["indent"] = format_opts.get("indent", 2)
    format_opts["sort_keys"] = format_opts.get("sort_keys", True)

    orjson_opts = None
    if format_opts["indent"]:
        orjson_opts = orjson.OPT_INDENT_2

    if format_opts["sort_keys"]:
        if orjson_opts is None:
            orjson_opts = orjson.OPT_SORT_KEYS
        else:
            orjson_opts |= orjson.OPT_SORT_KEYS

    try:
        return orjson.dumps(raw_data, default=str, option=orjson_opts).decode("utf-8")
    except TypeError:
        return json.dumps(raw_data, default=str, **format_opts)


def get_caller_function_name() -> str:
    """Determine the caller function name for caching."""
    stack = inspect.stack()
    for frame in stack:
        if frame.function.startswith("_") or frame.function == "__init__":
            continue
        return frame.function
    return "unknown_caller"


def export_raw_data_to_yaml(raw_data: Any) -> str:
    raw_data_stream = StringIO()

    def str_representer(dumper, data):
        # Represent plain strings without quotes
        if '\n' in data or '||' in data or '&&' in data:
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
        if any(char in data for char in
               [':', '{', '}', '[', ']', ',', '&', '*', '#', '?', '|', '-', '<', '>', '=', '!', '%', '@', '`']):
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')
        return dumper.represent_scalar('tag:yaml.org,2002:str', data)

    def dict_to_commented_map(data):
        if isinstance(data, dict):
            commented_map = CommentedMap()
            for key, value in data.items():
                commented_map[key] = dict_to_commented_map(value)
            return commented_map
        elif isinstance(data, list):
            return [dict_to_commented_map(item) for item in data]
        else:
            return data

    commented_raw_data = dict_to_commented_map(raw_data)

    yaml = YAML()
    yaml.default_flow_style = False
    yaml.indent(sequence=4, offset=2)
    yaml.representer.add_representer(str, str_representer)
    yaml.representer.ignore_aliases = lambda x: True
    yaml.dump(commented_raw_data, raw_data_stream)

    raw_data_yaml = raw_data_stream.getvalue()
    raw_data_stream.close()

    return raw_data_yaml


def get_encoding_for_file_path(file_path: FilePath) -> str:
    file_path = Path(file_path)
    suffix = file_path.suffix
    if suffix in [".yaml", ".yml"]:
        return "yaml"
    elif suffix in [".json"]:
        return "json"

    return "raw"


def wrap_raw_data_for_export(
        raw_data: Union[Mapping, Any],
        allow_encoding: Union[bool, str] = True,
        **format_opts: Any
) -> str:
    raw_data = make_raw_data_export_safe(raw_data)

    if isinstance(allow_encoding, str):
        if allow_encoding == "yaml":
            return export_raw_data_to_yaml(raw_data)
        elif allow_encoding == "json":
            return export_raw_data_to_json(raw_data, **format_opts)
        elif allow_encoding == "raw":
            return raw_data

        allow_encoding = strtobool(allow_encoding, raise_on_error=True)

    if allow_encoding:
        return export_raw_data_to_json(raw_data, **format_opts)

    return raw_data


def make_hashable(value: Any) -> Any:
    """Ensure a value is hashable for use as a cache key."""
    if isinstance(value, dict):
        return frozenset((k, make_hashable(v)) for k, v in value.items())
    elif isinstance(value, (list, set, tuple)):
        return tuple(make_hashable(v) for v in value)
    elif isinstance(value, pathlib.Path):
        return str(value)  # Convert paths to strings
    elif isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()  # Convert datetime to string
    elif isinstance(value, (int, float, str, bool, type(None))):
        return value  # Primitive types are already hashable

    try:
        # Attempt JSON serialization as a fallback
        return export_raw_data_to_json(value)
    except (TypeError, ValueError):
        # As a last resort, fallback to string representation
        return str(value)


def get_log_level(level):
    if level is None:
        return DEFAULT_LOG_LEVEL

    if isinstance(level, int):
        return level

    return getattr(logging, level.upper(), DEFAULT_LOG_LEVEL)


def get_loggers():
    loggers = [logging.getLogger()]
    loggers += [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    return loggers


def find_logger(name: str):
    loggers = get_loggers()
    for logger in loggers:
        if logger.name == name:
            return logger

    return None


def get_default_dict(
        use_sorted_dict: bool = False,
        default_type: Type = dict,
        levels: int = 2
) -> defaultdict:
    """
    Create a nested `defaultdict` with the specified number of levels.

    This function recursively generates a nested `defaultdict` structure.
    At the final level, the specified `default_type` is used as the default factory.
    This can be any type with a constructor that takes no arguments, such as `list`,
    `set`, `dict`, or custom types.

    Args:
        use_sorted_dict (bool, optional): Whether to use `SortedDict` instead of `dict` for
            dictionary levels. Only applies if `default_type` is `dict`. Defaults to `False`.
        default_type (Type, optional): The type to use as the default factory at the final level.
            Defaults to `dict`.
        levels (int, optional): The number of nested levels in the `defaultdict`.
            Must be greater than or equal to 1. Defaults to `2`.

    Returns:
        defaultdict: A nested `defaultdict` structure. The base level contains items of
        the specified `default_type`, and higher levels are `defaultdict`.

    Raises:
        ValueError: If `levels` is less than 1.

    Example:
        >>> # Create a 3-level nested dict with dictionaries at the deepest level
        >>> nested_dict = get_default_dict(levels=3)
        >>> nested_dict["level1"]["level2"]["key"] = "value"
        >>> print(nested_dict)
        defaultdict(<function ...>, {'level1': defaultdict(<function ...>, {'level2': {'key': 'value'}})})

        >>> # Create a 3-level nested dict with sets at the deepest level
        >>> nested_set_dict = get_default_dict(default_type=set, levels=3)
        >>> nested_set_dict["a"]["b"]["c"].add("value")
        >>> print(nested_set_dict)
        defaultdict(<function ...>, {'a': defaultdict(<function ...>, {'b': defaultdict(<class 'set'>, {'c': {'value'}})})})

        >>> # Create a simple 1-level defaultdict of lists
        >>> list_dict = get_default_dict(default_type=list, levels=1)
        >>> list_dict["key"].append("value")
        >>> print(list_dict)
        defaultdict(<class 'list'>, {'key': ['value']})
    """
    if levels < 1:
        raise ValueError("The number of levels must be greater than or equal to 1.")

    if levels == 1:
        return defaultdict(SortedDict if use_sorted_dict and default_type == dict else default_type)

    return defaultdict(lambda: get_default_dict(
        use_sorted_dict=use_sorted_dict,
        default_type=default_type,
        levels=levels - 1
    ))


def sanitize_asset(d: Any):
    if not isinstance(d, Mapping):
        return d

    filtered = {}

    for k, v in d.items():
        if k.startswith("_"):
            continue

        if not is_nothing(v):
            if isinstance(v, Mapping):
                filtered[k] = sanitize_asset(v)
            elif isinstance(v, list):
                filtered[k] = []

                for vv in v:
                    vv = sanitize_asset(vv)
                    if vv not in filtered[k]:
                        filtered[k].append(vv)
            else:
                if k == "description":
                    filtered[k] = truncate(
                        v, max_length=MAX_DESCRIPTION_LENGTH
                    )
                    continue

                filtered[k] = v

    return filtered


def file_path_depth(file_path: FilePath):
    depth = []

    for p in Path(file_path).parts:
        if p == ".":
            continue

        depth.append(p)

    return len(depth)


def file_path_rel_to_root(file_path: FilePath):
    depth = file_path_depth(file_path)
    path_rel_to_root = []

    for i in range(depth):
        path_rel_to_root.append("..")

    return "/".join(path_rel_to_root)


def sanitize_key(key: str, delim: str = "_"):
    return "".join(map(lambda x: x if (x.isalnum() or x == delim) else delim, key))


def unhump_map(m: Mapping[str, Any], drop_without_prefix: Optional[str] = None):
    unhumped = {}

    for k, v in m.items():
        if drop_without_prefix is not None and not k.startswith(drop_without_prefix):
            continue

        unhumped_key = inflection.underscore(k)

        if isinstance(v, Mapping):
            unhumped[unhumped_key] = unhump_map(v)
            continue

        unhumped[unhumped_key] = v

    return unhumped


def filter_list(
        l: Optional[List[str]],
        allowlist: List[str] = None,
        denylist: List[str] = None,
):
    if l is None:
        l = []

    if allowlist is None:
        allowlist = []

    if denylist is None:
        denylist = []

    filtered = []

    for elem in l:
        if (len(allowlist) > 0 and elem not in allowlist) or elem in denylist:
            continue

        filtered.append(elem)

    return filtered


def decode_hcl2(hcl2_data: str):
    hcl2_data_stream = StringIO(hcl2_data)
    return hcl2.load(hcl2_data_stream)


class Utils:
    def __init__(
            self,
            inputs: Optional[Any] = None,
            from_environment: bool = True,
            from_stdin: bool = False,
            to_console: bool = False,
            to_file: bool = True,
            logging: Optional[Logging] = None,
            logger: Optional[logging.Logger] = None,
            log_marker: Optional[str] = None,
            logger_name: Optional[str] = None,
            log_file_name: Optional[FilePath] = None,
            logged_statements_allowlist: List[str] = None,
            logged_statements_denylist: List[str] = None,
            **kwargs,
    ):
        self.logs = defaultdict(set)

        self.default_log_marker = log_marker
        self.default_logged_statements_allowlist = logged_statements_allowlist
        self.default_logged_statements_denylist = logged_statements_denylist
        self.errors = []
        self.last_error = None
        self.last_error_message = None

        if inputs is None:
            inputs = {}

        if from_environment:
            inputs = os.environ | inputs

        if from_stdin and not strtobool(os.getenv("OVERRIDE_STDIN", False)):
            inputs_from_stdin = sys.stdin.read()

            if not is_nothing(inputs_from_stdin):
                try:
                    inputs = json.loads(inputs_from_stdin) | inputs
                except json.JSONDecodeError as exc:
                    raise RuntimeError(
                        f"Failed to decode stdin:\n{inputs_from_stdin}"
                    ) from exc

        self.from_stdin = from_stdin
        self.inputs = CaseInsensitiveDict(inputs)

        doppler_token = os.getenv('DOPPLER_TOKEN')
        if doppler_token and DopplerSDK is not None:
            try:
                doppler = DopplerSDK()
                doppler.set_access_token(doppler_token)
                secrets_response = doppler.secrets.list(
                    project=DOPPLER_PROJECT,
                    config=DOPPLER_CONFIG,
                    accepts="application/json"
                ).secrets

                for name, secret_info in secrets_response.items():
                    self.inputs[name.removeprefix("FLIPSIDE_")] = secret_info['computed']
            except Exception as e:
                self.errors.append(f"Failed to fetch Doppler secrets: {str(e)}")

        self.VERBOSE = kwargs.get(
            "verbose",
            self.get_input(
                "verbose",
                default=VERBOSE,
                is_bool=True,
            ),
        )

        self.VERBOSITY = kwargs.get(
            "verbosity",
            self.get_input(
                "verbosity",
                default=VERBOSITY,
            ),
        )

        self.DEBUG_MARKERS = kwargs.get(
            "debug_markers",
            self.decode_input(
                "debug_markers",
                default=[],
                decode_from_base64=False,
            ),
        )

        self.LOG_FILE_NAME = kwargs.get(
            "log_file_name",
            self.get_input(
                "log_file_name",
                default=LOG_FILE_NAME,
            ),
        )

        self.active_marker = None
        self.log_file_count = 0

        self.tld = get_tld()

        self.merger = Merger(
            [(list, ["append"]), (dict, ["merge"]), (set, ["union"])],
            ["override"],
            ["override"],
        )

        self.to_console = to_console
        self.to_file = to_file

        if logger_name is None:
            logger_name = self.get_input("logger_name", required=False, default=self.get_unique_signature())

        if log_file_name is None:
            log_file_name = self.get_input("log_file_name", required=False, default=f"{logger_name}.log")

        self.logging = logging or Logging(to_console=to_console,
                                          to_file=to_file,
                                          logger=logger,
                                          logger_name=logger_name,
                                          log_file_name=log_file_name,
                                          log_marker=log_marker,
                                          logged_statements_allowlist=logged_statements_allowlist,
                                          logged_statements_denylist=logged_statements_denylist)
        self.logger = self.logging.logger

        # Initialize the shareable Terraform module parameters
        self._shareable_terraform_module_params = {
            "verbose": self.VERBOSE,
            "verbosity": self.VERBOSITY,
            "debug_markers": self.DEBUG_MARKERS,
            "log_file_name": self.LOG_FILE_NAME,
        }

        # Add additional attributes dynamically
        for name, value in kwargs.items():
            if (
                    name not in self._shareable_terraform_module_params
                    and isinstance(value, (bool, str, int))
                    and "port" not in name
                    and "api" not in name
            ):
                self._shareable_terraform_module_params[name] = value

        # Ensure kwargs includes all shareable params for further propagation
        self.kwargs = {
            **kwargs,  # Include original kwargs
            **self._shareable_terraform_module_params,  # Add shareable params
            "logger": self.logger,  # Add the logger instance
            "log_file_name": self.LOG_FILE_NAME,  # Include the log file name
            "log_marker": self.default_log_marker,  # Add default log marker
            "logging": self.logging,
        }

        if self.errors:
            self.exit_run(exit_on_completion=True)


    @property
    def decoders(self):
        return {
            'json': {
                'function': json.loads,
                'exception': json.JSONDecodeError
            },
            'yaml': {
                'function': self.decode_yaml,
                'exception': YAMLError
            },
            'hcl2': {
                'function': decode_hcl2,
                'exception': lark.exceptions.ParseError
            }
        }

    def multi_merge(self, *maps):
        merged_maps = {}
        for m in maps:
            merged_maps = self.merger.merge(merged_maps, m)

        return merged_maps

    def local_path(self, file_path: FilePath):
        path = Path(file_path)
        if path.is_absolute():
            return path.resolve()

        if self.tld is None:
            caller = get_caller()
            raise RuntimeError(
                f"[{caller}] CLI is not being run locally and has no top level directory to use with {file_path}"
            )

        return Path(self.tld, file_path).resolve()

    def local_path_exists(self, file_path: FilePath):
        caller = get_caller()

        if is_nothing(file_path):
            raise RuntimeError(f"File path being checked from {caller} is empty")

        local_file_path = self.local_path(file_path)

        if not local_file_path.exists():
            raise NotADirectoryError(
                f"Directory {local_file_path} from {caller} does not exist locally"
            )

        return local_file_path

    def get_repository_dir(self, dir_path: FilePath):
        if self.tld:
            repo_dir_path = self.local_path(dir_path)
            repo_dir_path.mkdir(parents=True, exist_ok=True)
        else:
            repo_dir_path = Path(dir_path)

        return repo_dir_path

    def get_shared_terraform_module_params(self):
        module_params = [
            {
                "name": "params",
                "default": {},
                "required": False,
                "description": "Override for multiple params",
                "type": "any",
                "json_encode": True,
                "base64_encode": True,
            },
            {
                "name": "debug_markers",
                "default": [],
                "required": False,
                "description": "Identifiers to generate verbose debug statements for",
                "type": "list(string)",
                "json_encode": True,
                "base64_encode": False,
            },
        ]

        for name, default in self._shareable_terraform_module_params.items():
            if (
                    not isinstance(default, (bool, str, int))
                    or "port" in name
                    or "api" in name
            ):
                continue

            module_params.append(
                {
                    "name": name,
                    "default": default,
                    "required": False,
                    "description": "Port library parameter",
                }
            )

        return module_params

    def get_unique_signature(self, delim="/"):
        return self.__class__.__module__ + delim + self.__class__.__name__

    def verbosity_exceeded(self, verbose: bool, verbosity: int):
        return self.logging.verbosity_exceeded(verbose, verbosity)

    def logged_statement(
            self,
            msg: str,
            json_data: Optional[List[Mapping[str, Any]] | Mapping[str, Any]] = None,
            labeled_json_data: Optional[Mapping[str, Mapping[str, Any]]] = None,
            identifiers: Optional[List[str]] = None,
            verbose: Optional[bool] = False,
            verbosity: Optional[int] = 1,
            active_marker: Optional[str] = None,
            log_level: Literal[
                "debug", "info", "warning", "error", "fatal", "critical"
            ] = "debug",
            log_marker: Optional[str] = None,
            allowlist: Optional[List[str]] = None,
            denylist: Optional[List[str]] = None,
    ):
        return self.logging.logged_statement(msg=msg,
                                             json_data=json_data,
                                             labeled_json_data=labeled_json_data,
                                             identifiers=identifiers,
                                             verbose=verbose,
                                             verbosity=verbosity,
                                             active_marker=active_marker,
                                             log_level=log_level,
                                             log_marker=log_marker,
                                             allowlist=allowlist,
                                             denylist=denylist, )

    def get_unique_sub_path(self, dir_path: FilePath):
        local_dir_path = self.local_path(dir_path)

        def get_sub_path():
            return local_dir_path.joinpath(str(uuid.uuid1()))

        local_sub_path = get_sub_path()

        while local_sub_path.exists():
            local_sub_path = get_sub_path()

        return local_sub_path

    def get_rel_to_root(self, dir_path: FilePath):
        try:
            return self.tld.relative_to(dir_path)
        except (ValueError, AttributeError):
            self.logger.warning(
                f"Could not calculate path for directory {dir_path} relative to the repository TLD {self.tld}",
                exc_info=True,
            )

        return None

    def log_results(
            self,
            results,
            log_file_name,
            no_formatting=False,
            ext=None,
            verbose=False,
            verbosity=0,
    ):
        if self.verbosity_exceeded(verbose, verbosity):
            return

        try:
            if not no_formatting:
                log_file_name += ".json"
                results = wrap_raw_data_for_export(results, allow_encoding=True)
        except TypeError:
            results = str(results)

        if not isinstance(results, str):
            results = str(results)

        log_dir = Path.cwd() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        if ext is not None:
            log_file_name += f".{ext}"

        log_file_name = log_file_name.replace(" ", "_").lower()
        log_file_name_with_ext = log_file_name + ".log"
        log_file_path = log_dir.joinpath(log_file_name_with_ext)

        while log_file_path.exists():
            self.log_file_count += 1
            log_file_name_with_ext = log_file_name + f".{self.log_file_count}.log"
            log_file_path = log_dir.joinpath(log_file_name_with_ext)

        with open(log_file_path, "w") as fh:
            fh.write(results)

        self.logged_statement(f"New results log: {log_file_path}")

        return results

    def filter_map(
            self,
            m: Optional[Mapping[str, Any]],
            allowlist: List[str] = None,
            denylist: List[str] = None,
    ):
        if m is None:
            m = {}

        if allowlist is None:
            allowlist = []

        if denylist is None:
            denylist = []

        fm = {}
        rm = {}

        for k, v in m.items():
            self.logged_statement(
                f"Checking if {k} is allowed", verbose=True, verbosity=2
            )
            if (len(allowlist) > 0 and k not in allowlist) or k in denylist:
                self.logged_statement(
                    f"Removing {k} from map: {list(m.keys())},"
                    f" either not in allowlist: {allowlist},"
                    f" or in denylist: {denylist}",
                    verbose=True,
                    verbosity=2,
                )
                rm[k] = v
            else:
                self.logged_statement(
                    f"{k} is allowed, allowing its value '{v}' through",
                    verbose=True,
                    verbosity=2,
                )
                fm[k] = v

        return fm, rm

    def get_input(
            self, k, default=None, required=False, is_bool=False, is_integer=False
    ) -> Any:
        inp = self.inputs.get(k)

        if is_nothing(inp):
            inp = default

        if is_bool:
            inp = strtobool(inp)

        if is_integer and inp is not None:
            try:
                inp = int(inp)
            except TypeError as exc:
                raise RuntimeError(f"Input {k} not an integer: {inp}") from exc

        if is_nothing(inp) and required:
            raise RuntimeError(
                f"Required input {k} not passed from inputs:\n{self.inputs}"
            )

        return inp

    def decode_input(
            self,
            k: str,
            default: Optional[Any] = None,
            required: bool = False,
            decode_from_json: bool = True,
            decode_from_yaml: bool = False,
            decode_from_base64: bool = True,
            allow_none: bool = True,
    ):
        conf = self.get_input(k, default=default, required=required)

        if conf is None:
            return conf

        if conf == default:
            return conf

        if decode_from_base64:
            try:
                conf = conf.replace(" ", "").replace("\n", "").replace("\r", "")
                conf = base64.b64decode(conf, validate=True).decode("utf-8")
            except binascii.Error as exc:
                raise RuntimeError(f"Failed to decode {conf} from base64") from exc

        if decode_from_json and decode_from_yaml:
            raise AttributeError(f"decode_from_json and decode_from_yaml are mutually exclusive")

        if decode_from_json:
            try:
                conf = json.loads(conf)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Failed to decode {conf} from JSON") from exc

        if decode_from_yaml:
            try:
                conf = self.decode_yaml(conf)
            except YAMLError as exc:
                raise RuntimeError(f"Failed to decode {conf} from YAML") from exc

        if conf is None and not allow_none:
            return default

        return conf

    def get_file(
            self,
            file_path: FilePath,
            decode: Optional[bool] = True,
            return_path: Optional[bool] = False,
            charset: Optional[str] = "utf-8",
            errors: Optional[str] = "strict",
            headers: Optional[Mapping[str, str]] = None,
            raise_on_not_found: bool = False,
    ):
        if headers is None:
            headers = {}

        file_data = ""

        def state_negative_result(result: str):
            self.logger.warning(result)

            if raise_on_not_found:
                raise FileNotFoundError(result)

        try:
            if is_url(str(file_path)):
                self.logged_statement(f"Getting remote URL: {file_path}")
                response = requests.get(file_path, headers=headers)
                if response.ok:
                    file_data = response.content.decode(charset, errors)
                else:
                    state_negative_result(
                        f"URL {file_path} could not be read:"
                        f" [{response.status_code}] {response.reason}"
                    )
            else:
                local_file = self.local_path(file_path)

                self.logged_statement(f"Getting local file: {local_file}")

                if local_file.is_file():
                    file_data = local_file.read_text(charset, errors)
                else:
                    state_negative_result(f"{file_path} does not exist")
        except ValueError as exc:
            self.logger.warning(f"Reading {file_path} not supported: {exc}")
            decode = False

        if decode:
            self.logged_statement(f"Decoding {file_path}")
            file_data = (
                {}
                if is_nothing(file_data)
                else self.decode_file(file_data=file_data, file_path=file_path)
            )

        retval = [file_data]

        if return_path:
            retval.append(file_path)

        if len(retval) == 1:
            return retval[0]

        return tuple(retval)

    def decode_yaml(self, yaml_data: str):
        yaml = YAML(typ="safe")

        class Ref:
            def __init__(self, value):
                self.value = value

            def __repr__(self):
                return f"!Ref {self.value}"

        def ref_constructor(loader, node):
            value = loader.construct_scalar(node)
            return Ref(value)

        SafeConstructor.add_constructor('!Ref', ref_constructor)

        yaml_data_stream = StringIO(yaml_data)
        return yaml.load(yaml_data_stream)

    def decode_data(self, data: str):
        for decoder in self.decoders.values():
            try:
                return decoder['function'](data)
            except decoder['exception']:
                continue

        raise RuntimeError(f"Exhausted all known decode methods against raw data:\n{data}")

    def decode_file(
            self,
            file_data: str,
            file_path: Optional[FilePath] = None,
            suffix: Optional[str] = None,
    ):
        if suffix is None:
            if file_path is not None:
                self.logger.info(f"Decoding file {file_path}")
                suffix = Path(file_path).suffix.lstrip(".").lower()

        try:
            if suffix == "yml" or suffix == "yaml":
                self.logger.info(f"Data is being loaded from YAML")
                return self.decode_yaml(file_data)
            elif suffix == "json":
                self.logger.info(f"Data is being loaded from JSON")
                return json.loads(file_data)
            elif suffix == "tf":
                self.logger.info(f"Data is being loaded from HCL2")
                return decode_hcl2(file_data)
            else:
                return self.decode_data(file_data)
        except (YAMLError, json.JSONDecodeError, lark.exceptions.ParseError, TypeError) as exc:
            raise RuntimeError(f"Failed to parse file {file_path}") from exc

    def update_file(
            self,
            file_path: FilePath,
            file_data: Any,
            allow_encoding: Optional[Union[bool, str]] = None,
            allow_empty: Optional[bool] = False,
            **format_opts: Any
    ):
        if is_nothing(file_data) and not allow_empty:
            self.logger.warning(f"Empty file data for {file_path} not allowed")
            return None

        if allow_encoding is None:
            allow_encoding = get_encoding_for_file_path(file_path)
            self.logger.debug(f"Detected encoding for {file_path}: {allow_encoding}")

        file_data = wrap_raw_data_for_export(file_data,
                                             allow_encoding=allow_encoding,
                                             **format_opts)

        if not isinstance(file_data, str):
            file_data = str(file_data)

        self.logged_statement(f"Updating local file {file_path}", verbose=True)
        lock = FileLock(f"{file_path}.lock", timeout=MAX_FILE_LOCK_WAIT)

        try:
            with lock.acquire():
                local_file = self.local_path(file_path)

                self.logged_statement(f"Updating local file: {local_file}")

                local_file.parent.mkdir(parents=True, exist_ok=True)

                return local_file.write_text(file_data)
        except Timeout:
            raise RuntimeError(
                f"Cannot update file path {file_path},"
                f" another instance of this application currently holds the lock."
            )
        finally:
            lock.release()
            self.delete_file(lock.lock_file)

    def delete_file(self, file_path: FilePath):
        local_file = self.local_path(file_path)
        self.logger.warning(f"Deleting local file {file_path}")
        return local_file.unlink(missing_ok=True)

    def sanitize_map(
            self,
            m: Dict[str, Any],
            delim: str = "_",
            max_sanitize_depth: Optional[int] = None,
            depth: int = 0,
    ):
        if depth >= max_sanitize_depth:
            self.logged_statement(
                f"Max sanitize depth of {max_sanitize_depth} exceeded for map, returning raw map"
            )
            return m

        sanitized = {}

        for k, v in m.items():
            new_k = sanitize_key(key=k, delim=delim)
            new_v = deepcopy(v)

            if isinstance(v, Dict):
                new_v = self.sanitize_map(
                    m=v,
                    delim=delim,
                    max_sanitize_depth=max_sanitize_depth,
                    depth=depth + 1,
                )

            if (
                    new_k in sanitized
                    and isinstance(sanitized[new_k], Dict)
                    and isinstance(new_v, Dict)
            ):
                sanitized[new_k] = self.merger.merge(sanitized[new_k], new_v)
                continue

            sanitized[new_k] = new_v

        return sanitized

    def exit_run(
            self,
            results: Any = None,
            unhump_results: bool = False,
            prefix: Optional[str] = None,
            prefix_allowlist: Optional[List[str]] = None,
            prefix_denylist: Optional[List[str]] = None,
            prefix_delimiter: Optional[str] = "_",
            sort_by_field: Optional[str] = None,
            format_results: bool = True,
            encode_to_base64: bool = False,
            encode_all_values_to_base64: bool = False,
            key: Optional[str] = None,
            exit_on_completion: bool = True,
            **format_opts,
    ):
        try:
            self.log_results(results, "results")

            if len(self.errors) > 0:
                raise RuntimeError(os.linesep.join(self.errors))

            if prefix:
                unhump_results = True

            if prefix_allowlist is None:
                prefix_allowlist = []

            if prefix_denylist is None:
                prefix_denylist = []

            if results is None:
                results = {}

            if sort_by_field:
                sorted_results = {}
                for top_level_key, top_level_value in results.items():
                    field_data = top_level_value.get(sort_by_field)
                    if is_nothing(field_data):
                        raise FormattingError(
                            f"Cannot return results when top level key {top_level_key}'s value for sort by field {sort_by_field} is empty or does not exist"
                        )

                    sorted_results[field_data] = top_level_value

                results = sorted_results

            if unhump_results:
                if prefix:
                    for top_level_key, top_level_value in results.items():
                        if not isinstance(top_level_value, Mapping):
                            results[top_level_key] = top_level_value
                            continue

                        unhumped_result = {}

                        for field_name, field_data in top_level_value.items():
                            unhumped_key = inflection.underscore(field_name)

                            if (
                                    (
                                            is_nothing(prefix_allowlist)
                                            or field_name in prefix_allowlist
                                            or unhumped_key in prefix_allowlist
                                    )
                                    and field_name not in prefix_denylist
                                    and unhumped_key not in prefix_denylist
                            ):
                                unhumped_key = prefix_delimiter.join(
                                    [prefix, unhumped_key]
                                )

                            if isinstance(field_data, Mapping):
                                unhumped_result[unhumped_key] = unhump_map(
                                    field_data
                                )
                                continue

                            unhumped_result[unhumped_key] = field_data

                        results[top_level_key] = unhumped_result
                else:
                    results = unhump_map(results)

            if not exit_on_completion:
                return results

            if "default" not in format_opts:
                format_opts["default"] = str

            def encode_result_with_base64(r: Any):
                if format_results:
                    self.logger.info(
                        "Formatting results before encoding them with base64"
                    )
                    r = wrap_raw_data_for_export(r, **format_opts)

                return base64.b64encode(r.encode("utf-8")).decode("utf-8")

            if encode_all_values_to_base64:
                self.logger.info("Encoding all top-level values in results with base64")
                results = {
                    top_level_key: encode_result_with_base64(top_level_value)
                    for top_level_key, top_level_value in deepcopy(results).items()
                }
                self.log_results(results, "results values base64 encoded")

            if encode_to_base64:
                self.logger.info("Encoding results with base64")
                results = encode_result_with_base64(results)
                self.log_results(results, "results base64 encoded")

            if key:
                self.logger.info(f"Wrapping results in key {key}")
                results = {key: results}

            if not isinstance(results, str):
                self.logger.info("Dumping results to JSON")
                results = orjson.dumps(results, default=str).decode("utf-8")

            sys.stdout.write(results)
            sys.exit(0)
        except FormattingError as exc:
            err_msg = (
                f"Failed to dump results because of a formatting error:\n\n{results}"
            )
            self.logger.critical(err_msg, exc_info=True)
            raise RuntimeError(err_msg) from exc