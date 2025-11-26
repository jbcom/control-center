"""File Data Type Utilities.

This module provides utilities for working with file paths, Git repositories,
and file extensions. It includes functions for retrieving the parent Git repository,
cloning repositories to temporary directories, and checking file extensions and encodings.
"""

from __future__ import annotations

import os
import sys
import tempfile

from pathlib import Path


if sys.version_info >= (3, 10):
    from typing import TypeAlias, Union
else:
    from typing import Union

    from typing_extensions import TypeAlias

from git import GitCommandError, InvalidGitRepositoryError, NoSuchPathError, Repo


FilePath: TypeAlias = Union[str, os.PathLike[str]]
"""Type alias for file paths that can be represented as strings or os.PathLike objects."""


def get_parent_repository(
    file_path: FilePath | None = None, search_parent_directories: bool = True
) -> Repo | None:
    """Retrieves the Git repository object for a given path.

    Args:
        file_path (FilePath | None): The path to a file or directory within the repository.
            If None, defaults to the current working directory.
        search_parent_directories (bool): Whether to search parent directories for the Git repository.
            Defaults to True.

    Returns:
        Repo | None: The Git repository object if found, otherwise None if the path is not a Git repository.
    """
    directory = Path(file_path) if file_path else Path.cwd()

    try:
        return Repo(str(directory), search_parent_directories=search_parent_directories)
    except (InvalidGitRepositoryError, NoSuchPathError):
        return None


def get_repository_name(repo: Repo) -> str | None:
    """Retrieves the name of the Git repository.

    Args:
        repo (Repo): The Git repository object.

    Returns:
        str | None: The name of the repository if found, otherwise None.
    """
    try:
        remote_url = next(iter(repo.remotes[0].urls))
        return Path(remote_url).stem
    except (IndexError, ValueError, StopIteration):
        return None


def clone_repository_to_temp(
    repo_owner: str, repo_name: str, github_token: str, branch: str | None = None
) -> tuple[Path, Repo]:
    """Clones a Git repository to a temporary directory for file operations.

    Args:
        repo_owner (str): The owner of the GitHub repository.
        repo_name (str): The name of the GitHub repository to clone.
        github_token (str): The GitHub token to access the repository.
        branch (str | None): The branch to clone. If None, the default branch is cloned.

    Returns:
        tuple[Path, Repo]: The path to the cloned repository's top-level directory and the Repo object.

    Raises:
        EnvironmentError: If errors occur while trying to clone a Git repository.
    """
    repo_url = (
        f"https://{github_token}:x-oauth-basic@github.com/{repo_owner}/{repo_name}.git"
    )

    try:
        temp_dir = Path(tempfile.mkdtemp())
        repo = Repo.clone_from(
            repo_url, str(temp_dir), branch=branch if branch else None
        )
        return temp_dir, repo
    except GitCommandError as e:
        error_message = "Git command error occurred"
        raise OSError(error_message) from e
    except InvalidGitRepositoryError as e:
        error_message = "The repository is invalid or corrupt."
        raise OSError(error_message) from e
    except NoSuchPathError as e:
        error_message = "The specified path does not exist."
        raise OSError(error_message) from e
    except PermissionError as e:
        error_message = "Permission denied: Check your GitHub token and repository access permissions."
        raise OSError(error_message) from e


def get_tld(
    file_path: FilePath | None = None, search_parent_directories: bool = True
) -> Path | None:
    """Retrieves the top-level directory of a Git repository.

    Args:
        file_path (FilePath | None): The path to a file or directory within the repository.
            If None, defaults to the current working directory.
        search_parent_directories (bool): Whether to search parent directories for the Git repository.
            Defaults to True.

    Returns:
        Path | None: The resolved top-level directory of the Git repository if found,
        otherwise None if the path is not a Git repository.
    """
    repo = get_parent_repository(
        file_path, search_parent_directories=search_parent_directories
    )
    return Path(repo.working_tree_dir) if repo and repo.working_tree_dir else None


def match_file_extensions(
    p: FilePath,
    allowed_extensions: list[str] | None = None,
    denied_extensions: list[str] | None = None,
) -> bool:
    """Matches the file extension of a given path against allowed or denied extensions.

    Args:
        p (FilePath): The path of the file to check.
        allowed_extensions (list[str] | None): List of allowed file extensions (without leading dot).
        denied_extensions (list[str] | None): List of denied file extensions (without leading dot).

    Returns:
        bool: True if the file's extension is allowed and not denied, otherwise False.
    """
    allowed_extensions = [
        ext.removeprefix(".").lower() for ext in (allowed_extensions or [])
    ]
    denied_extensions = [
        ext.removeprefix(".").lower() for ext in (denied_extensions or [])
    ]

    p = Path(p)
    suffix = (
        p.name.removeprefix(".")
        if p.name.startswith(".")
        else p.suffix.removeprefix(".")
    ).lower()

    return not (
        (allowed_extensions and suffix not in allowed_extensions)
        or suffix in denied_extensions
    )


def get_encoding_for_file_path(file_path: FilePath) -> str:
    """Determines the encoding type based on the file extension.

    Args:
        file_path (FilePath): The path of the file to check.

    Returns:
        str: The encoding type as a string (e.g., "yaml", "json", "hcl", "toml", or "raw").
    """
    suffix = Path(file_path).suffix
    if suffix in [".yaml", ".yml"]:
        return "yaml"
    elif suffix == ".json":
        return "json"
    elif suffix in [".hcl", ".tf"]:
        return "hcl"
    elif suffix in [".toml", ".tml"]:
        return "toml"
    return "raw"


def file_path_depth(file_path: FilePath) -> int:
    """Calculates the depth of a given file path (the number of directories in the path).

    Args:
        file_path (FilePath): The file path to calculate depth for.

    Returns:
        int: The depth of the file path, excluding the root.
    """
    p = Path(file_path)
    parts = p.parts  # parts is a tuple of strings

    if p.is_absolute():
        # Exclude root '/' from parts
        parts = parts[1:]  # Still a tuple

    # Exclude '.' and empty strings from parts
    filtered_parts = [part for part in parts if part not in (".", "")]

    return len(filtered_parts)


def file_path_rel_to_root(file_path: FilePath) -> str:
    """Constructs a relative path to the root directory from the given file path.

    Args:
        file_path (FilePath): The file path for which to construct the relative path.

    Returns:
        str: A string representing the relative path to the root.
    """
    depth = file_path_depth(file_path)
    if depth == 0:
        return ""
    return "/".join([".."] * depth)
