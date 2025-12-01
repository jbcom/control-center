import concurrent.futures
import functools
import json
import os
import re
import secrets
import shlex
import ssl
import string
import subprocess
import tempfile
import time
from collections import defaultdict, deque
from collections.abc import Sequence
from copy import copy, deepcopy
from datetime import datetime, timedelta
from http.client import IncompleteRead
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Set, Tuple, Union

import boto3
import googleapiclient.errors
import gspread
import hvac
import inflection
import pandas as pd
from boto3.resources.base import ServiceResource
from botocore.config import Config as AWSConfig
from botocore.exceptions import ClientError as AWSClientError
from botocore.exceptions import ParamValidationError as AWSParamValidationError
from gitignore_parser import parse_gitignore
from hvac.exceptions import InvalidPath
from ruamel.yaml import YAML, StringIO, YAMLError
from terraform_modules import settings, utils, vault_config
from terraform_modules.aws_client import AWSClient
from terraform_modules.errors import (
    FailedResponseError,
    RequestRateLimitedError,
    StateFileNotFoundError,
)
from terraform_modules.flat_maps import FlatMapContainer
from terraform_modules.github_client import GithubClient
from terraform_modules.google_client import GoogleClient
from terraform_modules.settings import SCOPES, SUBJECT
from terraform_modules.slack_client import SlackClient
from terraform_modules.terraform_module_resources import TerraformModuleResources
from terraform_modules.terraform_remote_module_variables import TerraformRemoteModuleVariables
from terraform_modules.utils import FilePath, Utils, get_caller_function_name, get_default_dict, make_hashable
from terraform_modules.vault_client import VaultClient
from terraform_modules.zoom_client import ZoomClient

from github import Repository as GithubRepo
from github import Team as GithubTeam
from sendgrid import SendGridAPIClient


class TerraformDataSource(Utils):
    ALLOWED_ENTITY_FIELDS = [
        "identifier",
        "title",
        "team",
        "properties",
        "relations",
    ]

    REQUIRED_ENTITY_FIELDS = [
        "identifier",
        "properties",
    ]

    REQUIRED_BLUEPRINT_FIELDS = [
        "identifier",
        "schema",
    ]

    S3_STORAGE_TYPES = [
        "StandardStorage",
        "IntelligentTieringFAStorage",
        "IntelligentTieringIAStorage",
        "IntelligentTieringAAStorage",
        "IntelligentTieringAIAStorage",
        "IntelligentTieringDAAStorage",
        "StandardIAStorage",
        "StandardIASizeOverhead",
        "StandardIAObjectOverhead",
        "OneZoneIAStorage",
        "OneZoneIASizeOverhead",
        "ReducedRedundancyStorage",
        "GlacierInstantRetrievalSizeOverhead",
        "GlacierInstantRetrievalStorage",
        "GlacierStorage",
        "GlacierStagingStorage",
        "GlacierObjectOverhead",
        "GlacierS3ObjectOverhead",
        "DeepArchiveStorage",
        "DeepArchiveObjectOverhead",
        "DeepArchiveS3ObjectOverhead",
        "DeepArchiveStagingStorage",
        "ExpressOneZone",
    ]

    TEAM_CALENDAR_ID = "flipsidecrypto.com_ds25ucouu8q2mcbvhn9ru8eacg@group.calendar.google.com"

    DEFAULT_USER_OUS = ["/Users", "Users/2FANotEnforced", "/Contract"]
    DEFAULT_TIMEZONE = "America/New_York"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        (
            terraform_module_resources,
            time_elapsed,
        ) = TerraformModuleResources.get_all_resources(
            terraform_modules=utils.get_available_methods(self.__class__),
            module_params=self.get_shared_terraform_module_params(),
            module_type="data_source",
        )

        self.logger.info(f"Getting Data Source Terraform Module Resources took {time_elapsed:0.2f} seconds to run")

        self.terraform_module_resources = terraform_module_resources

        # Initialize a nested client cache
        self._client_cache = get_default_dict(levels=2)

    def _get_cached_client(self, **kwargs) -> Optional[Any]:
        """Retrieve a client from the cache.

        # NOPARSE
        """

        caller = get_caller_function_name()

        # Transform each keyword argument into a hashable form
        hashable_kwargs = {k: make_hashable(v) for k, v in kwargs.items()}
        cache_key = frozenset(hashable_kwargs.items())

        return self._client_cache[caller].get(cache_key)

    def _set_cached_client(self, client: Any, **kwargs):
        """Store a client in the cache.

        # NOPARSE
        """
        caller = get_caller_function_name()

        # Transform each keyword argument into a hashable form
        hashable_kwargs = {k: make_hashable(v) for k, v in kwargs.items()}
        cache_key = frozenset(hashable_kwargs.items())

        self._client_cache[caller][cache_key] = client

    def get_aws_client(
        self,
        client_name: str,
        execution_role_arn: Optional[str] = None,
        role_session_name: Optional[str] = None,
        config: Optional[AWSConfig] = None,
        **client_args,
    ) -> boto3.client:
        """Gets the active AWS client.

        # NOPARSE
        """
        execution_role_arn = execution_role_arn or self.get_input("EXECUTION_ROLE_ARN", required=False)
        role_session_name = role_session_name or self.get_input("ROLE_SESSION_NAME", required=False)

        cached_client = self._get_cached_client(
            client_name=client_name,
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
            config=config,
            **client_args,
        )
        if cached_client:
            return cached_client

        aws_client = AWSClient(execution_role_arn, **self.kwargs).get_aws_client(
            client_name=client_name,
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
            config=config,
            **client_args,
        )
        self._set_cached_client(
            aws_client,
            client_name=client_name,
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
            config=config,
            **client_args,
        )
        return aws_client

    def get_aws_resource(
        self,
        service_name: str,
        execution_role_arn: Optional[str] = None,
        role_session_name: Optional[str] = None,
        config: Optional[AWSConfig] = None,
        **resource_args,
    ) -> ServiceResource:
        """Gets the active AWS resource.

        # NOPARSE
        """
        execution_role_arn = execution_role_arn or self.get_input("EXECUTION_ROLE_ARN", required=False)
        role_session_name = role_session_name or self.get_input("ROLE_SESSION_NAME", required=False)

        cached_resource = self._get_cached_client(
            service_name=service_name,
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
            config=config,
            **resource_args,
        )
        if cached_resource:
            return cached_resource

        aws_client = AWSClient(execution_role_arn, **self.kwargs)
        resource = aws_client.get_aws_resource(
            service_name=service_name,
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
            config=config,
            **resource_args,
        )
        self._set_cached_client(
            resource,
            service_name=service_name,
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
            config=config,
            **resource_args,
        )
        return resource

    def get_aws_session(
        self, execution_role_arn: Optional[str] = None, role_session_name: Optional[str] = None
    ) -> boto3.Session:
        """Gets the active AWS session.

        # NOPARSE
        """

        execution_role_arn = execution_role_arn or self.get_input("EXECUTION_ROLE_ARN", required=False)
        role_session_name = role_session_name or self.get_input("ROLE_SESSION_NAME", required=False)

        # Check cache
        cached_session = self._get_cached_client(
            execution_role_arn=execution_role_arn, role_session_name=role_session_name
        )
        if cached_session:
            return cached_session

        # Create new session
        aws_client = AWSClient(execution_role_arn, **self.kwargs)
        session = aws_client.get_aws_session(role_session_name=role_session_name, execution_role_arn=execution_role_arn)

        # Cache the session
        self._set_cached_client(session, execution_role_arn=execution_role_arn, role_session_name=role_session_name)
        return session

    def get_github_client(
        self, github_owner: Optional[str] = None, github_repo: Optional[str] = None, github_branch: Optional[str] = None
    ):
        """Gets the active Github client.

        # NOPARSE
        """
        github_owner = github_owner or self.get_input("GITHUB_OWNER", default=settings.GITHUB_OWNER)

        github_repo = github_repo or self.get_input("GITHUB_REPO", default=settings.GITHUB_REPO)

        github_branch = github_branch or self.get_input("GITHUB_BRANCH")
        github_token = self.get_input("GITHUB_TOKEN", required=True)

        cached_client = self._get_cached_client(
            github_owner=github_owner, github_repo=github_repo, github_branch=github_branch, github_token=github_token
        )
        if cached_client:
            return cached_client

        github_client = GithubClient(
            github_owner=github_owner,
            github_repo=github_repo,
            github_branch=github_branch,
            github_token=github_token,
            **self.kwargs,
        )
        self._set_cached_client(
            github_client,
            github_owner=github_owner,
            github_repo=github_repo,
            github_branch=github_branch,
            github_token=github_token,
        )
        return github_client

    def get_google_client(
        self, service_account_file: str | dict[str, Any] | None = None, subject: str | None = None
    ) -> GoogleClient:
        """Gets the active Google client.

        # NOPARSE
        """
        if not subject and not service_account_file:
            subject = SUBJECT

        service_account_file = service_account_file or self.get_input("GOOGLE_SERVICE_ACCOUNT")

        cached_client = self._get_cached_client(service_account_file=service_account_file, subject=subject)
        if cached_client:
            return cached_client

        google_client = GoogleClient(
            scopes=SCOPES,
            subject=subject,
            service_account_file=service_account_file,
            **self.kwargs,
        )
        self._set_cached_client(google_client, service_account_file=service_account_file, subject=subject)
        return google_client

    def get_slack_client(self):
        """Gets the active Slack client.

        # NOPARSE
        """
        token = self.get_input("SLACK_TOKEN", required=True)
        bot_token = self.get_input("SLACK_BOT_TOKEN", required=True)

        cached_client = self._get_cached_client(token=token, bot_token=bot_token)
        if cached_client:
            return cached_client

        slack_client = SlackClient(token=token, bot_token=bot_token, **self.kwargs)
        self._set_cached_client(slack_client, token=token, bot_token=bot_token)
        return slack_client

    def get_vault_client(self) -> hvac.Client:
        """Gets the active Vault client.

        # NOPARSE
        """
        vault_url = self.get_input(vault_config.VAULT_URL_ENV_VAR, required=False)
        vault_namespace = self.get_input(vault_config.VAULT_NAMESPACE_ENV_VAR, required=False)
        vault_token = self.get_input("VAULT_TOKEN", required=False)

        cached_client = self._get_cached_client(
            vault_url=vault_url, vault_namespace=vault_namespace, vault_token=vault_token
        )
        if cached_client:
            return cached_client

        vault_client = VaultClient.get_vault_client(
            vault_url=vault_url, vault_namespace=vault_namespace, vault_token=vault_token, **self.kwargs
        )
        self._set_cached_client(
            vault_client, vault_url=vault_url, vault_namespace=vault_namespace, vault_token=vault_token
        )
        return vault_client

    def get_zoom_client(self) -> ZoomClient:
        """Gets the active Zoom client.

        # NOPARSE
        """
        client_id = self.get_input("ZOOM_CLIENT_ID", required=True)
        client_secret = self.get_input("ZOOM_CLIENT_SECRET", required=True)
        account_id = self.get_input("ZOOM_ACCOUNT_ID", required=True)

        cached_client = self._get_cached_client(client_id=client_id, client_secret=client_secret, account_id=account_id)
        if cached_client:
            return cached_client

        zoom_client = ZoomClient(client_id=client_id, client_secret=client_secret, account_id=account_id, **self.kwargs)
        self._set_cached_client(zoom_client, client_id=client_id, client_secret=client_secret, account_id=account_id)
        return zoom_client

    @functools.lru_cache(maxsize=1)
    def get_caller_account_id(self):
        """Gets the active caller account ID

        # NOPARSE
        """
        sts_client = self.get_aws_client(client_name="sts")
        response = sts_client.get_caller_identity()
        return response.get("Account")

    @functools.lru_cache(maxsize=1)
    def get_identity_store_id(self, key: str = "IdentityStoreId"):
        """Gets the active identity store id

        # NOPARSE
        """
        sso_admin = self.get_aws_client(client_name="sso-admin")

        self.logger.info(f"Getting {key}")
        identity = sso_admin.list_instances()
        try:
            identity_store_id = identity["Instances"][0][key]
            self.logger.info(f"{key}: {identity_store_id}")
            return identity_store_id
        except (KeyError, IndexError) as exc:
            raise RuntimeError(f"Failed to get {key}: {identity}") from exc

    @functools.lru_cache(maxsize=1000)
    def get_git_repository(
        self, github_owner: Optional[str] = None, github_repo: Optional[str] = None, github_branch: Optional[str] = None
    ):
        """Gets a Github repository

        # NOPARSE
        """
        github_owner = github_owner or self.get_input("github_owner", default=settings.GITHUB_OWNER)

        github_repo = github_repo or self.get_input("github_repo", default=settings.GITHUB_REPO)

        github_token = self.get_input("GITHUB_TOKEN", required=True)

        return utils.clone_repository_to_temp(
            repo_owner=github_owner, repo_name=github_repo, github_token=github_token, branch=github_branch
        )

    def _terraform_state_exists_resource(self, resource: dict[str, Any], resources: list) -> bool:
        """
        Checks if a resource exists in the given list of resources.

        # NOPARSE
        """
        for item in resources:
            if (
                item["mode"] == resource["mode"]
                and item["type"] == resource["type"]
                and item["name"] == resource["name"]
            ):
                self.logged_statement(
                    "Found existing resource",
                    identifiers=[resource["mode"], resource["type"], resource["name"]],
                )
                return True
        return False

    def _terraform_state_merge_state_data(self, state: dict[str, Any], state_data: dict[str, Any]) -> None:
        """
        Merges state data into the given state dictionary.

        # NOPARSE
        """
        if utils.is_nothing(state):
            state.update(state_data)
            return

        resources = state.get("resources", [])

        for resource in state_data.get("resources", []):
            if resource["mode"] == "data" and self._terraform_state_exists_resource(resource, resources):
                self.logged_statement(
                    "Resource exists in target state",
                    identifiers=[resource["type"], resource["name"]],
                )
                if resource in resources:
                    state["resources"].remove(resource)
                else:
                    self.logged_statement(
                        "Skipping resource",
                        identifiers=[
                            resource["mode"],
                            resource["type"],
                            resource["name"],
                        ],
                    )

    def _terraform_state_load_from_file(self, state: dict[str, Any], state_path: FilePath) -> None:
        """
        Loads state data from a local file and merges it into the given state dictionary.

        # NOPARSE
        """
        local_state_path = self.local_path(state_path)
        if not local_state_path.exists():
            raise StateFileNotFoundError(state_path)

        self._terraform_state_merge_state_data(state, self.get_file(state_path))

    def _terraform_state_load_from_bucket(self, state: dict[str, Any], state_path: FilePath, bucket: str) -> None:
        """
        Loads state data from an S3 bucket and merges it into the given state dictionary.

        # NOPARSE
        """
        s3 = self.get_aws_client(client_name="s3")

        try:
            state_file_obj = s3.get_object(Bucket=bucket, Key=state_path)
            self._terraform_state_merge_state_data(
                state,
                self.decode_file(
                    file_data=state_file_obj["Body"].read().decode("utf-8"),
                    suffix="json",
                ),
            )
        except s3.exceptions.NoSuchKey as exc:
            raise StateFileNotFoundError(state_path, f"in bucket {bucket}") from exc

    def get_gitops_repository_file(self, file_path: FilePath, **kwargs):
        """Gets a Gitops repository file

        # NOPARSE
        """
        if utils.is_url(file_path):
            return self.get_file(file_path=file_path, **kwargs)

        file_path = Path(file_path)
        repo = utils.get_parent_repository(file_path)
        if repo is None:
            tld = None
            repo_name = None
        else:
            tld = Path(repo.working_tree_dir)
            repo_name = utils.get_repository_name(repo) or tld.name

        if not repo_name:
            if file_path.is_absolute():
                self.logger.info(f"Getting absolute local file path {file_path}")
                return self.get_file(file_path, **kwargs)

            self.logger.info(
                f"Cloning the gitops repository locally so {file_path} can be fetched from it since it does not exist in its own local repository"
            )
            try:
                tld, repo = self.get_git_repository(
                    github_owner=settings.GITHUB_OWNER, github_repo=settings.GITHUB_REPO, github_branch="main"
                )
            except EnvironmentError as exc:
                raise RuntimeError("Failed to get gitops repository locally") from exc

            repo_name = utils.get_repository_name(repo) or tld.name
            self.logger.info(f"Gitops repository cloned to {tld}, repo_name: {repo_name}")

        if repo_name == "gitops":
            if not file_path.is_absolute():
                self.logger.warning(f"Joining relative path {file_path} to the tld {tld}")
                file_path = tld.joinpath(file_path)
                self.logger.info(f"New file path: {file_path}")

            return self.get_file(file_path=file_path, **kwargs)

        def remove_tld(fp: Path):
            if not tld:
                return fp

            try:
                return fp.relative_to(tld)
            except ValueError:
                return fp

        file_path = remove_tld(file_path)
        self.logger.warning(f"Getting a Gitops repository file {file_path} from a non-Gitops repository {repo_name}")

        return self.git_client.get_repository_file(file_path=file_path, **kwargs)

    def get_files(
        self,
        repository_owner: Optional[str] = None,
        repository_name: Optional[str] = None,
        files: Optional[list[FilePath]] = None,
        relative_to_root: Optional[FilePath] = None,
        decode: Optional[bool] = None,
        allowed_extensions: Optional[list[str]] = None,
        denied_extensions: Optional[list[str]] = None,
        charset: Optional[str] = "utf-8",
        errors: Optional[str] = "strict",
        headers: Optional[dict[str, str]] = None,
        gitignore_file: Optional[FilePath] = None,
        match_dotfiles: bool = False,
        exit_on_completion: bool = True,
        github_client: Optional[GithubClient] = None,
    ):
        """Gets files either locally or from a repository

        generator=key: files, module_class: files

        name: repository_owner, required: false, type: string
        name: repository_name, required: false, type: string
        name: files, required: false, default: [], json_encode: true, base64_encode: true
        name: relative_to_root, required: false, type: string
        name: decode, required: false, default: true
        name: allowed_extensions, required: false, default: [], json_encode: true
        name: denied_extensions, required: false, default: [], json_encode: true
        name: charset, required: false, default: "utf-8"
        name: errors, required: false, default: "strict"
        name: headers, required: false, default: {}, json_encode: true, base64_encode: true
        name: gitignore_file, required: false, type: string
        name: match_dotfiles, required: false, default: false
        """
        if repository_owner is None:
            repository_owner = self.get_input("repository_owner", required=False)

        if repository_name is None:
            repository_name = self.get_input("repository_name", required=False)

        if files is None:
            files = self.decode_input("files", required=False, default=[], allow_none=False)

        if relative_to_root is None:
            relative_to_root = self.get_input("relative_to_root", required=False)

        if decode is None:
            decode = self.get_input("decode", required=False, default=True, is_bool=True)

        if allowed_extensions is None:
            allowed_extensions = self.decode_input(
                "allowed_extensions",
                required=False,
                default=[],
                decode_from_base64=False,
                allow_none=False,
            )

        if denied_extensions is None:
            denied_extensions = self.decode_input(
                "denied_extensions",
                required=False,
                default=[],
                decode_from_base64=False,
                allow_none=False,
            )

        if charset is None:
            charset = self.get_input("charset", required=False, default="utf-8")

        if errors is None:
            errors = self.get_input("errors", required=False, default="strict")

        if headers is None:
            headers = self.decode_input("headers", required=False, default={}, allow_none=False)

        if gitignore_file is None:
            gitignore_file = self.get_input("gitignore_file", required=False)

        if match_dotfiles is None:
            match_dotfiles = self.get_input("match_dotfiles", required=False, default=False, is_bool=True)

        use_local_repo = len(utils.all_non_empty(repository_owner, repository_name)) == 0
        gitignore_matches = None
        delete_gitignore_file = False

        if use_local_repo:
            if utils.is_nothing(gitignore_file):
                gitignore_file = self.local_path(".gitignore")
            else:
                gitignore_file = Path(gitignore_file)
        elif github_client is None:
            github_client = self.get_github_client(github_owner=repository_owner, github_repo=repository_name)
            gitignore_file_contents = github_client.get_repository_file(file_path=gitignore_file, decode=False)
            if not utils.is_nothing(gitignore_file_contents):
                tmp_gitignore_file = tempfile.NamedTemporaryFile(delete=False)
                with open(tmp_gitignore_file.name, "w") as fh:
                    fh.write(gitignore_file_contents)

                gitignore_file = Path(tmp_gitignore_file.name)
                delete_gitignore_file = True

        if gitignore_file.exists():
            self.logged_statement(f"Matching files against gitignore file: {gitignore_file}")
            gitignore_matches = parse_gitignore(gitignore_file)

        if delete_gitignore_file:
            gitignore_file.unlink(missing_ok=True)

        results = {}

        tic = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []

            for file in files:
                file_path = Path(file)

                if not match_dotfiles and file_path.name.startswith("."):
                    self.logged_statement(f"Rejecting {file_path} because dotfiles are not being matched")
                    continue

                if (
                    len(allowed_extensions) > 0 and file_path.suffix not in allowed_extensions
                ) or file_path.suffix in denied_extensions:
                    self.logged_statement(f"Rejecting {file_path}")
                    continue

                if gitignore_matches is not None and gitignore_matches(str(file_path.resolve())):
                    self.logged_statement(f"Rejecting {file_path} because of the gitignore file")
                    continue

                if use_local_repo:
                    futures.append(
                        executor.submit(
                            self.get_file,
                            file_path=file_path,
                            decode=decode,
                            return_path=True,
                            charset=charset,
                            errors=errors,
                            headers=headers,
                            raise_on_not_found=True,
                        )
                    )
                else:
                    futures.append(
                        executor.submit(
                            github_client.get_repository_file,
                            file_path=file_path,
                            decode=decode,
                            return_path=True,
                            return_sha=False,
                            charset=charset,
                            errors=errors,
                            raise_on_not_found=True,
                        )
                    )

            for future in concurrent.futures.as_completed(futures):
                try:
                    file_data, file_path = future.result()
                    if not utils.is_nothing(file_path):
                        self.logger.info(f"Successfully read {file_path}")

                        file_key = file_path
                        if relative_to_root:
                            file_key = Path(file_path).relative_to(relative_to_root)

                        file_key = str(file_key)

                        results[file_key] = file_data
                    else:
                        raise RuntimeError("Failed to get at least one file")
                except Exception as exc:
                    executor.shutdown(wait=False, cancel_futures=True)
                    raise RuntimeError(f"Failed to get files: {files}") from exc

        toc = time.perf_counter()
        self.logger.info(f"Getting files took {toc - tic:0.2f} seconds to run")

        self.logged_statement("Files", json_data=results, verbose=True, verbosity=2)

        return self.exit_run(
            results=results,
            key="files",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def scan_dir(
        self,
        repository_owner: Optional[str] = None,
        repository_name: Optional[str] = None,
        files_path: Optional[FilePath] = None,
        files_glob: Optional[str] = None,
        files_match: Optional[str] = None,
        paths_only: Optional[bool] = None,
        reject_dotfiles: Optional[bool] = None,
        decode: Optional[bool] = None,
        flatten: Optional[bool] = None,
        sanitize_keys: Optional[bool] = None,
        max_sanitize_depth: Optional[int] = None,
        stem_only: Optional[bool] = None,
        recursive: Optional[bool] = None,
        allowed_extensions: Optional[list[str]] = None,
        denied_extensions: Optional[list[str]] = None,
        exit_on_completion: bool = True,
    ):
        """Scans a directory to get configuration

        generator=key: tree, module_class: os

        name: repository_owner, required: false, type: string
        name: repository_name, required: false, type: string
        name: files_path, required: true, type: string
        name: files_glob, required: false, default: "*"
        name: files_match, required: false, type: string
        name: paths_only, required: false, default: false
        name: reject_dotfiles, required: false, default: true
        name: decode, required: false, default: true
        name: flatten, required: false, default: false
        name: sanitize_keys, required: false, default: false
        name: max_sanitize_depth, required: false, type: number
        name: stem_only, required: false, default: false
        name: recursive, required: false, default: true
        name: allowed_extensions, required: false, default: [], json_encode: true
        name: denied_extensions, required: false, default: [], json_encode: true
        name: replace_chars_in_key_using, required: false
        name: replace_chars_in_key_with, required: false"""
        if repository_owner is None:
            repository_owner = self.get_input("repository_owner", required=False)

        if repository_name is None:
            repository_name = self.get_input("repository_name", required=False)

        if files_path is None:
            files_path = self.get_input("files_path", required=True)

        if files_glob is None:
            files_glob = self.get_input("files_glob", required=False, default="*")

        if files_match is None:
            files_match = self.get_input("files_match", required=False)

        if paths_only is None:
            paths_only = self.get_input("paths_only", required=False, default=False, is_bool=True)

        if reject_dotfiles is None:
            reject_dotfiles = self.get_input("reject_dotfiles", required=False, default=True, is_bool=True)

        if decode is None:
            decode = self.get_input("decode", required=False, default=True, is_bool=True)

        if flatten is None:
            flatten = self.get_input("flatten", required=False, default=False, is_bool=True)

        if sanitize_keys is None:
            sanitize_keys = self.get_input("sanitize_keys", required=False, default=False, is_bool=True)

        if max_sanitize_depth is None:
            max_sanitize_depth = self.get_input("max_sanitize_depth", required=False, is_integer=True)

        if stem_only is None:
            stem_only = self.get_input("stem_only", required=False, default=False, is_bool=True)

        if recursive is None:
            recursive = self.get_input("recursive", required=False, default=True, is_bool=True)

        if allowed_extensions is None:
            allowed_extensions = self.decode_input(
                "allowed_extensions",
                required=False,
                default=[],
                decode_from_base64=False,
            )

        if denied_extensions is None:
            denied_extensions = self.decode_input(
                "denied_extensions",
                required=False,
                default=[],
                decode_from_base64=False,
            )

        files_path = Path(files_path)
        use_local_repo = len(utils.all_non_empty(repository_owner, repository_name)) == 0

        def is_valid_path(p: FilePath):
            p = Path(p)

            if not utils.match_file_extensions(
                p,
                allowed_extensions=allowed_extensions,
                denied_extensions=denied_extensions,
            ):
                self.logged_statement(
                    f"Rejecting file {p} either not in allowed extensions or in denied extensions",
                    labeled_json_data={
                        "allowed extensions": allowed_extensions,
                        "denied extensions": denied_extensions,
                    },
                    verbose=True,
                    verbosity=2,
                )

                return False

            if not reject_dotfiles or ".terraform/modules" in str(p):
                self.logged_statement(f"File {p} is valid", verbose=True, verbosity=2)
                return True

            for part in p.resolve().parts:
                if part.startswith("."):
                    self.logged_statement(f"Rejecting hidden file path {p}", verbose=True, verbosity=2)
                    return False

            self.logged_statement(f"File path {p} is not hidden and is valid", verbose=True, verbosity=2)
            return True

        if use_local_repo:

            def is_valid_local_path(p: FilePath):
                p = self.local_path(p)

                if not p.is_file():
                    self.logged_statement(f"Rejecting non-file {p}", verbose=True, verbosity=2)
                    return False

                return is_valid_path(p)

            abs_local_file_path = self.local_path(files_path)
            if recursive:
                self.logger.info(f"Getting all local files matching '{files_glob}' under {files_path} recursively")
                paths = [p for p in abs_local_file_path.rglob(files_glob) if is_valid_local_path(p)]
            else:
                self.logger.info(f"Getting all local files matching '{files_glob}' under {files_path}")
                paths = [p for p in abs_local_file_path.glob(files_glob) if is_valid_local_path(p)]

            if paths_only:
                self.logger.info("Returning paths")
                return self.exit_run(
                    results=paths,
                    key="tree",
                    encode_to_base64=True,
                    format_json=False,
                    exit_on_completion=exit_on_completion,
                )

            files_data = self.get_files(
                files=paths,
                relative_to_root=abs_local_file_path,
                decode=decode,
                allowed_extensions=allowed_extensions,
                denied_extensions=denied_extensions,
                exit_on_completion=False,
            )
        else:
            github_client = self.get_github_client(
                github_owner=repository_owner,
                github_repo=repository_name,
            )
            self.logger.info(f"Getting all remote files under {files_path}")
            contents = github_client.repo.get_contents(str(files_path))
            paths = []

            while contents:
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    if not recursive:
                        self.logged_statement(f"Skipping directory {file_content.path}, non-recursive scan")
                        continue

                    self.logged_statement(f"Scanning directory {file_content.path}")
                    contents.extend(github_client.repo.get_contents(file_content.path))
                    continue

                file_path = file_content.path
                if is_valid_path(file_path):
                    paths.append(file_content.path)

            if paths_only:
                self.logger.info("Returning paths")
                self.exit_run(
                    results=paths,
                    key="tree",
                    encode_to_base64=True,
                    format_json=False,
                    exit_on_completion=exit_on_completion,
                )

            files_data = self.get_files(
                repository_owner=repository_owner,
                repository_name=repository_name,
                files=paths,
                decode=decode,
                allowed_extensions=allowed_extensions,
                denied_extensions=denied_extensions,
                match_dotfiles=(False if reject_dotfiles else True),
                exit_on_completion=False,
                github_client=github_client,
            )

        if flatten:
            self.log_results(files_data, "flat_tree")
            return self.exit_run(
                results=files_data,
                key="tree",
                encode_to_base64=True,
                format_json=False,
                exit_on_completion=exit_on_completion,
            )

        tree = {}

        def fill_tree_from_path(p: FilePath):
            b = tree

            for part in Path(p).parts:
                self.logged_statement(
                    f"Filling tree for path {p}, branch: {part}",
                    verbose=True,
                    verbosity=2,
                )

                # Ensure b[part] is a dictionary
                if part not in b:
                    self.logged_statement(f"New part: {part} for the tree", verbose=True, verbosity=2)
                    b[part] = {}
                elif not isinstance(b[part], dict):
                    raise RuntimeError(f"Parsing {p}, expected {part} to be a dictionary, but found {type(b[part])}")

                b = b[part]

            # Ensure the final branch is a dictionary
            if not isinstance(b, dict):
                raise RuntimeError(f"Parsing {p}, expected the final branch to be a dictionary, but found {type(b)}")

            return b

        for file_path, file_data in files_data.items():
            cur_path = Path(file_path)
            if not utils.is_nothing(files_match) and not files_path.match(files_match):
                self.logger.warning(f"{file_path} was rejected, does not match the pattern {files_match}")
                continue

            branch = fill_tree_from_path(cur_path.parent)

            if not isinstance(branch, dict):
                raise RuntimeError(f"{file_path} scanned malformed, branch not a dictionary but a {type(branch)}")

            file_key = cur_path.stem if stem_only else cur_path.name
            branch[file_key] = file_data

        if sanitize_keys:
            self.logger.info(f"Sanitizing the tree until max sanitize depth {max_sanitize_depth}")
            self.log_results(tree, "raw tree")
            tree = self.sanitize_map(m=tree, max_sanitize_depth=max_sanitize_depth)

        self.log_results(tree, "tree")
        return self.exit_run(
            results=tree,
            key="tree",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def get_valid_gitkeep_records(self, record_dir: FilePath, record_files: list[str]):
        """Gets valid Gitkeep records
        NOPARSE
        """
        valid_records = []

        github_client = self.get_github_client()

        for record_file in set(record_files):
            record_path = Path(record_dir).joinpath(record_file)
            if self.tld:
                record_exists = record_path.exists() and record_path.is_file()
            else:
                record_data = github_client.get_repository_file(file_path=record_path, decode=False)
                record_exists = False if utils.is_nothing(record_data) else True

            if not record_exists:
                self.logger.warning(f"Discarding invalid record {record_path}")
                continue

            valid_records.append(record_file)

        self.logger.info(f"Gitkeep records for {record_dir}: {valid_records}")

        return valid_records

    def get_gitkeep_record(self, record_dir: Optional[FilePath] = None, exit_on_completion: bool = True):
        """Gets the gitkeep record for a directory

        generator=key: record, module_class: git

        name: record_dir, required: true, type: string"""
        if record_dir is None:
            record_dir = self.get_input("record_dir", required=True)

        self.logger.info(f"Getting the Gitkeep record for {record_dir}")

        record_dir = self.local_path(record_dir) if self.tld else Path(record_dir)
        records_file = record_dir.joinpath(".gitkeep")
        github_client = self.get_github_client()

        if self.tld:
            gitkeep_record = self.get_file(records_file, decode=False)
        else:
            gitkeep_record = github_client.get_repository_file(records_file, decode=False)

        if utils.is_nothing(gitkeep_record):
            self.logger.info("No existing records")
            return self.exit_run(
                key="record",
                encode_to_base64=True,
                format_json=False,
                exit_on_completion=exit_on_completion,
            )

        valid_records = self.get_valid_gitkeep_records(record_dir=record_dir, record_files=gitkeep_record.splitlines())

        return self.exit_run(
            valid_records,
            key="record",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def group_and_format_files(
        self,
        files: Optional[list[dict[str, dict[str, str]]]] = None,
        preserve_names_as_is: Optional[list[str]] = None,
        exit_on_completion: Optional[bool] = True,
    ):
        """Groups and formats files

        generator=key: files, module_class: os
        extra_output=key: gitkeep_records

        name: files, required: true, json_encode: true, base64_encode: true
        name: preserve_names_as_is, required: false, default: [], json_encode: true"""

        if files is None:
            files = self.decode_input("files", required=True)

        if preserve_names_as_is is None:
            preserve_names_as_is = self.decode_input(
                "preserve_names_as_is",
                required=False,
                default=[],
                decode_from_base64=False,
                allow_none=False,
            )

        self.logger.info(f"Grouping and formatting files [Preserving names: {preserve_names_as_is}]")

        grouped_files = {}
        gitkeep_records = {}

        for folders_group in files:
            for folder_name, files_group in folders_group.items():
                if folder_name not in gitkeep_records:
                    gitkeep_records[folder_name] = []

                for file_name, file_data in files_group.items():
                    if utils.is_nothing(file_data):
                        continue

                    if file_name not in gitkeep_records[folder_name]:
                        gitkeep_records[folder_name].append(file_name)

                    if not isinstance(file_data, str):
                        file_data = str(file_data)

                    file_path = Path(folder_name).joinpath(file_name)

                    if file_name in preserve_names_as_is:
                        file_path = str(file_path)
                        self.logger.info(f"Preserving {file_path} as is")
                        grouped_files[file_path] = file_data
                        continue

                    match file_path.suffix.lower():
                        case ".json":
                            self.logger.info(f"Formatting JSON file {file_path}")
                            try:
                                json_data = json.loads(file_data)
                                file_data = utils.wrap_raw_data_for_export(json_data, allow_encoding=True)

                            except json.JSONDecodeError:
                                self.logger.warning(
                                    f"Reverting to unformatted JSON file because of error during " f"formatting",
                                    exc_info=True,
                                )
                        case ".tf":
                            fmt_cmd = shlex.split("terraform fmt -")
                            self.logger.info(f"Formatting HCL file {file_path} with {fmt_cmd}")
                            p = subprocess.run(fmt_cmd, input=file_data, capture_output=True, text=True)
                            if p.returncode == 0:
                                file_data = p.stdout
                                self.logged_statement(f"Formatted {file_path}:\n{file_data}")
                            else:
                                self.logger.warning(
                                    f"Reverting to unformatted Terraform file because of error during formatting: {p.stderr}"
                                )

                    file_path = str(file_path)

                    grouped_files[file_path] = file_data

        self.log_results(grouped_files, "grouped_files")

        return self.exit_run(
            results=dict(
                files=utils.wrap_raw_data_for_export(grouped_files, allow_encoding=True),
                gitkeep_records=utils.wrap_raw_data_for_export(gitkeep_records, allow_encoding=True),
            ),
            encode_all_values_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def config_file_data(
        self,
        config: Optional[Any] = None,
        config_dir: Optional[str] = None,
        config_dirs: Optional[list[str]] = None,
        config_glob: Optional[str] = None,
        config_files_match: Optional[str] = None,
        ordered_config_merge: Optional[bool] = None,
        nest_config_under_key: Optional[str] = None,
        allowed_extensions: Optional[list[str]] = None,
        denied_extensions: Optional[list[str]] = None,
        exit_on_completion: Optional[bool] = True,
    ):
        """Gathers config file data

        generator=key: config, module_class: utils

        name: config, required: false, default: {}, json_encode: true, base64_encode: true
        name: config_dir, required: false, type: string
        name: config_dirs, required: false, default: [], json_encode: true
        name: config_glob, required: false, type: string
        name: config_files_match, required: false, type: string
        name: ordered_config_merge, required: false, default: true
        name: nest_config_under_key, required: false, type: string
        name: allowed_extensions, required: false, default: [], json_encode: true
        name: denied_extensions, required: false, default: [], json_encode: true"""

        if config is None:
            config = self.decode_input("config", required=False, default={}, allow_none=False)

        if config_dir is None:
            config_dir = self.get_input("config_dir", required=False)

        if config_dirs is None:
            config_dirs = self.decode_input(
                "config_dirs",
                required=False,
                default=[],
                decode_from_base64=False,
                allow_none=False,
            )

        if config_glob is None:
            config_glob = self.get_input("config_glob", required=False)

        if config_files_match is None:
            config_files_match = self.get_input("config_files_match", required=False)

        if ordered_config_merge is None:
            ordered_config_merge = self.get_input("ordered_config_merge", required=False, default=True, is_bool=True)

        if nest_config_under_key is None:
            nest_config_under_key = self.get_input("nest_config_under_key", required=False)

        if allowed_extensions is None:
            allowed_extensions = self.decode_input(
                "allowed_extensions",
                required=False,
                default=[],
                decode_from_base64=False,
                allow_none=False,
            )

        if denied_extensions is None:
            denied_extensions = self.decode_input(
                "denied_extensions",
                required=False,
                default=[],
                decode_from_base64=False,
                allow_none=False,
            )

        self.logged_statement(
            "Getting config files",
            labeled_json_data={
                "config": config,
                "config_dir": config_dir,
                "config_dirs": config_dirs,
                "allowed_extensions": allowed_extensions,
                "denied_extensions": denied_extensions,
                "nest config under key": nest_config_under_key,
            },
            verbose=True,
            verbosity=2,
        )

        if not utils.is_nothing(config_dir):
            config_dirs.insert(0, config_dir)

        for _config_dir in list(set(config_dirs)):
            self.logger.info(f"Scanning {_config_dir} for configuration")
            config_files = self.scan_dir(
                files_path=_config_dir,
                files_glob=config_glob,
                files_match=config_files_match,
                sanitize_keys=True,
                max_sanitize_depth=1,
                stem_only=True,
                decode=True,
                allowed_extensions=allowed_extensions,
                denied_extensions=denied_extensions,
                exit_on_completion=False,
            )

            self.log_results(config_files, "config files")

            if ordered_config_merge:
                self.logger.info("Merging config file data on top of any inline configuration")
                config |= config_files
            else:
                self.logger.info("Performing deep merge of config file data into any inline configuration")
                config = self.merger.merge(config, config_files)

        if not utils.is_nothing(nest_config_under_key):
            self.logger.info(f"Nesting config file data under key '{nest_config_under_key}'")
            config = {nest_config_under_key: config}

        self.log_results(config, "config file data")

        return self.exit_run(
            config,
            key="config",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def merge_records_data(
        self,
        records: Optional[Any] = None,
        record_files: Optional[list[str]] = None,
        record_directories: Optional[dict[str, str]] = None,
        record_categories: Optional[dict[str, dict[str, str]]] = None,
        nest_records_under_key: Optional[str] = None,
        allowlist: Optional[list[str]] = None,
        denylist: Optional[list[str]] = None,
        ordered_records_merge: Optional[bool] = None,
        exit_on_completion: bool = True,
    ):
        """Merges records data

        generator=key: records, module_class: utils

        name: records, required: false, default: {}, json_encode: true, base64_encode: true
        name: record_files, required: false, default: [], json_encode: true
        name: record_directories, required: false, default: {}, json_encode: true, base64_encode: true
        name: record_categories, required: false, default: {}, json_encode: true, base64_encode: true
        name: nest_records_under_key, required: false, type: string
        name: allowlist, required: false, default: [], json_encode: true
        name: denylist, required: false, default: [], json_encode: true
        name: ordered_records_merge, required: false, default: true
        """
        if records is None:
            records = self.decode_input("records", required=False, default={}, allow_none=False)

        if record_files is None:
            record_files = self.decode_input(
                "record_files",
                required=False,
                default=[],
                decode_from_base64=False,
                allow_none=False,
            )

        if record_directories is None:
            record_directories = self.decode_input("record_directories", required=False, default={}, allow_none=False)

        if record_categories is None:
            record_categories = self.decode_input("record_categories", required=False, default={}, allow_none=False)

        if nest_records_under_key is None:
            nest_records_under_key = self.get_input("nest_records_under_key", required=False)

        if allowlist is None:
            allowlist = self.decode_input(
                "allowlist",
                required=False,
                default=[],
                allow_none=False,
                decode_from_base64=False,
            )

        if denylist is None:
            denylist = self.decode_input(
                "denylist",
                required=False,
                default=[],
                allow_none=False,
                decode_from_base64=False,
            )

        if ordered_records_merge is None:
            ordered_records_merge = self.get_input("ordered_records_merge", required=False, default=True, is_bool=True)

        self.logged_statement(
            "Merging records",
            labeled_json_data={
                "records": records,
                "record_files": record_files,
                "record_directories": record_directories,
                "record_categories": record_categories,
                "allowlist": allowlist,
                "denylist": denylist,
                "nest_records_under_key": nest_records_under_key,
                "ordered_records_merge": ordered_records_merge,
            },
            verbose=True,
            verbosity=2,
        )

        source_maps = []
        if not utils.is_nothing(records):
            self.logger.info("Merging raw records")
            source_maps.append(records)

        for category_name, category_config in record_categories.items():
            self.logger.info(f"Merging category {category_name}")

            records_path = category_config.get("records_path")
            pattern = category_config.get("pattern", "*.json")

            if utils.is_nothing(records_path):
                raise RuntimeError(
                    f"Cannot merge records - Category {category_name} is missing a records path: {category_config}"
                )

            category_merge = self.deepmerge(
                source_directories={
                    records_path: pattern,
                },
                ordered=ordered_records_merge,
                exit_on_completion=False,
            )

            if utils.is_nothing(category_merge):
                self.logger.warning(f"Merge of category {category_name} returned nothing")
                continue

            source_maps.append(
                {
                    category_name: category_merge,
                }
            )

        self.logger.info("Merging records")
        merged_records = self.deepmerge(
            source_maps=source_maps,
            source_files=record_files,
            source_directories=record_directories,
            nest_data_under_key=nest_records_under_key,
            ordered=ordered_records_merge,
            allowlist=allowlist,
            denylist=denylist,
            exit_on_completion=False,
        )

        self.log_results(merged_records, "merged records")

        return self.exit_run(
            merged_records,
            key="records",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def merge_sources(
        self,
        source_directories: Optional[dict[str, str]] = None,
        source_files: Optional[list[FilePath]] = None,
        source_maps: Optional[Any] = None,
        source_data: Optional[list[str]] = None,
        override_data: Optional[Any] = None,
        state_path: Optional[str] = None,
        state_paths: Optional[dict[str, str]] = None,
        state_key: Optional[str] = None,
        ordered_state_merge: Optional[bool] = None,
        nest_state_under_key: Optional[str] = None,
        merge_record: Optional[FilePath] = None,
        merge_records: Optional[list[FilePath]] = None,
        record_directories: Optional[dict[FilePath, str]] = None,
        extra_record_categories: Optional[dict[str, dict[str, str]]] = None,
        nest_records_under_key: Optional[str] = None,
        ordered_records_merge: Optional[bool] = None,
        config_dir: Optional[str] = None,
        config_dirs: Optional[list[str]] = None,
        ordered_config_merge: Optional[bool] = None,
        nest_config_under_key: Optional[str] = None,
        ordered_sources_merge: Optional[bool] = None,
        nest_sources_under_key: Optional[str] = None,
        parent_records: Optional[list[FilePath]] = None,
        ordered_parent_records_merge: Optional[bool] = None,
        parent_config_dirs: Optional[list[FilePath]] = None,
        ordered_parent_config_dirs_merge: Optional[bool] = None,
        ordered_parent_sources_merge: Optional[bool] = None,
        ordered: Optional[bool] = None,
        allowlist: Optional[list[str]] = None,
        denylist: Optional[list[str]] = None,
        passthrough_data_channel: Optional[Any] = None,
        exit_on_completion: bool = True,
    ):
        """Merges sources of data

        generator=key: data, module_class: utils

        name: source_directories, required: false, default: {}, json_encode: true, base64_encode: true
        name: source_files, required: false, default: [], json_encode: true
        name: source_maps, required: false, default: [], json_encode: true, base64_encode: true
        name: source_data, required: false, default: [], json_encode: true, base64_encode: true
        name: override_data, required: false, default: {}, json_encode: true, base64_encode: true
        name: state_path, required: true, type: string
        name: state_paths, required: false, default: {}, json_encode: true, base64_encode: true
        name: state_key, required: false, default: context
        name: ordered_state_merge, required: false, default: true
        name: nest_state_under_key, required: false, type: string
        name: merge_record, required: false, type: string
        name: merge_records, required: false, default: [], json_encode: true
        name: record_directories, required: false, default: {}, json_encode: true, base64_encode: true
        name: extra_record_categories, required: false, default: {}, json_encode: true, base64_encode: true
        name: ordered_records_merge, required: false, default: true
        name: nest_records_under_key, required: false, type: string
        name: config_dir, required: false, type: string
        name: config_dirs, required: false, default: [], json_encode: true
        name: ordered_config_merge, required: false, default: true
        name: nest_config_under_key, required: false, type: string
        name: ordered_sources_merge, required: false, default: true
        name: nest_sources_under_key, required: false, type: string
        name: parent_records, required: false, default: [], json_encode: true
        name: ordered_parent_records_merge, required: false, default: true
        name: parent_config_dirs, required: false, default: [], json_encode: true
        name: ordered_parent_config_dirs_merge, required: false, default: true
        name: ordered_parent_sources_merge, required: false, default: true
        name: ordered, required: false
        name: allowlist, required: false, default: [], json_encode: true
        name: denylist, required: false, default: [], json_encode: true
        name: passthrough_data_channel, required: false, json_encode: true, base64_encode: true
        """
        if source_directories is None:
            source_directories = self.decode_input("source_directories", required=False, default={}, allow_none=False)

        if source_files is None:
            source_files = self.decode_input(
                "source_files",
                required=False,
                default=[],
                decode_from_base64=False,
                allow_none=False,
            )

        if source_maps is None:
            source_maps = self.decode_input("source_maps", required=False, default=[], allow_none=False)

        if source_data is None:
            source_data = self.decode_input("source_data", required=False, default=[], allow_none=False)

        if override_data is None:
            override_data = self.decode_input("override_data", required=False, default={}, allow_none=False)

        if state_path is None:
            state_path = self.get_input("state_path", required=False)

        if state_paths is None:
            state_paths = self.decode_input("state_paths", required=False, default={}, allow_none=False)

        if state_key is None:
            state_key = self.get_input("state_key", required=False, default="context")

        if nest_state_under_key is None:
            nest_state_under_key = self.get_input("nest_state_under_key", required=False)

        if ordered_state_merge is None:
            ordered_state_merge = self.get_input("ordered_state_merge", required=False, default=True, is_bool=True)

        if merge_record is None:
            merge_record = self.get_input("merge_record", required=False)

        if merge_records is None:
            merge_records = self.decode_input(
                "merge_records",
                required=False,
                default=[],
                decode_from_base64=False,
                allow_none=False,
            )

        if record_directories is None:
            record_directories = self.decode_input("record_directories", required=False, default={}, allow_none=False)

        if extra_record_categories is None:
            extra_record_categories = self.decode_input(
                "extra_record_categories", required=False, default={}, allow_none=False
            )

        if nest_records_under_key is None:
            nest_records_under_key = self.get_input("nest_records_under_key", required=False)

        if ordered_records_merge is None:
            ordered_records_merge = self.get_input("ordered_records_merge", required=False, default=True, is_bool=True)

        if config_dir is None:
            config_dir = self.get_input("config_dir", required=False)

        if config_dirs is None:
            config_dirs = self.decode_input(
                "config_dirs",
                required=False,
                default=[],
                decode_from_base64=False,
                allow_none=False,
            )

        if ordered_config_merge is None:
            ordered_config_merge = self.get_input("ordered_config_merge", required=False, default=True, is_bool=True)

        if nest_config_under_key is None:
            nest_config_under_key = self.get_input("nest_config_under_key", required=False)

        if nest_sources_under_key is None:
            nest_sources_under_key = self.get_input("nest_sources_under_key", required=False)

        if ordered_sources_merge is None:
            ordered_sources_merge = self.get_input("ordered_sources_merge", required=False, default=True, is_bool=True)

        if parent_records is None:
            parent_records = self.decode_input(
                "parent_records",
                required=False,
                default=[],
                decode_from_base64=False,
                allow_none=False,
            )

        if ordered_parent_records_merge is None:
            ordered_parent_records_merge = self.get_input(
                "ordered_parent_records_merge",
                required=False,
                default=True,
                is_bool=True,
            )

        if parent_config_dirs is None:
            parent_config_dirs = self.decode_input(
                "parent_config_dirs",
                required=False,
                default=[],
                decode_from_base64=False,
                allow_none=False,
            )

        if ordered_parent_config_dirs_merge is None:
            ordered_parent_config_dirs_merge = self.get_input(
                "ordered_parent_config_dirs_merge",
                required=False,
                default=True,
                is_bool=True,
            )

        if ordered_parent_sources_merge is None:
            ordered_parent_sources_merge = self.get_input(
                "ordered_parent_sources_merge",
                required=False,
                default=True,
                is_bool=True,
            )

        if ordered is None:
            ordered = self.get_input("ordered", required=False, is_bool=True)

        if allowlist is None:
            allowlist = self.decode_input(
                "allowlist",
                required=False,
                default=[],
                allow_none=False,
                decode_from_base64=False,
            )

        if denylist is None:
            denylist = self.decode_input(
                "denylist",
                required=False,
                default=[],
                allow_none=False,
                decode_from_base64=False,
            )

        if passthrough_data_channel is None:
            passthrough_data_channel = self.decode_input("passthrough_data_channel", required=False)

        self.logger.info("Merging sources of data")

        allowed_config_files = [".json", ".yaml", ".yml"]

        if ordered is not None:
            self.logger.info(f"Overriding all merge ordering to {ordered}")
            ordered_parent_config_dirs_merge = ordered
            ordered_parent_records_merge = ordered
            ordered_parent_sources_merge = ordered
            ordered_state_merge = ordered
            ordered_config_merge = ordered
            ordered_records_merge = ordered
            ordered_sources_merge = ordered

        if not utils.is_nothing(state_path):
            state_paths[state_path] = state_key

        filtered_state_paths = {}
        for sp, sk in state_paths.items():
            existing_sk = filtered_state_paths.get(sp)
            if existing_sk == sk:
                self.logger.warning(f"Removing duplicate state path {sp} with state key {sk} from data sources")
                continue

            filtered_state_paths[sp] = sk

        state_paths = filtered_state_paths

        if not utils.is_nothing(config_dir):
            config_dirs.insert(0, config_dir)

        filtered_config_dirs = []
        for d in set(config_dirs):
            if d in parent_config_dirs:
                self.logger.warning(f"Removing {d} from config directories, directory is part of the parent data")
                continue

            filtered_config_dirs.append(d)

        config_dirs = filtered_config_dirs

        if not utils.is_nothing(merge_record):
            merge_records.insert(0, merge_record)

        filtered_merge_records = []
        for mr in set(merge_records):
            if mr in parent_records:
                self.logger.warning(f"Removing {mr} from merge records, merge record is part of the parent data")
                continue

            filtered_merge_records.append(mr)

        merge_records = filtered_merge_records

        def filter_tags(t: dict[str, str]):
            filtered = {}

            for k, v in t.items():
                if utils.is_nothing(v):
                    self.logger.warning(f"Rejecting empty tag {k}")
                    continue

                k = k.title()

                if k in filtered:
                    self.logger.warning(f"Rejecting duplicate tag {k}")
                    continue

                if k.startswith("Aws:"):
                    self.logger.warning(f"Rejecting internal AWS tag {k}")
                    continue

                filtered[k] = v

            return filtered

        override_tags = override_data.pop("tags", {})
        if not utils.is_nothing(override_tags):
            override_tags = filter_tags(override_tags)
            self.logged_statement(f"Filtering override data tags", json_data=override_tags)
            override_data["tags"] = override_tags

        self.logged_statement(
            "Data sources",
            labeled_json_data=dict(
                state_paths=state_paths,
                config_dirs=config_dirs,
                merge_records=merge_records,
                parent_records=parent_records,
                parent_config_dirs=parent_config_dirs,
            ),
        )

        self.logger.info("Fetching any state data sources")
        state_data = []
        for sp, sk in state_paths.items():
            sd = self.get_aws_s3_terraform_state_outputs(
                state_key=sk,
                state_path=sp,
                fail_on_not_found=False,
                exit_on_completion=False,
            )
            if utils.is_nothing(sd):
                self.logger.warning(f"State data source {sp} returned nothing")
                continue

            state_data.append(sd)

        if state_data:
            self.logger.info("Merging any state data sources")
            merged_state_data = self.deepmerge(
                source_maps=state_data,
                nest_data_under_key=nest_state_under_key,
                ordered=ordered_state_merge,
                allowlist=allowlist,
                denylist=denylist,
                exit_on_completion=False,
            )

            if utils.is_nothing(merged_state_data):
                self.logger.warning("Merged state data returned nothing")
            else:
                source_maps.append(merged_state_data)
                self.log_results(merged_state_data, "merged state data")

        if config_dirs:
            self.logger.info("Merging config data sources")
            config_data = self.config_file_data(
                config_dirs=config_dirs,
                ordered_config_merge=ordered_config_merge,
                nest_config_under_key=nest_config_under_key,
                allowed_extensions=allowed_config_files,
                exit_on_completion=False,
            )

            if utils.is_nothing(config_data):
                self.logger.warning("Config data returned nothing")
            else:
                source_maps.append(config_data)
                self.log_results(config_data, "config data")

        if (
            not utils.is_nothing(merge_records)
            or not utils.is_nothing(record_directories)
            or not utils.is_nothing(extra_record_categories)
        ):
            self.logger.info("Merging record data sources")
            records_data = self.merge_records_data(
                record_files=merge_records,
                record_directories=record_directories,
                record_categories=extra_record_categories,
                nest_records_under_key=nest_records_under_key,
                ordered_records_merge=ordered_records_merge,
                allowlist=allowlist,
                denylist=denylist,
                exit_on_completion=False,
            )

            if utils.is_nothing(records_data):
                self.logger.warning("Records data returned nothing")
            else:
                source_maps.append(records_data)
                self.log_results(records_data, "records data")

        if not utils.is_nothing(passthrough_data_channel):
            self.logger.info("Passing data channel through to be merged last")
            source_maps.append(passthrough_data_channel)

        self.logger.info("Merging data sources")
        merged_data = self.deepmerge(
            source_directories=source_directories,
            source_files=source_files,
            source_maps=source_maps,
            source_data=source_data,
            override_data=override_data,
            nest_data_under_key=nest_sources_under_key,
            ordered=ordered_sources_merge,
            allowlist=allowlist,
            denylist=denylist,
            exit_on_completion=False,
        )

        self.log_results(merged_data, "merged data")

        if utils.is_nothing(parent_records) and utils.is_nothing(parent_config_dirs):
            self.logger.info("No parent data to merge into, returning data sources")
            return self.exit_run(
                results=merged_data,
                key="data",
                encode_to_base64=True,
                format_json=False,
                exit_on_completion=exit_on_completion,
            )

        parent_source_maps = []

        if not utils.is_nothing(parent_records):
            self.logger.info(f"Parent records: {parent_records}")
            parent_records_data = self.merge_records_data(
                record_files=parent_records,
                ordered_records_merge=ordered_parent_records_merge,
                exit_on_completion=False,
            )

            if utils.is_nothing(parent_records_data):
                self.logger.warning("Parent records data returned nothing")
            else:
                parent_source_maps.append(parent_records_data)
                self.log_results(parent_records_data, "parent records data")

        if not utils.is_nothing(parent_config_dirs):
            self.logger.info(f"Parent config directories: {parent_config_dirs}")
            parent_config_data = self.config_file_data(
                config_dirs=parent_config_dirs,
                allowed_extensions=allowed_config_files,
                ordered_config_merge=ordered_parent_config_dirs_merge,
                exit_on_completion=False,
            )

            if utils.is_nothing(parent_config_data):
                self.logger.warning("Parent config data returned nothing")
            else:
                parent_source_maps.append(parent_config_data)
                self.log_results(parent_config_data, "parent config data")

        if utils.is_nothing(parent_source_maps):
            self.logger.warning("No parent data returned, returning merged sources data")
            return self.exit_run(
                results=merged_data,
                key="data",
                encode_to_base64=True,
                format_json=False,
                exit_on_completion=exit_on_completion,
            )

        self.logger.info("Merging parent data sources")
        child_and_parent_data = self.deepmerge(
            source_maps=parent_source_maps,
            ordered=ordered_parent_sources_merge,
            override_data=merged_data,
            exit_on_completion=False,
        )

        self.log_results(child_and_parent_data, "merged child and parent data")

        return self.exit_run(
            results=child_and_parent_data,
            key="data",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def deepmerge(
        self,
        source_directories: Optional[dict[str, str]] = None,
        source_files: Optional[list[FilePath]] = None,
        source_maps: Optional[Any] = None,
        source_data: Optional[list[str]] = None,
        override_data: Optional[Any] = None,
        ordered: Optional[bool] = None,
        nest_data_under_key: Optional[str] = None,
        allowlist: Optional[list[str]] = None,
        denylist: Optional[list[str]] = None,
        exit_on_completion: bool = True,
    ):
        """Deeply merges source data

        generator=key: merged_maps, module_class: utils, no_class_in_module_name: true

        name: source_directories, required: false, default: {}, json_encode: true, base64_encode: true
        name: source_files, required: false, default: [], json_encode: true
        name: source_maps, required: false, default: [], json_encode: true, base64_encode: true
        name: source_data, required: false, default: [], json_encode: true, base64_encode: true
        name: override_data, required: false, default: {}, json_encode: true, base64_encode: true
        name: ordered, required: false, default: false
        name: nest_data_under_key, required: false
        name: allowlist, required: false, default: [], json_encode: true
        name: denylist, required: false, default: [], json_encode: true"""

        if source_directories is None:
            source_directories = self.decode_input("source_directories", required=False, default={}, allow_none=False)

        if source_files is None:
            source_files = self.decode_input(
                "source_files",
                required=False,
                default=[],
                decode_from_base64=False,
                allow_none=False,
            )

        if source_maps is None:
            source_maps = self.decode_input("source_maps", required=False, default=[], allow_none=False)

        if source_data is None:
            source_data = self.decode_input("source_data", required=False, default=[], allow_none=False)

        if override_data is None:
            override_data = self.decode_input("override_data", required=False, default={}, allow_none=False)

        if ordered is None:
            ordered = self.get_input("ordered", required=False, default=False, is_bool=True)

        if nest_data_under_key is None:
            nest_data_under_key = self.get_input("nest_data_under_key", required=False)

        if allowlist is None:
            allowlist = self.decode_input(
                "allowlist",
                required=False,
                default=[],
                decode_from_base64=False,
                allow_none=False,
            )

        if denylist is None:
            denylist = self.decode_input(
                "denylist",
                required=False,
                default=[],
                decode_from_base64=False,
                allow_none=False,
            )

        self.logged_statement(
            "Deeply merging source data",
            labeled_json_data={
                "source maps": source_maps,
                "source data": source_data,
                "source directories": source_directories,
                "source files": source_files,
                "overrides": override_data,
                "ordered": ordered,
                "nest data under key": nest_data_under_key,
            },
            verbose=True,
            verbosity=2,
        )

        raw_data = []
        if isinstance(source_maps, Mapping):
            source_maps = [source_maps]

        def add_source_maps_to_raw_data(m):
            try:
                for source_map in m:
                    if utils.is_nothing(source_map):
                        self.logger.warning("Skipping empty source map")
                        continue

                    if isinstance(source_map, Mapping):
                        raw_data.append(source_map)
                        continue

                    add_source_maps_to_raw_data(source_map)
            except TypeError as exc:
                raise RuntimeError(f"Malformed source map cannot be merged: {source_map}") from exc

        add_source_maps_to_raw_data(source_maps)

        for data in source_data:
            self.logger.info("Decoding raw data")
            parsed_data = self.decode_file(file_data=data)
            if not utils.is_nothing(parsed_data):
                raw_data.append(parsed_data)

        for file_path in utils.all_non_empty(*list(set(source_files))):
            self.logger.info(f"Merging source file data from {file_path}")
            file_data = self.get_file(file_path=file_path, decode=True)
            raw_data.append(file_data)

        for files_path, files_pattern in source_directories.items():
            found_config = self.config_file_data(
                config_dir=files_path,
                config_glob=files_pattern,
                ordered_config_merge=ordered,
                exit_on_completion=False,
            )

            if not utils.is_nothing(found_config):
                self.log_results(found_config, "found config")
                raw_data.extend(utils.all_values_from_map(found_config))

        self.logger.info(f"Found {len(raw_data)} datums to merge")
        merged_data = {}

        for datum in raw_data:
            if ordered:
                self.logged_statement(
                    "Ordered merge of datum into merge data",
                    labeled_json_data={"merged_data": merged_data, "datum": datum},
                    verbose=True,
                    verbosity=2,
                )

                merged_data |= datum
            else:
                self.logged_statement(
                    "Unordered merge of datum into merge data",
                    labeled_json_data={"merged_data": merged_data, "datum": datum},
                    verbose=True,
                    verbosity=2,
                )

                merged_data = self.merger.merge(merged_data, datum)
                self.log_results(merged_data, "merged data")

        self.log_results(merged_data, "merged data")

        if not utils.is_nothing(override_data):
            self.logged_statement(
                "Merging override data",
                labeled_json_data={"overrides": override_data},
                verbose=True,
                verbosity=2,
            )
            merged_data |= override_data

            self.log_results(merged_data, "overridden merge data")

        filtered_data, rejected_data = self.filter_map(m=merged_data, allowlist=allowlist, denylist=denylist)
        self.log_results(filtered_data, "filtered data")
        self.log_results(rejected_data, "rejected data")

        filtered_data = utils.deduplicate_map(filtered_data)

        if not utils.is_nothing(nest_data_under_key):
            self.logger.info(f"Nesting data under key {nest_data_under_key}")
            filtered_data = {nest_data_under_key: filtered_data}

        return self.exit_run(
            results=filtered_data,
            key="merged_maps",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def flatmap(
        self,
        source_map: Optional[dict] = None,
        delimiter: Optional[str] = None,
        use_parent_in_child_keys: Optional[bool] = None,
        use_all_ancestors_in_child_keys: Optional[bool] = None,
        exit_on_completion: bool = True,
    ):
        """Recursively flattens a nested map structure using dataclasses

        generator=key: flattened_map, module_class: utils, no_class_in_module_name: true

        name: source_map, required: true, json_encode: true, base64_encode: true
        name: delimiter, required: false, default: "_"
        name: use_parent_in_child_keys, required: false, default: false
        name: use_all_ancestors_in_child_keys, required: false, default: false
        """

        if source_map is None:
            source_map = self.decode_input("source_map", required=True, allow_none=False)

        if delimiter is None:
            delimiter = self.get_input("delimiter", required=False, default="_")

        if use_parent_in_child_keys is None:
            use_parent_in_child_keys = self.get_input(
                "use_parent_in_child_keys", required=False, default=False, is_bool=True
            )

        if use_all_ancestors_in_child_keys is None:
            use_all_ancestors_in_child_keys = self.get_input(
                "use_all_ancestors_in_child_keys", required=False, default=False, is_bool=True
            )

        self.logged_statement(
            "Flattening nested map structure using dataclasses",
            labeled_json_data={
                "source_map_keys": list(source_map.keys()) if source_map else [],
                "delimiter": delimiter,
                "use_parent_in_child_keys": use_parent_in_child_keys,
                "use_all_ancestors_in_child_keys": use_all_ancestors_in_child_keys,
            },
            verbose=True,
            verbosity=2,
        )

        # Create the flattened container using dataclasses
        container = FlatMapContainer(
            source_map=source_map,
            delimiter=delimiter,
            use_parent_in_child_keys=use_parent_in_child_keys,
            use_all_ancestors_in_child_keys=use_all_ancestors_in_child_keys,
        )

        # Get the clean flattened data (no metadata pollution)
        flattened_map = container.flattened_data

        self.logger.info(f"Successfully flattened {len(source_map)} root items into {len(flattened_map)} total items")
        self.logger.info(f"Maximum nesting depth: {container.max_depth}")
        self.logger.info(f"Root entries: {len(container.root_entries)}, Child entries: {len(container.child_entries)}")

        # Log depth breakdown
        depth_breakdown = {depth: len(container.entries_at_depth(depth)) for depth in range(container.max_depth + 1)}
        self.logger.info(f"Entries by depth: {depth_breakdown}")

        self.log_results(flattened_map, "flattened map")

        return self.exit_run(
            results=flattened_map,
            key="flattened_map",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def export_env_vars(
        self,
        env_vars: Optional[dict] = None,
        prefix: Optional[str] = None,
        key_transform: Optional[str] = None,
        output_format: Optional[str] = None,
        write_to_file: Optional[bool] = None,
        exit_on_completion: bool = True,
    ):
        """Export environment variables in CI-friendly format using GitHub Actions heredoc syntax

        generator=key: exported, module_class: utils, no_class_in_module_name: true

        name: env_vars, required: false, json_encode: true, base64_encode: true
        name: prefix, required: false, default: ""
        name: key_transform, required: false
        name: output_format, required: false, default: "github_env"
        name: write_to_file, required: false, default: true
        """
        # This method handles multi-line values (certificates, private keys, etc.) safely
        # by using GitHub Actions' heredoc format. It can automatically detect CI environments
        # and write directly to GITHUB_ENV when available.
        #
        # When piping JSON from stdin, you can either:
        # - Pipe the env vars directly: echo '{"KEY": "value"}' | tm_cli export_env_vars
        # - Or wrap in env_vars key: echo '{"env_vars": {"KEY": "value"}}' | tm_cli export_env_vars
        if env_vars is None:
            # Try to get env_vars from the explicit key first
            env_vars = self.decode_input("env_vars", required=False, allow_none=True)

            # If env_vars key wasn't provided, check if stdin had direct JSON dict
            # (i.e., the user piped {"KEY": "value"} instead of {"env_vars": {"KEY": "value"}})
            if env_vars is None and self.from_stdin and self._stdin_data:
                # Check if stdin data has the env_vars key, otherwise use the whole stdin data
                if "env_vars" in self._stdin_data:
                    env_vars = self._stdin_data["env_vars"]
                else:
                    # Use entire stdin data as env vars (direct piping mode)
                    env_vars = self._stdin_data

            if not env_vars:
                raise RuntimeError("env_vars is required: pipe JSON directly or use {'env_vars': {...}}")

        if prefix is None:
            prefix = self.get_input("prefix", required=False, default="")

        if key_transform is None:
            key_transform = self.get_input("key_transform", required=False)

        if output_format is None:
            output_format = self.get_input("output_format", required=False, default="github_env")

        if write_to_file is None:
            write_to_file = self.get_input("write_to_file", required=False, default=True, is_bool=True)

        self.logged_statement(
            "Exporting environment variables",
            labeled_json_data={
                "env_vars_keys": list(env_vars.keys()) if env_vars else [],
                "prefix": prefix,
                "key_transform": key_transform,
                "output_format": output_format,
                "write_to_file": write_to_file,
            },
            verbose=True,
            verbosity=2,
        )

        # Format the environment variables
        formatted_output = utils.format_github_env_entries(
            data=env_vars,
            prefix=prefix,
            key_transform=key_transform,
        )

        result = {
            "formatted": formatted_output,
            "count": len(env_vars),
            "keys": [f"{prefix}{k}" if prefix else k for k in env_vars.keys()],
        }

        # Write to GITHUB_ENV if requested and available
        written_to_file = False
        if write_to_file:
            github_env = os.getenv("GITHUB_ENV")
            if github_env:
                self.logger.info(f"Writing {len(env_vars)} environment variables to GITHUB_ENV")
                written_to_file = utils.write_to_github_env(
                    data=env_vars,
                    prefix=prefix,
                    key_transform=key_transform,
                    env_file=github_env,
                )
                result["written_to_github_env"] = written_to_file
            else:
                self.logger.warning("GITHUB_ENV not available, outputting formatted content only")
                result["written_to_github_env"] = False

        # For non-CI or when direct output is needed, print to stdout
        if output_format == "github_env" and not written_to_file:
            # Output formatted heredoc syntax directly
            print(formatted_output)
            return self.exit_run(
                results=result,
                key="exported",
                exit_on_completion=exit_on_completion,
            )

        return self.exit_run(
            results=result,
            key="exported",
            exit_on_completion=exit_on_completion,
        )

    def get_latest_terragrunt_version(
        self,
        exit_on_completion: bool = True,
    ):
        """Gets the latest Terragrunt version

        generator=key: version, plaintext_output: true, module_class: terragrunt
        """
        github_client = self.get_github_client(
            github_owner="gruntwork-io",
            github_repo="terragrunt",
        )

        latest_release = github_client.repo.get_latest_release()

        return self.exit_run(
            results=latest_release.title,
            format_results=False,
            key="version",
            exit_on_completion=exit_on_completion,
        )

    def build_github_actions_workflow(
        self,
        workflow_name: Optional[str] = None,
        concurrency_group: Optional[str] = None,
        environment_variables: Optional[dict[str, str]] = None,
        secrets: Optional[dict[str, str]] = None,
        use_oidc_auth: Optional[bool] = None,
        events: Optional[dict[str, Any]] = None,
        triggers: Optional[dict[str, Any]] = None,
        inputs: Optional[dict[str, Any]] = None,
        pull_requests: Optional[dict[str, Any]] = None,
        jobs: Optional[dict[str, Any]] = None,
        exit_on_completion: bool = True,
    ):
        """Builds a Github Actions workflow

        generator=key: workflow, plaintext_output: true, module_class: github

        name: workflow_name, required: true, type: string
        name: concurrency_group, required: false, type: string
        name: environment_variables, required: false, default: {}, json_encode: true, base64_encode: true
        name: secrets, required: false, default: {}, json_encode: true, base64_encode: true
        name: use_oidc_auth, required: false, default: false
        name: events, required: false, default: {}, json_encode: true, base64_encode: true
        name: triggers, required: false, default: {}, json_encode: true, base64_encode: true
        name: inputs, required: false, default: {}, json_encode: true, base64_encode: true
        name: pull_requests, required: false, default: {}, json_encode: true, base64_encode: true
        name: jobs, required: true, json_encode: true, base64_encode: true
        """
        if workflow_name is None:
            workflow_name = self.get_input("workflow_name", required=True)

        if concurrency_group is None:
            concurrency_group = self.get_input("concurrency_group", required=False)

        if environment_variables is None:
            environment_variables = self.decode_input(
                "environment_variables", required=False, default={}, allow_none=False
            )

        if secrets is None:
            secrets = self.decode_input("secrets", required=False, default={}, allow_none=False)

        if use_oidc_auth is None:
            use_oidc_auth = self.get_input("use_oidc_auth", required=False, default=True, is_bool=True)

        if events is None:
            events = self.decode_input("events", required=False, default={}, allow_none=False)

        if triggers is None:
            triggers = self.decode_input("triggers", required=False, default={}, allow_none=False)

        if inputs is None:
            inputs = self.decode_input("inputs", required=False, default={}, allow_none=False)

        if pull_requests is None:
            pull_requests = self.decode_input("pull_requests", required=False, default={}, allow_none=False)

        if jobs is None:
            jobs = self.decode_input("jobs", required=True)

        self.logger.info(f"Generating a Github Actions workflow {workflow_name}")

        workflow = {
            "name": workflow_name,
        }

        if not utils.is_nothing(concurrency_group):
            workflow["concurrency"] = concurrency_group

        workflow_env = {
            "COMMIT_SHA": "${{ github.event_name == 'pull_request' && github.event.pull_request.head.sha || github.sha }}",
            "BRANCH": "${{ github.event_name == 'pull_request' && format('refs/heads/{0}', github.event.pull_request.head.ref) || github.ref }}",
        }

        for k, v in environment_variables.items():
            workflow_env[k] = v

        for k, v in secrets.items():
            workflow_env[k] = "${{ secrets." + v + " }}"

        workflow["env"] = workflow_env

        permissions = {
            "contents": "write",
            "pull-requests": "write",
        }

        if use_oidc_auth:
            permissions["id-token"] = "write"

        push_triggers = {}

        for trigger_key in ["paths", "branches", "tags"]:
            trigger_config = utils.all_non_empty(*triggers.get(trigger_key, []))
            if utils.is_nothing(trigger_config):
                self.logged_statement(f"No {trigger_key} triggers")
                continue

            push_triggers[trigger_key] = trigger_config

        self.logged_statement("Push triggers", json_data=push_triggers)

        workflow_inputs = {}
        found_required_input = False
        if inputs:
            self.logger.info("Terraform workflow has inputs, checking if any are required")
            for default_input_key, input_config in inputs.items():
                input_key = input_config.pop("key", default_input_key)

                if utils.is_nothing(input_key):
                    input_key = default_input_key

                workflow_inputs[input_key] = input_config
                input_required = utils.strtobool(input_config.get("required", False))
                input_default = input_config.get("default")

                workflow_inputs[input_key]["required"] = input_required
                if input_default is not None and input_config.get("type") == "boolean":
                    input_default = utils.strtobool(input_default)
                    workflow_inputs[input_key]["default"] = input_default

                if input_required:
                    if found_required_input:
                        continue

                    found_required_input = True
                    self.logger.warning(f"Input {input_key} is required, disabling any automatic triggers")
                    events["push"] = False
                    events["pull_request"] = False
                    events["release"] = False
                    events["schedule"] = []

        workflow_events = {}
        if events.get("push", True):
            self.logged_statement("Triggering on push")
            workflow_events["push"] = deepcopy(push_triggers)

        if events.get("pull_request", True):
            self.logged_statement("Triggering on pull request")
            workflow_events["pull_request"] = {}

            for ignore_key in ["branches", "paths", "tags"]:
                ignored = pull_requests.get(f"ignored_{ignore_key}", [])
                if utils.is_nothing(ignored) and ignore_key in push_triggers:
                    self.logged_statement(f"Grabbing {ignore_key} triggers for pull requests from push triggers")
                    workflow_events["pull_request"][ignore_key] = push_triggers[ignore_key]
                else:
                    self.logged_statement(f"Ignoring {ignore_key} {ignored} on pull request")
                    workflow_events["pull_request"][f"{ignore_key}-ignore"] = ignored

            if pull_requests.get("merge_queue", False):
                self.logged_statement("Supporting merge queues for pull requests")
                workflow_events["pull_request"]["merge_group"] = {}

        if events.get("release", False):
            self.logged_statement("Triggering on release")
            workflow_events["release"] = {
                "types": [
                    "published",
                ]
            }

        if events.get("call", True):
            self.logged_statement("Triggering on call")
            workflow_events["workflow_call"] = {}
            if inputs:
                workflow_events["workflow_call"]["inputs"] = workflow_inputs

        if events.get("dispatch", True):
            self.logged_statement("Triggering on dispatch")
            workflow_events["workflow_dispatch"] = {}
            if inputs:
                workflow_events["workflow_dispatch"]["inputs"] = workflow_inputs

        schedules = events.get("schedule", [])
        if not utils.is_nothing(schedules):
            workflow_events["schedule"] = []
            for schedule in schedules:
                self.logged_statement(f"Scheduling workflow to run on: {schedule}")
                workflow_events["schedule"].append({"cron": schedule})

        self.log_results(workflow_events, "workflow events")

        if utils.is_nothing(workflow_events) or utils.is_nothing(jobs):
            self.logger.warning("Either there are no events, no jobs, or both, returning nothing")
            return self.exit_run(
                results="",
                format_results=False,
                key="workflow",
                exit_on_completion=exit_on_completion,
            )

        workflow["on"] = workflow_events

        if not utils.is_nothing(permissions):
            workflow["permissions"] = permissions

        workflow["jobs"] = jobs

        self.logged_statement("Workflow YAML", json_data=workflow)

        workflow_stream = StringIO()

        def str_representer(dumper, data):
            data = data.replace("${{ ", "${{").replace(" }}", "}}")
            if len(data.splitlines()) > 1 or "||" in data or "&&" in data:
                return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
            return dumper.represent_scalar("tag:yaml.org,2002:str", data)

        try:
            with YAML(output=workflow_stream) as yaml:
                yaml.default_flow_style = False
                yaml.indent(sequence=4, offset=2)
                yaml.representer.add_representer(str, str_representer)
                yaml.representer.ignore_aliases = lambda x: True
                yaml.dump(workflow)
        except YAMLError as exc:
            raise RuntimeError(f"Failed to dump workflow to YAML") from exc

        workflow_yaml = workflow_stream.getvalue()
        workflow_stream.close()

        self.logged_statement(f"Workflow YAML file:\n\n{workflow_yaml}")

        return self.exit_run(
            results=workflow_yaml,
            format_results=False,
            key="workflow",
            exit_on_completion=exit_on_completion,
        )

    def list_sendgrid_authenticated_domains(
        self, project: Optional[str] = None, exit_on_completion: Optional[bool] = True
    ):
        """List authenticated Sendgrid domains for a project

        generator=key: domains, module_class: sendgrid

        name: project, required: true, type: string"""
        if project is None:
            project = self.get_input("project", required=True)

        sendgrid_api_key = self.SENDGRID_API_KEY.get(project)
        if utils.is_nothing(sendgrid_api_key):
            raise RuntimeError(f"No Sendgrid API key in Vault for project {project}")

        sendgrid_api_client = SendGridAPIClient(sendgrid_api_key)

        response = sendgrid_api_client.client.whitelabel.domains.get()

        domains = {}

        if utils.is_nothing(response.body):
            raise RuntimeError(f"Sendgrid failed to return a body, status code: {response.status_code}")

        try:
            raw_domains = json.loads(response.body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Failed to decode response from Sendgrid: {response.body}") from exc

        for domain in raw_domains:
            domain_id = domain.get("id")
            if utils.is_nothing(domain_id):
                raise RuntimeError(f"Domain has no ID: {domain}")

            domains[domain_id] = domain

        return self.exit_run(
            domains,
            key="domains",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def get_github_users(self, prefix: Optional[bool] = None, exit_on_completion: bool = True):
        """Gets Github users for the organization

        generator=key: users, module_class: github

        name: prefix, required: false, default: false
        """

        if prefix is None:
            prefix = self.get_input("prefix", required=False, default=False, is_bool=True)

        self.logger.info("Getting Github users")

        github_users = {}
        github_users_by_email = {}
        named_user_objects = {}
        github_client = self.get_github_client()

        # Fetch verified domain emails for the organization
        def make_verified_domain_emails_query(after_cursor=None):
            return """
            query {
              organization(login: "ORG") {
                membersWithRole (first: 100, after: AFTER){
                  pageInfo {
                    hasNextPage
                    endCursor
                  }
                  edges {
                      node {
                        login
                        organizationVerifiedDomainEmails(login: "ORG")
                      }
                    }
                }
              }
            }
            """.replace(
                "ORG", github_client.GITHUB_OWNER
            ).replace(
                "AFTER", '"{}"'.format(after_cursor) if after_cursor else "null"
            )

        def fetch_organization_verified_domain_emails():
            vde = {}

            has_next_page = True
            after_cursor = None

            while has_next_page:
                data = github_client.graphql_client.execute(
                    query=make_verified_domain_emails_query(after_cursor),
                    headers={"Authorization": f"Bearer {github_client.GITHUB_TOKEN}"},
                )
                for member in data["data"]["organization"]["membersWithRole"]["edges"]:
                    node = member["node"]
                    login = node["login"]
                    emails = node["organizationVerifiedDomainEmails"]
                    if utils.is_nothing(login) or len(emails) != 1:
                        self.logger.warning(
                            f"Graphql API returned member with unexpected domain verification data: {member}"
                        )
                        continue

                    vde[login] = emails[0]

                has_next_page = data["data"]["organization"]["membersWithRole"]["pageInfo"]["hasNextPage"]
                after_cursor = data["data"]["organization"]["membersWithRole"]["pageInfo"]["endCursor"]

            return vde

        verified_domain_emails = fetch_organization_verified_domain_emails()

        def get_member_data(member):
            ud = member.raw_data
            ud["role"] = member.get_organization_membership(github_client.GITHUB_OWNER).role
            ud["full_name"] = member.name

            pe = ud.get("primary_email")
            if utils.is_nothing(pe):
                pe = verified_domain_emails.get(member.login)
                ud["primary_email"] = pe

            return member, ud

        members = list(github_client.org.get_members())
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_member = {executor.submit(get_member_data, member): member for member in members}
            for future in concurrent.futures.as_completed(future_to_member):
                member, user_data = future.result()
                member_login = member.login
                github_users[member_login] = user_data

                named_user_objects[member_login] = member

                primary_email = user_data.get("primary_email")
                if primary_email:
                    self.logger.info(f"Found a Github user {member_login} with a primary email {primary_email}")
                    github_users_by_email[primary_email] = user_data
                    named_user_objects[primary_email] = member

        return self.exit_run(
            github_users,
            key="users",
            encode_to_base64=True,
            format_json=False,
            prefix="github" if prefix else None,
            prefix_denylist=[
                "name",
                "full_name",
                "primary_email",
            ],
            exit_on_completion=exit_on_completion,
        )

    def get_github_repositories(self, exit_on_completion: bool = True):
        """Gets Github repositories for the organization

        generator=key: repositories, module_class: github
        """
        self.logger.info("Getting Github repositories")

        github_repos = {}
        github_client = self.get_github_client()

        def get_repository_branches(r: GithubRepo):
            branches = {}

            for branch in r.get_branches():
                branches[branch.name] = branch.raw_data

            return {
                r.name: dict(
                    branches=branches,
                )
            }

        tic = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []

            for repo in github_client.org.get_repos():
                repo_name = repo.name
                self.logger.info(f"Getting repository {repo_name}")
                github_repos[repo.name] = repo.raw_data
                futures.append(executor.submit(get_repository_branches, repo))

            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if not utils.is_nothing(result):
                        self.logger.info(f"Successfully read branches for a repository")
                        github_repos = self.merger.merge(github_repos, result)
                    else:
                        raise RuntimeError("Failed to get at least repository's branches")
                except Exception as exc:
                    executor.shutdown(wait=False, cancel_futures=True)
                    raise RuntimeError(f"Failed to get repositories") from exc

        toc = time.perf_counter()
        self.logger.info(f"Getting repositories took {toc - tic:0.2f} seconds to run")

        return self.exit_run(
            github_repos,
            key="repositories",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def get_github_teams(self, exit_on_completion: bool = True):
        """Gets Github teams for the organization

        generator=key: teams, module_class: github
        """
        self.logger.info("Getting Github teams")

        github_teams = {}
        github_client = self.get_github_client()

        def get_team_members(t: GithubTeam):
            members = []

            for member in t.get_members():
                members.append(member.login)

            return {
                t.name: dict(
                    members=members,
                )
            }

        def get_team_permissions(t: GithubTeam):
            permissions = {}

            for repo in t.get_repos():
                permissions[repo.name] = [
                    perm_name for perm_name, perm_allowed in repo.permissions.raw_data.items() if perm_allowed
                ]

            return {
                t.name: dict(
                    permissions=permissions,
                )
            }

        tic = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []

            for team in github_client.org.get_teams():
                github_teams[team.name] = team.raw_data
                github_teams[team.name]["github_team_name"] = team.name
                futures.append(executor.submit(get_team_members, team))
                futures.append(executor.submit(get_team_permissions, team))

            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if not utils.is_nothing(result):
                        self.logger.info(f"Successfully read permissions or membership for a team")
                        github_teams = self.merger.merge(github_teams, result)
                    else:
                        raise RuntimeError("Failed to get at least one team's permissions or membership")
                except Exception as exc:
                    executor.shutdown(wait=False, cancel_futures=True)
                    raise RuntimeError(f"Failed to get team permissions or membership") from exc

        toc = time.perf_counter()
        self.logger.info(f"Getting team permissions and membership took {toc - tic:0.2f} seconds to run")

        self.log_results(github_teams, "github teams")

        return self.exit_run(
            github_teams,
            key="teams",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def get_s3_buckets_containing_name(
        self,
        name_tag: Optional[str] = None,
        execution_role_arn: Optional[str] = None,
        role_session_name: Optional[str] = None,
        exit_on_completion: bool = True,
    ):
        """Tags all S3 buckets in an AWS account containing a name tag

        generator=key: buckets, module_class: aws

        name: name_tag, required: false, default: s3-bucket-name
        name: execution_role_arn, required: false, type: string
        name: role_session_name, required: false, type: string
        """
        if name_tag is None:
            name_tag = self.get_input("name_tag", required=True)

        if execution_role_arn is None:
            execution_role_arn = self.get_input("execution_role_arn", required=False)

        if role_session_name is None:
            role_session_name = self.get_input("role_session_name", required=False)

        self.logger.info(f"Finding S3 buckets containing {name_tag}")

        s3 = self.get_aws_resource(
            service_name="s3",
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
        )

        buckets = {}

        for s3_bucket in s3.buckets.all():
            s3_bucket_name = s3_bucket.name
            if name_tag in s3_bucket_name:
                self.logger.info(f"{s3_bucket_name} matches {name_tag}")
                buckets[s3_bucket_name] = self.get_s3_bucket_features(
                    bucket_name=s3_bucket_name,
                    execution_role_arn=execution_role_arn,
                    role_session_name=role_session_name,
                    bucket=s3_bucket,
                    exit_on_completion=False,
                )
        return self.exit_run(
            buckets,
            key="buckets",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def get_s3_bucket_features(
        self,
        bucket_name: Optional[str] = None,
        execution_role_arn: Optional[str] = None,
        role_session_name: Optional[str] = None,
        bucket: Optional[Any] = None,
        exit_on_completion: bool = True,
    ):
        """Get AWS S3 bucket data

        generator=key: features, module_class: aws

        name: bucket_name, required: true, type: string
        name: execution_role_arn, required: false, type: string
        name: role_session_name, required: false, type: string"""
        if bucket_name is None:
            bucket_name = self.get_input("bucket_name", required=True)

        if execution_role_arn is None:
            execution_role_arn = self.get_input("execution_role_arn", required=False)

        if role_session_name is None:
            role_session_name = self.get_input("role_session_name", required=False)

        self.logger.info(f"Getting bucket data for {bucket_name}")

        s3 = self.get_aws_resource(
            service_name="s3",
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
        )

        if bucket is None:
            bucket = s3.Bucket(bucket_name)

        if not bucket.creation_date:
            return self.exit_run(
                key="features",
                encode_to_base64=True,
                format_json=False,
                exit_on_completion=exit_on_completion,
            )

        bucket_features = {}

        try:
            bucket_logging = bucket.Logging()
            bucket_features["logging"] = bucket_logging.logging_enabled
        except AWSClientError:
            self.logger.warning("No logging configuration for the bucket")
            bucket_features["logging"] = None

        try:
            bucket_versioning = bucket.Versioning()
            bucket_features["versioning"] = bucket_versioning.status
        except AWSClientError:
            self.logger.warning("No versioning configuration for the bucket")
            bucket_features["versioning"] = None

        try:
            bucket_lifecycle_configuration = bucket.LifecycleConfiguration()
            bucket_features["lifecycle_configuration_rules"] = bucket_lifecycle_configuration.rules
        except AWSClientError:
            self.logger.warning("No lifecycle configuration for the bucket")
            bucket_features["lifecycle_configuration_rules"] = None

        try:
            bucket_policy = bucket.Policy()
            bucket_features["policy"] = bucket_policy.policy
        except AWSClientError:
            self.logger.warning("No policy for the bucket")
            bucket_features["policy"] = None

        return self.exit_run(
            bucket_features,
            key="features",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def get_aws_users(
        self,
        unhump_users: Optional[bool] = None,
        sort_by_name: Optional[bool] = None,
        prefix: Optional[bool] = None,
        exit_on_completion: bool = True,
    ):
        """Gets all AWS users for the identity store in the organization

        generator=key: users, module_class: aws

        name: unhump_users, required: false, default: true
        name: sort_by_name, required: false, default: false
        name: prefix, required: false, default: false
        """
        if unhump_users is None:
            unhump_users = self.get_input("unhump_users", required=False, default=True, is_bool=True)

        if sort_by_name is None:
            sort_by_name = self.get_input("sort_by_name", required=False, default=False, is_bool=True)

        if prefix is None:
            prefix = self.get_input("prefix", required=False, default=False, is_bool=True)

        if prefix:
            unhump_users = True

        self.logger.info("Getting AWS users")

        identity_store_id = self.get_identity_store_id()
        identity_store = self.get_aws_client(client_name="identitystore")

        self.logger.info(f"Listing identity store users for {identity_store_id}")

        users = {}
        name_fields = set()

        def get_users(last_token: Optional[str] = None):
            kwargs = utils.get_aws_call_params(IdentityStoreId=identity_store_id, NextToken=last_token)
            results = identity_store.list_users(**kwargs)

            for user in results.get("Users", []):
                user_name_data = user.pop("Name", {})
                name_fields.update(user_name_data.keys())
                user = self.merger.merge(user, user_name_data)

                users[user["UserId"]] = user

            return results.get("NextToken")

        next_token = get_users()

        while not utils.is_nothing(next_token):
            self.logger.info("Still more users to get...")
            next_token = get_users(next_token)

        return self.exit_run(
            results=users,
            key="users",
            encode_to_base64=True,
            format_json=False,
            unhump_results=unhump_users,
            prefix="aws_identitystore" if prefix else None,
            prefix_denylist=list(name_fields),
            sort_by_field="UserName" if sort_by_name else None,
            exit_on_completion=exit_on_completion,
        )

    def get_aws_groups(
        self,
        unhump_groups: Optional[bool] = None,
        sort_by_name: Optional[bool] = None,
        prefix: Optional[bool] = None,
        expand_users: Optional[bool] = None,
        exit_on_completion: bool = True,
    ):
        """Gets all AWS groups for the identity store in the organization

        generator=key: groups, module_class: aws

        name: unhump_groups, required: false, default: true
        name: sort_by_name, required: false, default: false
        name: prefix, required: false, default: false
        name: expand_users, required: false, default: false
        """
        if unhump_groups is None:
            unhump_groups = self.get_input("unhump_groups", required=False, default=True, is_bool=True)

        if sort_by_name is None:
            sort_by_name = self.get_input("sort_by_name", required=False, default=False, is_bool=True)

        if prefix is None:
            prefix = self.get_input("prefix", required=False, default=False, is_bool=True)

        if expand_users is None:
            expand_users = self.get_input("expand_users", required=False, default=False, is_bool=True)

        if prefix:
            unhump_groups = True

        self.logger.info("Getting AWS groups")

        if expand_users:
            self.logger.info("Getting AWS users for expanded membership data")
            aws_users = self.get_aws_users(
                unhump_users=False,
                sort_by_name=False,
                prefix=False,
                exit_on_completion=False,
            )

        identity_store_id = self.get_identity_store_id()
        identity_store = self.get_aws_client(client_name="identitystore")

        self.logger.info(f"Listing identity store groups for {identity_store_id}")

        groups = {}

        def get_groups(last_token: Optional[str] = None):
            kwargs = utils.get_aws_call_params(IdentityStoreId=identity_store_id, NextToken=last_token)
            results = identity_store.list_groups(**kwargs)

            for group in results.get("Groups", []):
                group_id = group["GroupId"]

                if expand_users:
                    group["Members"] = {}
                else:
                    group["Members"] = []

                def get_group_members(last_member_token: Optional[str] = None):
                    member_kwargs = utils.get_aws_call_params(
                        IdentityStoreId=identity_store_id,
                        GroupId=group_id,
                        NextToken=last_member_token,
                    )
                    member_results = identity_store.list_group_memberships(**member_kwargs)

                    for membership in member_results.get("GroupMemberships", []):
                        user_id = membership.get("MemberId", {}).get("UserId")
                        if utils.is_nothing(user_id):
                            raise RuntimeError(
                                f"Invalid returned membership from API for AWS group: {group}\nMembership: {membership}"
                            )

                        if not expand_users:
                            group["Members"].append(user_id)
                            continue

                        user_data = aws_users.get(user_id)
                        if utils.is_nothing(user_data):
                            raise RuntimeError(
                                f"Invalid returned user ID {user_id} from API in members for AWS group: {group}\nUser does not exist in AWS users or is null: {list(aws_users.keys())}"
                            )

                        if not sort_by_name:
                            group["Members"][user_id] = user_data
                            continue

                        user_name = user_data.get("UserName")
                        if utils.is_nothing(user_name):
                            raise RuntimeError(
                                f"User {user_id} has no user name and cannot be sorted by name for group membership: {user_data}"
                            )

                        group["Members"][user_name] = user_data

                    return member_results.get("NextToken")

                member_next_token = get_group_members()

                while not utils.is_nothing(member_next_token):
                    self.logger.info("Still more group members to get...")
                    member_next_token = get_group_members(member_next_token)

                groups[group_id] = group

            return results.get("NextToken")

        next_token = get_groups()

        while not utils.is_nothing(next_token):
            self.logger.info("Still more groups to get...")
            next_token = get_groups(next_token)

        return self.exit_run(
            results=groups,
            key="groups",
            encode_to_base64=True,
            format_json=False,
            unhump_results=unhump_groups,
            prefix="aws_identitystore" if prefix else None,
            sort_by_field="DisplayName" if sort_by_name else None,
            exit_on_completion=exit_on_completion,
        )

    def get_aws_sso_permission_sets(
        self,
        unhump_permission_sets: Optional[bool] = None,
        sort_by_name: Optional[bool] = None,
        exit_on_completion: bool = True,
    ):
        """Gets all AWS permission sets

        generator=key: permission_sets, module_class: aws

        name: unhump_permission_sets, required: false, default: false
        name: sort_by_name, required: false, default: false
        """
        if unhump_permission_sets is None:
            unhump_permission_sets = self.get_input(
                "unhump_permission_sets", required=False, default=True, is_bool=True
            )

        if sort_by_name is None:
            sort_by_name = self.get_input("sort_by_name", required=False, default=False, is_bool=True)

        self.logger.info("Getting AWS permission sets")

        identity_store_arn = self.get_identity_store_id(key="InstanceArn")
        sso_admin = self.get_aws_client(client_name="sso-admin")

        permission_sets = {}

        def get_permission_sets(last_token: Optional[str] = None):
            kwargs = utils.get_aws_call_params(InstanceArn=identity_store_arn, NextToken=last_token)
            results = sso_admin.list_permission_sets(**kwargs)
            for permission_set_id in results.get("PermissionSets", []):
                permission_set_data = sso_admin.describe_permission_set(
                    InstanceArn=identity_store_arn, PermissionSetArn=permission_set_id
                )["PermissionSet"]

                # Get inline policy
                inline_policy = sso_admin.get_inline_policy_for_permission_set(
                    InstanceArn=identity_store_arn, PermissionSetArn=permission_set_id
                )["InlinePolicy"]

                if not utils.is_nothing(inline_policy):
                    permission_set_data["InlinePolicy"] = inline_policy

                # Get managed policies
                managed_policies = []
                managed_policies_token = None

                # Use similar pattern as the outer pagination logic
                managed_policies_kwargs = {"InstanceArn": identity_store_arn, "PermissionSetArn": permission_set_id}

                managed_policies_response = sso_admin.list_managed_policies_in_permission_set(**managed_policies_kwargs)
                managed_policies.extend(managed_policies_response.get("AttachedManagedPolicies", []))
                managed_policies_token = managed_policies_response.get("NextToken")

                # Handle pagination for managed policies
                while not utils.is_nothing(managed_policies_token):
                    managed_policies_kwargs["NextToken"] = managed_policies_token
                    managed_policies_response = sso_admin.list_managed_policies_in_permission_set(
                        **managed_policies_kwargs
                    )
                    managed_policies.extend(managed_policies_response.get("AttachedManagedPolicies", []))
                    managed_policies_token = managed_policies_response.get("NextToken")

                if managed_policies:
                    permission_set_data["ManagedPolicies"] = managed_policies

                permission_sets[permission_set_id] = permission_set_data

            return results.get("NextToken")

        next_token = get_permission_sets()

        while not utils.is_nothing(next_token):
            self.logger.info("Still more permission sets to get...")
            next_token = get_permission_sets(next_token)

        return self.exit_run(
            results=permission_sets,
            key="permission_sets",
            encode_to_base64=True,
            format_json=False,
            unhump_results=unhump_permission_sets,
            sort_by_field="Name" if sort_by_name else None,
            exit_on_completion=exit_on_completion,
        )

    def get_aws_sso_account_assignments(
        self,
        users: Optional[dict[str, Any]] = None,
        groups: Optional[dict[str, Any]] = None,
        account_id: Optional[str] = None,
        permission_set_arn: Optional[str] = None,
        sort_by_name: Optional[bool] = None,
        exit_on_completion: bool = True,
    ):
        """Gets all AWS account assignments for an account and permission set

        generator=key: assignments, module_class: aws
        foreach=module_name: get_aws_account_assignments_for_accounts

        name: users, required: false, default: {}, json_encode: true, base64_encode: true
        name: groups, required: false, default: {}, json_encode: true, base64_encode: true
        name: aws_accounts, required: true, foreach_only: true, foreach_iterator: true, json_encode: true, base64_encode: true
        name: account_id, required: true, type: string, foreach_key: true
        name: permission_set_arn, required: true, type: string
        name: sort_by_name, required: false, default: false
        """
        if users is None:
            users = self.decode_input("users", required=False, default={}, allow_none=False)

        if groups is None:
            groups = self.decode_input("groups", required=False, default={}, allow_none=False)

        if account_id is None:
            account_id = self.get_input("account_id")

        if permission_set_arn is None:
            permission_set_arn = self.get_input("permission_set_arn")

        if sort_by_name is None:
            sort_by_name = self.get_input("sort_by_name", required=False, default=False, is_bool=True)

        self.logger.info(f"Getting AWS account assignments for {account_id} and {permission_set_arn}")

        if utils.is_nothing(users):
            self.logger.info("Fetching AWS users for matching principals")
            users = self.get_aws_users(unhump_users=True, sort_by_name=False, exit_on_completion=False)

        if utils.is_nothing(groups):
            self.logger.info("Fetching AWS groups for matching principals")
            groups = self.get_aws_groups(unhump_groups=True, sort_by_name=False, exit_on_completion=False)

        identity_store_arn = self.get_identity_store_id(key="InstanceArn")

        # Configure the client with standard retry mode
        from botocore.config import Config

        retry_config = Config(
            retries={
                "max_attempts": 5,  # Includes the initial call plus 4 retries
                "mode": "standard",  # Use standard retry mode which includes more retryable errors
            }
        )

        sso_admin = self.get_aws_client(client_name="sso-admin", config=retry_config)
        assignments = utils.get_default_dict()

        # Function to handle delete_account_assignment with proper exception handling
        def delete_assignment(pi: str, pt: str) -> bool:
            try:
                response = sso_admin.delete_account_assignment(
                    InstanceArn=identity_store_arn,
                    PermissionSetArn=permission_set_arn,
                    PrincipalId=pi,
                    PrincipalType=pt,
                    TargetId=account_id,
                    TargetType="AWS_ACCOUNT",
                )

                # Log retry attempts if any occurred
                ra = response.get("ResponseMetadata", {}).get("RetryAttempts", 0)
                if ra > 0:
                    self.logger.info(f"Successfully deleted assignment after {ra} retry attempts")
                else:
                    self.logger.info(f"Successfully deleted invalid assignment for {pt} {pi}")

                return True

            except AWSClientError as e:
                ec = e.response["Error"]["Code"]
                em = e.response["Error"]["Message"]
                ri = e.response["ResponseMetadata"]["RequestId"]
                hc = e.response["ResponseMetadata"]["HTTPStatusCode"]
                ra = e.response["ResponseMetadata"].get("RetryAttempts", 0)

                # Resource not found is not an error for deletion
                if ec == "ResourceNotFoundException":
                    self.logger.info(f"Assignment for {pt} {pi} does not exist: {em}")
                    return True

                # Log with appropriate level based on error type
                if ec in ("ThrottlingException", "InternalServerException"):
                    log_method = self.logger.warning
                else:
                    log_method = self.logger.error

                log_method(
                    f"Error when deleting assignment for {pt} {pi}: "
                    f"{ec} - {em}. RequestID: {ri}, HTTP: {hc}, "
                    f"Retry attempts: {ra}"
                )

                # Add to errors list with detailed information
                self.errors.append(
                    f"AWS error for delete_account_assignment: {ec} - {em} " f"(RequestID: {ri}, Retries: {ra})"
                )

            except AWSParamValidationError as e:
                self.logger.error(f"Parameter validation error: {str(e)}")
                self.errors.append(f"Parameter validation error: {str(e)}")

            except Exception as e:
                self.logger.error(f"Unexpected error when deleting assignment: {str(e)}")
                self.errors.append(f"Unexpected error for delete_account_assignment: {str(e)}")

            return False

        # Get and process paginator results
        try:
            paginate_params = {
                "AccountId": account_id,
                "InstanceArn": identity_store_arn,
                "PermissionSetArn": permission_set_arn,
            }

            assignments_paginator = sso_admin.get_paginator("list_account_assignments")
            page_iterator = assignments_paginator.paginate(**paginate_params, PaginationConfig={"PageSize": 100})

            # Get all assignments directly using JMESPath
            all_assignments = page_iterator.search("AccountAssignments[]")

            # Process the assignments
            assignment_count = 0
            for assignment in all_assignments:
                assignment_count += 1
                principal_id = assignment["PrincipalId"]
                principal_id_key = inflection.underscore(principal_id)
                principal_type = assignment["PrincipalType"]

                if principal_type == "USER":
                    principal_data = users.get(principal_id_key, {})
                    principal_name = principal_data.get("user_name")
                elif principal_type == "GROUP":
                    principal_data = groups.get(principal_id_key, {})
                    principal_name = principal_data.get("display_name")
                else:
                    self.errors.append(
                        f"Unsupported principal type {principal_type} for principal ID {principal_id} in assignment: {assignment}"
                    )
                    continue

                if utils.is_nothing(principal_data) or not principal_name:
                    self.logger.warning(
                        f"No matching {principal_type} found for principal {principal_id} or principal is missing name for assignment: {assignment}\nCleaning up invalid principal assignment"
                    )
                    delete_assignment(principal_id, principal_type)
                    continue

                if sort_by_name:
                    assignments[principal_type][principal_name] = principal_data
                else:
                    assignments[principal_type][principal_id] = principal_data

            self.logger.info(f"Processed {assignment_count} assignments")

        except AWSClientError as exc:
            error_code = exc.response["Error"]["Code"]
            error_message = exc.response["Error"]["Message"]
            request_id = exc.response["ResponseMetadata"]["RequestId"]
            http_code = exc.response["ResponseMetadata"]["HTTPStatusCode"]
            retry_attempts = exc.response["ResponseMetadata"].get("RetryAttempts", 0)

            self.logger.error(
                f"AWS API error during pagination: {error_code} - {error_message}. "
                f"RequestID: {request_id}, HTTP: {http_code}, Retry attempts: {retry_attempts}"
            )
            self.errors.append(
                f"AWS API error during pagination: {error_code} - {error_message} "
                f"(RequestID: {request_id}, Retries: {retry_attempts})"
            )

        except AWSParamValidationError as exc:
            self.logger.error(f"Parameter validation error during pagination: {str(exc)}")
            self.errors.append(f"Parameter validation error: {str(exc)}")

        except Exception as exc:
            self.logger.error(f"Unexpected error during pagination: {str(exc)}")
            self.errors.append(f"Unexpected error during pagination: {str(exc)}")

        return self.exit_run(
            results=assignments,
            key="assignments",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def label_aws_account(
        self,
        aws_account: Optional[dict[str, Any]] = None,
        aws_organization_units: Optional[dict[str, Any]] = None,
        domains: Optional[dict[str, str]] = None,
        caller_account_id: Optional[str] = None,
        exit_on_completion: bool = True,
    ):
        """Labels an AWS account or accounts with metadata

        generator=key: accounts, module_class: aws

        name: aws_account, required: true, json_encode: true, base64_encode: true, foreach_value: true
        name: aws_accounts, required: true, foreach_only: true, foreach_iterator: true, json_encode: true, base64_encode: true
        name: account_key, required: true, type: string, foreach_key: true
        name: aws_organization_units, required: false, json_encode: true, base64_encode: true
        name: domains, required: true, json_encode: true, base64_encode: true
        name: caller_account_id, required: false, type: string
        """
        if aws_account is None:
            aws_account = self.decode_input("aws_account", required=True)

        if aws_organization_units is None:
            aws_organization_units = self.decode_input("aws_organization_units", required=False)

        if domains is None:
            domains = self.decode_input("domains", required=True)

        if caller_account_id is None:
            caller_account_id = self.get_input("caller_account_id", required=False)
            if not caller_account_id:
                self.logger.info("Fetching caller identity...")
                aws_client = self.get_aws_client(client_name="sts")
                response = aws_client.get_caller_identity()
                caller_account_id = response.get("Account")
                if not caller_account_id:
                    raise RuntimeError("Failed to get caller account ID")

        self.logger.info("Getting AWS accounts and labeling them")
        labeled_accounts = {}

        # Get organization accounts
        self.logger.info("Getting AWS organization accounts")
        org_units = {}
        orgs = self.get_aws_client(client_name="organizations")

        # Get root information
        self.logger.info("Getting root information")
        roots = orgs.list_roots()
        try:
            root_parent_id = roots["Roots"][0]["Id"]
        except (KeyError, IndexError) as exc:
            raise RuntimeError(f"Failed to find root parent ID: {roots}") from exc

        self.logger.info(f"Root parent ID: {root_parent_id}")

        accounts_paginator = orgs.get_paginator("list_accounts_for_parent")
        ou_paginator = orgs.get_paginator("list_organizational_units_for_parent")
        tags_paginator = orgs.get_paginator("list_tags_for_resource")

        # Helper function to yield tag key-value pairs
        def yield_tag_keypairs(tags: list[dict[str, str]]):
            for tag in tags:
                yield tag["Key"], tag["Value"]

        # Helper function to process classifications
        def process_classifications(classification_str):
            if not classification_str:
                return []
            return [
                re.sub(r"[^A-Za-z0-9_-]+", "_", c).lower().removesuffix("_accounts")
                for c in classification_str.split(" ")
                if c
            ]

        # Extract accounts and OUs recursively
        def get_accounts_recursive(parent_id):
            accounts = {}
            for page in accounts_paginator.paginate(ParentId=parent_id):
                for account in page["Accounts"]:
                    account_id = account["Id"]
                    account_tags = {}
                    for tags_page in tags_paginator.paginate(ResourceId=account_id):
                        for k, v in yield_tag_keypairs(tags_page["Tags"]):
                            account_tags[k] = v

                    account["tags"] = account_tags
                    accounts[account_id] = account

            for page in ou_paginator.paginate(ParentId=parent_id):
                for ou in page["OrganizationalUnits"]:
                    ou_id = ou["Id"]
                    ou_name = ou["Name"]

                    # Process OU data for the aws_organization_units structure
                    if ou_id not in org_units:
                        # Get OU tags
                        ou_tags = {}
                        for tags_page in tags_paginator.paginate(ResourceId=ou_id):
                            for k, v in yield_tag_keypairs(tags_page["Tags"]):
                                ou_tags[k] = v

                        # Create unit entry in expected format for labeling
                        org_units[ou_name] = {
                            "id": ou_id,
                            "name": ou_name,
                            "control_tower_organizational_unit": f"{ou_name} ({ou_id})",
                            "tags": ou_tags,
                        }

                    # Process accounts in this OU
                    for account_id, account_data in get_accounts_recursive(ou_id).items():
                        # Add OU information to account
                        account_data["OuId"] = ou_id
                        account_data["OuName"] = ou_name
                        account_data["OuTags"] = org_units[ou_name]["tags"]
                        accounts[account_id] = account_data

            return accounts

        # Get all organization accounts
        aws_organization_accounts = get_accounts_recursive(root_parent_id)

        # Mark all organization accounts as initially unmanaged
        for account_id in aws_organization_accounts:
            aws_organization_accounts[account_id]["managed"] = False

        # Use the extracted org_units if aws_organization_units wasn't provided
        if not aws_organization_units:
            aws_organization_units = org_units

        # Get Control Tower accounts
        self.logger.info("Getting AWS Control Tower accounts")
        service_catalog = self.get_aws_client(client_name="servicecatalog")

        # Find the Control Tower Account Factory product
        account_factory = service_catalog.search_products_as_admin(
            Filters={
                "FullTextSearch": [
                    "AWS Control Tower Account Factory",
                ]
            }
        )

        try:
            product_id = account_factory["ProductViewDetails"][0]["ProductViewSummary"]["ProductId"]
        except (KeyError, IndexError) as exc:
            raise RuntimeError(
                f"Failed to find account factory product ID from service catalog: {account_factory}"
            ) from exc

        if utils.is_nothing(product_id):
            raise RuntimeError(f"Account factory product ID returned from AWS is empty: {account_factory}")

        self.logger.info(f"Control Tower product ID: {product_id}")

        # Helper function to get provisioned accounts
        def get_provisioned_accounts(last_token=None):
            search_params = {
                "Filters": {
                    "SearchQuery": [
                        product_id,
                    ]
                }
            }

            if not utils.is_nothing(last_token):
                search_params["PageToken"] = last_token

            return service_catalog.search_provisioned_products(**search_params)

        # Get Control Tower accounts
        controltower_accounts = {}
        next_page_token = None

        while True:
            results = get_provisioned_accounts(next_page_token)
            provisioned_products = results.get("ProvisionedProducts", [])

            for account in provisioned_products:
                provisioned_account_id = account["PhysicalId"]
                provisioned_product_id = account["Id"]

                # Extract account data
                ct_account = {
                    "id": provisioned_account_id,
                    "name": account["Name"],
                    "provisioned_product_id": provisioned_product_id,
                    "managed": True,
                    "tags": {},
                }

                # Process tags
                for tag in account.get("Tags", []):
                    ct_account["tags"][tag["Key"]] = tag["Value"]

                # Get outputs
                for output in service_catalog.get_provisioned_product_outputs(
                    ProvisionedProductId=provisioned_product_id
                ).get("Outputs", []):
                    ct_account[output["OutputKey"]] = output["OutputValue"]

                # Find or set organizational unit
                if "OrganizationalUnit" in ct_account:
                    ou_match = re.search(r"\((.*?)\)", ct_account["OrganizationalUnit"])
                    if ou_match:
                        ct_account["parent_id"] = ou_match.group(1)

                controltower_accounts[provisioned_account_id] = ct_account

            next_page_token = results.get("NextPageToken")
            if not next_page_token:
                break

        # Merge organization and Control Tower accounts and label them
        for account_id, account_data in aws_organization_accounts.items():
            # Convert to the format expected by label_aws_account
            aws_account = {
                "account_id": account_id,
                "id": account_id,
                "name": account_data.get("Name", ""),
                "email": account_data.get("Email", ""),
                "parent_id": account_data.get("OuId", ""),
                "organizational_unit": account_data.get("OuName", ""),
                "unit": account_data.get("OuName", ""),
                "tags": account_data.get("tags", {}),
                "managed": False,
            }

            # Check if it's also a Control Tower account
            if account_id in controltower_accounts:
                ct_data = controltower_accounts[account_id]
                aws_account["managed"] = True
                aws_account["provisioned_product_id"] = ct_data.get("provisioned_product_id")
                aws_account["account_id"] = account_id

                # Merge any additional CT data
                for key, value in ct_data.items():
                    if key not in aws_account and key not in ["id", "name", "tags"]:
                        aws_account[key] = value

            # Label the account
            # Extract unit for this account
            unit = {}
            parent_id = aws_account.get("parent_id")
            ou_label = aws_account.get("organizational_unit")

            if parent_id or ou_label:
                # Try to find by parent_id
                if parent_id:
                    for unit_name, unit_data in aws_organization_units.items():
                        if unit_data["id"] == parent_id:
                            unit = deepcopy(unit_data)
                            break

                # Try by OU label if not found by parent_id
                if not unit and ou_label:
                    extracted_id = None
                    match = re.search(r"\((.*?)\)", ou_label)
                    if match:
                        extracted_id = match.group(1)

                    for unit_name, unit_data in aws_organization_units.items():
                        ctrl_tower_ou = unit_data.get("control_tower_organizational_unit")
                        if (ctrl_tower_ou and ou_label == ctrl_tower_ou) or (
                            extracted_id and unit_data["id"] == extracted_id
                        ):
                            unit = deepcopy(unit_data)
                            break

            # Get unit tags
            unit_tags = unit.get("tags", {})

            # Apply labeling logic
            account_name = aws_account["name"]
            aws_account["account_name"] = account_name

            # Normalize name and create network name/json key
            normalized_name = account_name.replace(" ", "")
            json_key = normalized_name.replace("-", "_")
            aws_account["json_key"] = json_key

            network_name = normalized_name.replace("_", "-").lower()
            aws_account["network_name"] = network_name

            # Process execution role
            tags = aws_account.get("tags", {})
            root_account = aws_account["id"] == caller_account_id
            execution_role_name = "" if root_account else tags.get("ExecutionRoleName", "AWSControlTowerExecution")
            execution_role_arn = "" if root_account else f"arn:aws:iam::{account_id}:role/{execution_role_name}"
            aws_account["execution_role_arn"] = execution_role_arn

            # Process environment and domain
            environment = tags.get("Environment", "dev" if account_name.startswith("User-") else "global")
            aws_account["environment"] = environment
            domain = aws_account.get("domain", domains.get(environment))
            aws_account["domain"] = domain

            # Set subdomain
            aws_account["subdomain"] = (
                domain
                if environment not in ["stg", "prod"] or domain.startswith(network_name)
                else f"{network_name}.{domain}"
            )

            # Process spoke status
            spoke = utils.strtobool(tags.get("Spoke", unit_tags.get("Spoke", False)))
            aws_account["spoke"] = spoke

            # Process classifications
            account_classifications = process_classifications(tags.get("Classifications", ""))
            unit_classifications = process_classifications(unit_tags.get("Classifications", ""))
            aws_account["classifications"] = list(set(account_classifications + unit_classifications))

            # Add to labeled accounts
            labeled_accounts[account_id] = aws_account

        # Also include any Control Tower accounts not in Organization accounts
        for account_id, ct_data in controltower_accounts.items():
            if account_id not in labeled_accounts:
                # Format account data
                aws_account = {
                    "id": account_id,
                    "name": ct_data.get("name", ""),
                    "parent_id": ct_data.get("parent_id", ""),
                    "organizational_unit": ct_data.get("OrganizationalUnit", ""),
                    "unit": ct_data.get("OrganizationalUnit", ""),
                    "tags": ct_data.get("tags", {}),
                    "managed": True,
                    "provisionedj_product_id": ct_data.get("provisioned_product_id"),
                }

                # Apply same labeling logic as above (simplified for brevity)
                account_name = aws_account["name"]
                aws_account["account_name"] = account_name

                normalized_name = account_name.replace(" ", "")
                aws_account["json_key"] = normalized_name.replace("-", "_")
                aws_account["network_name"] = normalized_name.replace("_", "-").lower()

                # Find matching unit
                unit = {}
                for unit_name, unit_data in aws_organization_units.items():
                    if (aws_account.get("parent_id") and unit_data["id"] == aws_account["parent_id"]) or (
                        aws_account.get("organizational_unit")
                        and unit_data.get("control_tower_organizational_unit") == aws_account["organizational_unit"]
                    ):
                        unit = deepcopy(unit_data)
                        break

                # Apply same domain and classification logic
                tags = aws_account.get("tags", {})
                unit_tags = unit.get("tags", {})

                environment = tags.get("Environment", "dev" if account_name.startswith("User-") else "global")
                aws_account["environment"] = environment
                domain = aws_account.get("domain", domains.get(environment))
                aws_account["domain"] = domain

                aws_account["subdomain"] = (
                    domain
                    if environment not in ["stg", "prod"] or domain.startswith(aws_account["network_name"])
                    else f"{aws_account['network_name']}.{domain}"
                )

                aws_account["spoke"] = utils.strtobool(tags.get("Spoke", unit_tags.get("Spoke", False)))

                account_classifications = process_classifications(tags.get("Classifications", ""))
                unit_classifications = process_classifications(unit_tags.get("Classifications", ""))
                aws_account["classifications"] = list(set(account_classifications + unit_classifications))

                # Add to labeled accounts
                labeled_accounts[account_id] = aws_account

        self.logger.info(f"Labeled {len(labeled_accounts)} AWS accounts")

        classified_accounts = utils.get_default_dict(use_sorted_dict=True)

        for account_id, account_data in labeled_accounts.items():
            self.logger.info(f"Classifying {account_id}")
            classified_accounts["accounts"][account_id] = account_data
            classified_accounts["accounts_by_name"][account_data["name"]] = account_data
            classified_accounts["accounts_by_json_key"][account_data["json_key"]] = account_data

            for classification in account_data["classifications"]:
                if not classification or classification == "accounts":
                    self.logger.warning(f"Skipping invalid classification '{classification}'")
                    continue

                classified_accounts[f"{classification}_accounts"][account_id] = account_data
                classified_accounts[f"{classification}_accounts_by_name"][account_data["name"]] = account_data
                classified_accounts[f"{classification}_accounts_by_json_key"][account_data["json_key"]] = account_data

                account_environment = account_data.get("environment")
                if utils.is_nothing(account_environment):
                    self.logger.warning(f"Skipping {account_id} from environment classification, has no environment")
                elif account_environment in classified_accounts[f"{classification}_accounts_by_environment"]:
                    self.logger.info(
                        f"Promoting {classification}_accounts_by_environment to hold multiple accounts under environment classification {account_environment}"
                    )
                    existing_held_account = classified_accounts[f"{classification}_accounts_by_environment"][
                        account_environment
                    ]
                    classified_accounts[f"{classification}_accounts_by_environment"][account_environment] = [
                        existing_held_account,
                        account_data,
                    ]
                else:
                    classified_accounts[f"{classification}_accounts_by_environment"][account_environment] = account_data

            if not utils.is_nothing(caller_account_id) and caller_account_id in labeled_accounts:
                classified_accounts["root_account"] = labeled_accounts[caller_account_id]

        return self.exit_run(
            results=classified_accounts,
            key="accounts",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def get_aws_organization_accounts(
        self,
        unhump_accounts: Optional[bool] = None,
        sort_by_name: Optional[bool] = None,
        exit_on_completion: bool = False,
    ):
        """Gets all AWS accounts managed through AWS Organizations

        generator=key: accounts, module_class: aws

        name: unhump_accounts, required: false, default: true
        name: sort_by_name, required: false, default: false
        """
        if unhump_accounts is None:
            unhump_accounts = self.get_input("unhump_accounts", required=False, default=True, is_bool=True)

        if sort_by_name is None:
            sort_by_name = self.get_input("sort_by_name", required=False, default=False, is_bool=True)

        self.logger.info("Getting AWS organization accounts")

        org_units = {}

        orgs = self.get_aws_client(client_name="organizations")
        self.logger.info("Getting root information")
        roots = orgs.list_roots()

        try:
            root_parent_id = roots["Roots"][0]["Id"]
        except (KeyError, IndexError) as exc:
            raise RuntimeError(f"Failed to find root parent ID: {roots}") from exc

        self.logger.info(f"Root parent ID: {root_parent_id}")

        accounts_paginator = orgs.get_paginator("list_accounts_for_parent")
        ou_paginator = orgs.get_paginator("list_organizational_units_for_parent")
        tags_paginator = orgs.get_paginator("list_tags_for_resource")

        def yield_tag_keypairs(tags: list[dict[str, str]]):
            for tag in tags:
                yield tag["Key"], tag["Value"]

        def get_accounts_recursive(parent_id):
            accounts = {}
            for page in accounts_paginator.paginate(ParentId=parent_id):
                for account in page["Accounts"]:
                    account_id = account["Id"]
                    account_tags = {}
                    for tags_page in tags_paginator.paginate(ResourceId=account_id):
                        for k, v in yield_tag_keypairs(tags_page["Tags"]):
                            account_tags[k] = v

                    account["tags"] = account_tags
                    accounts[account_id] = account

            for page in ou_paginator.paginate(ParentId=parent_id):
                for ou in page["OrganizationalUnits"]:
                    ou_id = ou["Id"]
                    ou_data = org_units.get(ou_id)
                    if utils.is_nothing(ou_data):
                        ou_data = {}
                        for k, v in deepcopy(ou).items():
                            ou_data[f"Ou{k.title()}"] = v

                        org_units[ou_id] = ou_data

                    for account_id, account_data in get_accounts_recursive(ou_id).items():
                        accounts[account_id] = self.merger.merge(deepcopy(account_data), deepcopy(ou_data))

            return accounts

        aws_accounts = get_accounts_recursive(root_parent_id)

        self.logger.info("Setting organization accounts initially to unmanaged")
        for account_id in deepcopy(aws_accounts).keys():
            aws_accounts[account_id]["managed"] = False

        return self.exit_run(
            results=aws_accounts,
            key="accounts",
            encode_to_base64=True,
            format_json=False,
            unhump_results=unhump_accounts,
            sort_by_field="Name" if sort_by_name else None,
            exit_on_completion=exit_on_completion,
        )

    def get_aws_controltower_accounts(
        self,
        unhump_accounts: Optional[bool] = None,
        sort_by_name: Optional[bool] = None,
        exit_on_completion: bool = True,
    ):
        """Gets AWS accounts managed with ControlTower

        generator=key: accounts, module_class: aws

        name: unhump_accounts, required: false, default: true
        name: sort_by_name, required: false, default: false
        """
        if unhump_accounts is None:
            unhump_accounts = self.get_input("unhump_accounts", required=False, default=True, is_bool=True)

        if sort_by_name is None:
            sort_by_name = self.get_input("sort_by_name", required=False, default=False, is_bool=True)

        self.logger.info("Getting AWS Control Tower accounts")

        self.logger.info("Getting AWS users to match accounts with")
        aws_users = self.get_aws_users(unhump_users=False, sort_by_name=True, exit_on_completion=False)

        service_catalog = self.get_aws_client(client_name="servicecatalog")
        account_factory = service_catalog.search_products_as_admin(
            Filters={
                "FullTextSearch": [
                    "AWS Control Tower Account Factory",
                ]
            }
        )

        self.logger.info("Fetching the Control Tower product ID")

        try:
            product_id = account_factory["ProductViewDetails"][0]["ProductViewSummary"]["ProductId"]
        except (KeyError, IndexError) as exc:
            raise RuntimeError(
                f"Failed to find account factory product ID from service catalog: {account_factory}"
            ) from exc

        if utils.is_nothing(product_id):
            raise RuntimeError(f"Account factory product ID returned from AWS is empty: {account_factory}")

        self.logger.info(f"Control Tower product ID: {product_id}")
        self.logger.info("Fetching the Control Tower provisioned accounts")

        aws_accounts = {}

        def get_account_email(ad: dict[str, Any]) -> str | None:
            return ad.get("SSOUserEmail", ad.get("AccountEmail"))

        def get_provisioned_accounts(last_token: Optional[str] = None):
            if utils.is_nothing(last_token):
                results = service_catalog.search_provisioned_products(
                    Filters={
                        "SearchQuery": [
                            product_id,
                        ]
                    }
                )
            else:
                results = service_catalog.search_provisioned_products(
                    Filters={
                        "SearchQuery": [
                            product_id,
                        ]
                    },
                    PageToken=last_token,
                )

            provisioned_products = results.get("ProvisionedProducts", [])

            for account in provisioned_products:
                provisioned_account_id = account["PhysicalId"]
                provisioned_product_id = account["Id"]
                account["ProvisionedProductId"] = provisioned_product_id
                account["Id"] = provisioned_account_id
                account_tags = account.get("Tags", [])
                account["Tags"] = {}
                for tag in account_tags:
                    account["Tags"][tag["Key"]] = tag["Value"]

                self.logger.info(f"Fetching outputs for {provisioned_account_id}")
                for output in service_catalog.get_provisioned_product_outputs(
                    ProvisionedProductId=provisioned_product_id
                ).get("Outputs", []):
                    account[output["OutputKey"]] = output["OutputValue"]

            return results.get("NextPageToken")

        next_page_token = get_provisioned_accounts()

        while not utils.is_nothing(next_page_token):
            self.logger.info("More accounts remain to be fetched...")
            next_page_token = get_provisioned_accounts(next_page_token)

        return self.exit_run(
            results=aws_accounts,
            key="accounts",
            encode_to_base64=True,
            format_json=False,
            unhump_results=unhump_accounts,
            sort_by_field="Name" if sort_by_name else None,
            exit_on_completion=exit_on_completion,
        )

    def get_aws_accounts(
        self,
        unhump_accounts: Optional[bool] = None,
        sort_by_name: Optional[bool] = None,
        label_aws_accounts: Optional[bool] = None,
        aws_organization_units: Optional[dict[str, Any]] = None,
        domains: Optional[dict[str, str]] = None,
        caller_account_id: Optional[str] = None,
        exit_on_completion: bool = True,
    ):
        """Gets all AWS accounts managed with ControlTower or AWS Organizations

        generator=key: accounts, module_class: aws

        name: unhump_accounts, required: false, default: true
        name: sort_by_name, required: false, default: false
        name: label_aws_accounts, required: false, default: false
        name: aws_organization_units, required: false, json_encode: true, base64_encode: true
        name: domains, required: false, json_encode: true, base64_encode: true
        name: caller_account_id, required: false, type: string
        """
        if unhump_accounts is None:
            unhump_accounts = self.get_input("unhump_accounts", required=False, default=True, is_bool=True)

        if sort_by_name is None:
            sort_by_name = self.get_input("sort_by_name", required=False, default=False, is_bool=True)

        if label_aws_accounts is None:
            label_aws_accounts = self.get_input("label_aws_accounts", required=False, default=False, is_bool=True)

        if aws_organization_units is None and label_aws_accounts:
            aws_organization_units = self.decode_input("aws_organization_units", required=False)

        if domains is None and label_aws_accounts:
            domains = self.decode_input("domains", required=False)

        if caller_account_id is None and label_aws_accounts:
            caller_account_id = self.get_input("caller_account_id", required=False)

        aws_organization_accounts = self.get_aws_organization_accounts(
            unhump_accounts=False, sort_by_name=False, exit_on_completion=False
        )

        for account_id in aws_organization_accounts.keys():
            aws_organization_accounts[account_id]["Managed"] = False

        aws_controltower_accounts = self.get_aws_controltower_accounts(
            unhump_accounts=False, sort_by_name=False, exit_on_completion=False
        )

        for account_id in aws_controltower_accounts.keys():
            aws_controltower_accounts[account_id]["Managed"] = True

        aws_accounts = self.merger.merge(aws_organization_accounts, aws_controltower_accounts)

        # Label AWS accounts if requested
        if label_aws_accounts and aws_organization_units and domains:
            self.logger.info("Labeling AWS accounts...")

            for account_id, account_data in deepcopy(aws_accounts).items():
                labeled_account = self.label_aws_account(
                    aws_account=account_data,
                    aws_organization_units=aws_organization_units,
                    domains=domains,
                    caller_account_id=caller_account_id,
                    exit_on_completion=False,
                )
                if utils.is_nothing(labeled_account):
                    self.errors.append(f"Labeling AWS account {account_id} returned nothing after, skipping account.")
                    continue

                aws_accounts[account_id] = labeled_account

        return self.exit_run(
            results=aws_accounts,
            key="accounts",
            encode_to_base64=True,
            format_json=False,
            unhump_results=unhump_accounts,
            sort_by_field="Name" if sort_by_name else None,
            exit_on_completion=exit_on_completion,
        )

    def get_new_aws_controltower_accounts_from_google(
        self,
        aws_organization_units: Optional[dict[str, Any]] = None,
        default_environment: Optional[str] = None,
        exit_on_completion: bool = True,
    ):
        """Gets new AWS accounts managed with ControlTower

        generator=key: accounts, module_class: aws

        name: aws_organization_units, required: true, json_encode: true, base64_encode: true
        name: default_environment, required: false, default: "global"
        """
        if aws_organization_units is None:
            aws_organization_units = self.decode_input("aws_organization_units", required=True)

        if default_environment is None:
            default_environment = self.get_input("default_environment", required=False, default="global")

        self.logger.info("Getting new AWS Control Tower accounts from Google")
        google_users = {
            data["primary_email"]: data
            for data in self.get_google_users(
                unhump_users=True, flatten_name=True, active_only=True, include_bots=False, exit_on_completion=False
            ).values()
        }

        google_groups = {
            data["name"]: data
            for data in self.get_google_groups(unhump_groups=True, sort_by_name=True, exit_on_completion=False).values()
        }

        new_accounts = {}

        for unit_key, unit_data in aws_organization_units.items():
            if "provisioning" not in unit_data:
                self.logger.warning(f"No provisioning config found for  organization unit {unit_key}, skipping")
                continue

            self.logger.info(f"Getting new AWS Control Tower accounts for organization unit {unit_key}")
            unit_provisioning = unit_data["provisioning"]
            unit_remaps = unit_provisioning.get("remaps", {})
            unit_user_emails = unit_provisioning.get("users", [])
            unit_group_names = unit_provisioning.get("groups", [])

            for group_name in unit_group_names:
                if group_name not in google_groups:
                    self.errors.append(f"Skipping group {group_name}, group not found")
                    continue

                group_data = google_groups[group_name]

                self.logger.info(f"Checking members for group {group_name}")
                group_members = group_data.get("members")
                if utils.is_nothing(group_members):
                    self.logger.warning(f"No members for group {group_name}, skipping group")
                    continue

                for member_email, member_data in group_members.items():
                    member_type = member_data.get("type")
                    member_status = member_data.get("status")
                    if member_type != "USER" or member_status != "ACTIVE" or member_email not in google_users:
                        self.logger.warning(f"Skipping {member_email}, not a user, not active, or not found")
                        continue

                    if member_email not in unit_user_emails:
                        self.logger.info(f"Adding {member_email} to unit user emails")
                        unit_user_emails.append(member_email)

                    if "classifications" not in google_users[member_email]:
                        google_users[member_email]["classifications"] = []

                    group_classification = group_name.replace(" ", "_").lower()
                    if group_classification not in google_users[member_email]["classifications"]:
                        self.logger.info(f"Adding {group_classification} as a classification for {member_email}")
                        google_users[member_email]["classifications"].append(group_classification)

            for primary_email in unit_user_emails:
                if primary_email not in google_users or "@" not in primary_email:
                    self.errors.append(f"Skipping {primary_email}, not found in Google users or primary email invalid")
                    continue

                user_data = google_users[primary_email]
                primary_email_remap = unit_remaps.get(primary_email, {})
                account_email = primary_email_remap.get("account_email", primary_email)
                key = primary_email_remap.get("key")
                account_name = primary_email_remap.get("account_name")

                if not key or not account_name:
                    # Extract local part
                    local_part = primary_email.split("@", 1)[0].strip().lower()

                    # Use translation tables
                    if not key:
                        trans_table_key = str.maketrans({".": "_", "_": "_"})  # optional _:_ for safety
                        key = f"user_{local_part.translate(trans_table_key)}"

                    if not account_name:
                        trans_table_name = str.maketrans({".": "-", "_": "-"})
                        account_name = f"User-{local_part.translate(trans_table_name).title().replace(' ', '')}"

                if key in new_accounts:
                    self.errors.append(f"Duplicate account key {key}")
                    continue

                unit_classifications = set(unit_data.get("classifications", []))
                unit_classifications.add(unit_key.replace(" ", "_").lower())
                account_classifications = set(user_data.get("classifications", []))
                account_classifications.update(unit_classifications)

                new_accounts[key] = {
                    "name": account_name,
                    "email": account_email,
                    "sso_email": primary_email,
                    "first_name": user_data["given_name"],
                    "last_name": user_data["family_name"],
                    "organizational_unit": unit_key,
                    "classifications": sorted(account_classifications),
                    "environment": unit_data.get("environment", default_environment),
                    "close_on_deletion": True,
                    "control_tower_managed": True,
                    "execution_role_name": "AWSControlTowerExecution",
                }

        if self.errors:
            self.logger.warning(
                f"At least one error occurred, dumping user names:\n{list(google_users.keys())}And group names:\n{list(google_groups.keys())}\nFor diagnostics"
            )

        return self.exit_run(
            results=new_accounts,
            key="accounts",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def get_aws_codedeploy_deployments(
        self,
        application_name: Optional[str] = None,
        deployment_group_name: Optional[str] = None,
        include_only: Optional[list[str]] = None,
        execution_role_arn: Optional[str] = None,
        role_session_name: Optional[str] = None,
        raise_on_error: Optional[bool] = None,
        exit_on_completion: bool = True,
    ):
        """Gets all CodeDeploy deployments for an application and deployment group

        generator=key: deployments, module_class: aws

        name: application_name, required: true, type: string
        name: deployment_group_name, required: true, type: string
        name: include_only, required: false, default: [], json_encode: true, base64_encode: false
        name: execution_role_arn, required: false, type: string
        name: role_session_name, required: false, type: string
        name: raise_on_error, required: false, default: false
        """
        if application_name is None:
            application_name = self.get_input(
                "application_name",
                required=True,
            )

        if deployment_group_name is None:
            deployment_group_name = self.get_input(
                "deployment_group_name",
                required=True,
            )

        if include_only is None:
            include_only = self.decode_input(
                "include_only",
                required=False,
                default=[],
                allow_none=False,
                decode_from_base64=False,
            )

        if execution_role_arn is None:
            execution_role_arn = self.get_input("execution_role_arn", required=False)

        if role_session_name is None:
            role_session_name = self.get_input("role_session_name", required=False)

        if raise_on_error is None:
            raise_on_error = self.get_input("raise_on_error", required=False, default=False, is_bool=True)

        self.logger.info(
            f"Getting all CodeDeploy deployments for {application_name} in deployment group {deployment_group_name}"
        )

        valid_include_only_statuses = {
            "Created",
            "Queued",
            "InProgress",
            "Baking",
            "Succeeded",
            "Failed",
            "Stopped",
            "Ready",
        }

        invalid_include_only_statuses = set(include_only) - valid_include_only_statuses
        if len(invalid_include_only_statuses) > 0:
            raise ValueError(f"Invalid statuses specified for include_only: {invalid_include_only_statuses}")

        code_deploy = self.get_aws_client(
            client_name="codedeploy",
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
        )

        paginator = code_deploy.get_paginator("list_deployments")
        deployments = set()

        try:
            page_iterator = paginator.paginate(
                applicationName=application_name,
                deploymentGroupName=deployment_group_name,
                includeOnlyStatuses=include_only,
                PaginationConfig={
                    "MaxItems": 100,
                },
            )

            for page in page_iterator:
                deployments.update(page["deployments"])
        except AWSClientError:
            if raise_on_error:
                raise

            self.logger.warning(
                f"A client error occurred while getting CodeDeploy deployments for Application {application_name} and / or deployment group {deployment_group_name}",
                exc_info=True,
            )

        return self.exit_run(
            results=deployments,
            key="deployments",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def get_aws_s3_bucket_sizes_in_account(
        self,
        execution_role_arn: Optional[str] = None,
        role_session_name: Optional[str] = None,
        exit_on_completion: bool = True,
    ):
        """Gets all of the AWS S3 bucket sizes in an AWS account

        generator=key: buckets, module_class: aws

        name: execution_role_arn, required: false, type: string
        name: role_session_name, required: false, type: string
        """
        if execution_role_arn is None:
            execution_role_arn = self.get_input("execution_role_arn", required=False)

        if role_session_name is None:
            role_session_name = self.get_input("role_session_name", required=False)

        self.logger.info("Getting S3 bucket sizes for all buckets in AWS account")

        s3 = self.get_aws_resource(
            service_name="s3",
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
        )

        buckets_iter = s3.buckets.pages()

        cloudwatch = self.get_aws_client(
            client_name="cloudwatch",
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
        )

        seconds_in_one_day = 86400

        def get_avg_for_bucket_storage_type(bn: str, st: str):
            datapoints = cloudwatch.get_metric_statistics(
                Namespace="AWS/S3",
                Dimensions=[
                    {"Name": "BucketName", "Value": bn},
                    {"Name": "StorageType", "Value": st},
                ],
                MetricName="BucketSizeBytes",
                StartTime=datetime.now() - timedelta(days=7),
                EndTime=datetime.now(),
                Period=seconds_in_one_day,
                Statistics=["Average"],
                Unit="Bytes",
            )["Datapoints"]

            for datapoint in datapoints:
                avg = datapoint.get("Average")
                if not utils.is_nothing(avg):
                    return avg

            return None

        buckets = utils.get_default_dict()
        for page in buckets_iter:
            for bucket in page:
                bucket_name = bucket.name
                self.logger.info(f"Getting the bucket size for {bucket_name} from Cloudwatch")

                for storage_type in self.S3_STORAGE_TYPES:
                    avg = get_avg_for_bucket_storage_type(bucket_name, storage_type)
                    if avg is not None:
                        self.logger.info(f"Average for {bucket_name} storage type {storage_type}: {avg}")
                        buckets[bucket_name][storage_type] = avg

        self.log_results(buckets, "s3 bucket sizes")

        return self.exit_run(
            results=buckets,
            key="buckets",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def merge_aws_s3_terraform_state_files(
        self,
        state_files: list[Optional[FilePath]] = None,
        s3_bucket: Optional[str] = None,
        fail_on_not_found: Optional[bool] = None,
        exit_on_completion: bool = True,
    ):
        """Merge AWS S3 Terraform state files

        generator=key: state, module_class: terraform

        name: state_files, required: true, json_encode: true
        name: s3_bucket, required: false, default: flipside-crypto-internal-tooling
        name: fail_on_not_found, required: false, default: false
        """

        if state_files is None:
            state_files = self.decode_input("state_files", required=False, decode_from_base64=False)

        if s3_bucket is None:
            s3_bucket = self.get_input("s3_bucket", required=False, default="flipside-crypto-internal-tooling")

        if fail_on_not_found is None:
            fail_on_not_found = self.get_input("fail_on_not_found", required=False, default=False, is_bool=True)

        self.logged_statement(
            f"Merging Terraform state files in AWS S3 bucket {s3_bucket}",
            identifiers=state_files,
        )

        state = {}

        for state_file in state_files:
            try:
                self._terraform_state_load_from_bucket(state=state, state_path=state_file, bucket=s3_bucket)
            except StateFileNotFoundError as exc:
                report = f"[StateFileNotFoundError] {exc}"

                if fail_on_not_found:
                    self.errors.append(report)
                else:
                    self.logger.warning(report)

        self.log_results(state, "merged state")

        return self.exit_run(
            results=state,
            key="state",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def get_aws_s3_terraform_state_outputs(
        self,
        state_key: Optional[str] = None,
        extra_state_keys: Optional[list[str]] = None,
        state_path: Optional[str] = None,
        s3_bucket: Optional[str] = None,
        fail_on_not_found: Optional[bool] = None,
        exit_on_completion: bool = True,
    ):
        """Gets Terraform state outputs from AWS S3

        generator=key: outputs, module_class: terraform

        name: state_key, required: false, default: context
        name: extra_state_keys, required: false, default: [], json_encode: true
        name: state_path, required: true, type: string
        name: s3_bucket, required: false, default: flipside-crypto-internal-tooling
        name: fail_on_not_found, required: false, default: false
        """

        if state_key is None:
            state_key = self.get_input("state_key", required=False, default="context")

        if extra_state_keys is None:
            extra_state_keys = self.decode_input(
                "extra_state_keys",
                required=False,
                default=[],
                decode_from_base64=False,
                allow_none=False,
            )

        if state_path is None:
            state_path = self.get_input("state_path", required=True)

        if s3_bucket is None:
            s3_bucket = self.get_input("s3_bucket", required=False, default="flipside-crypto-internal-tooling")

        if fail_on_not_found is None:
            fail_on_not_found = self.get_input("fail_on_not_found", required=False, default=False, is_bool=True)

        self.logger.info(f"Getting {state_key} from Terraform state {state_path} in AWS S3 bucket {s3_bucket}")

        state = {}

        try:
            self._terraform_state_load_from_bucket(state=state, state_path=state_path, bucket=s3_bucket)
        except StateFileNotFoundError as exc:
            report = f"[StateFileNotFoundError] {exc}"

            if fail_on_not_found:
                self.errors.append(report)
            else:
                self.logger.warning(report)

            return self.exit_run(
                key="output",
                encode_to_base64=True,
                format_json=False,
                exit_on_completion=exit_on_completion,
            )

        extra_state_keys = set(extra_state_keys)
        extra_state_keys.add(state_key)

        self.logger.info(f"State keys for state path {state_path}: {extra_state_keys}")

        outputs = {}
        reports = []

        state_file_outputs = state.get("outputs", {})
        if utils.is_nothing(state_file_outputs):
            report = f"[KeyError] State path {state_path} does not have outputs"
            if fail_on_not_found:
                self.errors.append(report)
            else:
                self.logger.warning(report)

            return self.exit_run(
                key="output",
                encode_to_base64=True,
                format_json=False,
                exit_on_completion=exit_on_completion,
            )

        for sk in extra_state_keys:
            self.logger.info(f"Getting output for state key {sk}")
            output_data = state_file_outputs.get(sk)
            if utils.is_nothing(output_data):
                reports.append(f"[KeyError] Failed to retrieve key {sk} from {state_path} outputs")
                continue

            output_value = output_data.get("value")
            if utils.is_nothing(output_value):
                reports.append(f"[KeyError] Failed to retrieve value from {state_path} output key {sk}")
                continue

            outputs[sk] = output_value

        if not utils.is_nothing(reports):
            for report in reports:
                if fail_on_not_found:
                    self.errors.append(report)
                else:
                    self.logger.warning(report)

        if extra_state_keys == {state_key}:
            self.logger.info(f"Returning the output of the singular state key {state_key}")
            outputs = outputs.get(state_key)

        self.log_results(outputs, "outputs")

        return self.exit_run(
            results=outputs,
            key="outputs",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def preprocess_aws_organization(
        self,
        aws_organization: Optional[dict[str, Any]] = None,
        domains: Optional[dict[str, str]] = None,
        google_organization: Optional[dict[str, Any]] = None,
        tags: Optional[dict[str, str]] = None,
        exit_on_completion: bool = True,
    ):
        """Preprocesses AWS organization data for use in Terraform

        generator=key: organization, module_class: aws

        name: aws_organization, required: true, json_encode: true, base64_encode: true
        name: domains, required: true, json_encode: true, base64_encode: true
        name: google_organization, required: false, json_encode: true, base64_encode: true
        name: tags, required: false, json_encode: true, base64_encode: true
        """
        if aws_organization is None:
            aws_organization = self.decode_input("aws_organization", required=True)

        if domains is None:
            domains = self.decode_input("domains", required=True)

        if google_organization is None:
            google_organization = self.decode_input("google_organization", required=False) or {}

        if tags is None:
            tags = self.decode_input("tags", required=False) or {}

        self.logger.info("Preprocessing AWS organization data")

        # Preprocess units
        units_processed = {}
        for unit_name, unit_data in aws_organization.get("units", {}).items():
            self.logger.info(f"Preprocessing unit {unit_name}")

            # Basic unit information
            unit_processed = {
                "name": unit_data.get("name", unit_name),
                "classifications": unit_data.get("classifications", []),
                "classification_type": unit_data.get("classification_type", ""),
                "environment": unit_data.get("environment", "global"),
                "domain": domains.get(unit_data.get("environment", "global"), domains.get("global")),
            }

            # Process classifications - only use what's provided, no defaults

            # Process classification type - only use what's provided, no defaults

            # Process environment - use provided value or default to global

            # Process domain - derive from environment

            # Calculate tags - filter out null values
            unit_tags = {}
            for k, v in {
                **tags,
                **{
                    "Name": unit_processed["name"],
                    "Classifications": " ".join(unit_processed["classifications"]),
                    "Type": unit_processed["classification_type"],
                    "Environment": unit_processed["environment"],
                },
            }.items():
                if v is not None and v != "":
                    unit_tags[k] = v

            unit_processed["tags"] = unit_tags
            units_processed[unit_name] = unit_processed

        # Get system accounts from root and unit accounts
        system_accounts = {}

        # Add root accounts
        for account_name, account_data in aws_organization.get("root", {}).get("accounts", {}).items():
            system_accounts[account_name] = account_data

        # Add unit accounts
        for unit_name, unit_data in aws_organization.get("units", {}).items():
            for account_name, account_data in unit_data.get("accounts", {}).items():
                # Add organizational_unit field to unit accounts
                system_accounts[account_name] = {**account_data, "organizational_unit": unit_name}

        # Get user accounts from Google organization
        user_accounts = google_organization.get("aws_user_accounts", {})

        # Normalize and preprocess all accounts
        aws_accounts = {}
        for account_name, account_data in {**system_accounts, **user_accounts}.items():
            self.logger.info(f"Preprocessing account {account_name}")

            # Basic account information
            account_processed = {"name": account_data.get("name", account_name)}

            # Ensure email is set - this is preprocessing, not defaulting
            account_name_normalized = account_processed["name"].replace(" ", "-").replace("_", "-").lower()
            account_processed["email"] = account_data.get("email", f"{account_name_normalized}@flipsidecrypto.com")

            # Control tower managed - use the provided value or default to true
            account_processed["control_tower_managed"] = account_data.get("control_tower_managed", True)

            # Normalize account name for keys - this is preprocessing, not defaulting
            account_processed["json_key"] = account_processed["name"].replace(" ", "").replace("-", "_")
            account_processed["network_name"] = account_processed["name"].replace(" ", "").replace("_", "-").lower()

            # Process classifications - only use what's provided, no defaults
            # For backward compatibility, check both classifications and classification_types
            classifications = []
            if "classifications" in account_data:
                classifications = account_data["classifications"]
            elif "classification_types" in account_data:
                classifications = account_data["classification_types"]
            elif account_processed["name"].startswith("User-"):
                classifications = ["testbed", "team"]

            account_processed["classifications"] = classifications

            # Process environment - derive from name or classifications if not provided
            environment = "global"
            if "environment" in account_data:
                environment = account_data["environment"]
            elif account_processed["name"].startswith("User-"):
                environment = "dev"
            elif "production" in classifications:
                environment = "prod"
            elif "staging" in classifications:
                environment = "stg"

            account_processed["environment"] = environment

            # Process domain - derive from environment
            account_processed["domain"] = domains.get(environment, domains.get("global"))

            # Process subdomain - derive from domain and name
            if "subdomain" in account_data:
                account_processed["subdomain"] = account_data["subdomain"]
            else:
                domain = account_processed["domain"]
                network_name = account_processed["network_name"]

                # If not stg/prod OR domain starts with network name, use domain as is
                if environment not in ["stg", "prod"] or domain.startswith(network_name):
                    account_processed["subdomain"] = domain
                else:
                    account_processed["subdomain"] = f"{network_name}.{domain}"

            # Process execution role name - only set for Control Tower accounts
            if "execution_role_name" in account_data:
                account_processed["execution_role_name"] = account_data["execution_role_name"]
            else:
                account_processed["execution_role_name"] = (
                    "AWSControlTowerExecution" if account_processed["control_tower_managed"] else ""
                )

            # Process additional metadata - use provided values or sensible defaults
            account_processed["spoke"] = account_data.get("spoke", False)
            account_processed["close_on_deletion"] = account_data.get("close_on_delete", False)

            # Process IAM user access to billing - only relevant for non-Control Tower accounts
            if "iam_user_access_to_billing" in account_data:
                account_processed["iam_user_access_to_billing"] = account_data["iam_user_access_to_billing"]
            else:
                account_processed["iam_user_access_to_billing"] = (
                    None if account_processed["control_tower_managed"] else "ALLOW"
                )

            # Calculate tags - filter out null values
            account_tags = {}
            for k, v in {
                **tags,
                **{
                    "Name": account_processed["name"],
                    "Environment": account_processed["environment"],
                    "Classifications": " ".join(account_processed["classifications"]),
                    "Spoke": "true" if account_processed["spoke"] else "false",
                },
            }.items():
                if v is not None and v != "":
                    account_tags[k] = v

            account_processed["tags"] = account_tags
            aws_accounts[account_name] = account_processed

        # Create unit classifications lookup
        unit_classifications_by_name = {}
        for unit_name, unit_data in units_processed.items():
            unit_classifications_by_name[unit_data["name"]] = unit_data["classifications"]

        # Create account classifications by name lookup
        accounts_by_classification = {}
        all_classifications = set()
        for account_data in aws_accounts.values():
            all_classifications.update(account_data["classifications"])

        for classification in all_classifications:
            if classification == "":
                continue

            accounts_by_classification[classification] = {}
            for account_name, account_data in aws_accounts.items():
                if classification in account_data["classifications"]:
                    accounts_by_classification[classification][account_name] = account_data

        # Create account by name lookup
        accounts_by_name = {}
        for account_name, account_data in aws_accounts.items():
            accounts_by_name[account_data["name"]] = account_data

        # Create account by email lookup
        accounts_by_email = {}
        for account_name, account_data in aws_accounts.items():
            accounts_by_email[account_data["email"]] = account_data

        # Create account by key lookup
        accounts_by_key = {}
        for account_name, account_data in aws_accounts.items():
            accounts_by_key[account_data["json_key"]] = account_data

        # Create the final context object
        organization = {
            "accounts": aws_accounts,
            "units": units_processed,
            "unit_classifications_by_name": unit_classifications_by_name,
            "accounts_by_classification": accounts_by_classification,
            "accounts_by_name": accounts_by_name,
            "accounts_by_email": accounts_by_email,
            "accounts_by_key": accounts_by_key,
            "organization": aws_organization,
        }

        return self.exit_run(
            results=organization,
            key="organization",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def classify_aws_accounts(
        self,
        aws_accounts: Optional[dict[str, Any]] = None,
        suffix: Optional[str] = None,
        exit_on_completion: bool = True,
    ):
        """Classifies AWS accounts

        generator=key: classifications, module_class: aws

        name: aws_accounts, required: true, json_encode: true, base64_encode: true
        name: suffix, required: false, type: string
        """
        if aws_accounts is None:
            aws_accounts = self.decode_input("aws_accounts", required=True)

        if suffix is None:
            suffix = self.get_input("suffix", required=False)

        self.logger.info("Classifying AWS accounts")

        classified_accounts = defaultdict(list)

        accounts_suffix = f"_accounts{suffix}" if suffix else "_accounts"

        for account_key, account_data in aws_accounts.items():
            self.logger.info(f"Classifying AWS account {account_key}")

            for classification in account_data["classifications"]:
                if not classification or classification == "accounts":
                    self.logger.warning(f"Skipping invalid classification '{classification}'")
                    continue

                classified_accounts[f"{classification}{accounts_suffix}"].append(account_key)

        return self.exit_run(
            results=classified_accounts,
            key="classifications",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def get_google_organization_id(
        self,
        service_account_file: Optional[Mapping] = None,
        exit_on_completion: bool = True,
    ):
        """
        Retrieves the organization ID associated with the authenticated service account.

        generator=key: organization_id, plaintext_output: true, module_class: google

        name: service_account_file, required: false, json_encode: true, base64_encode: true
        """

        # Decode inputs
        service_account_file = service_account_file or self.decode_input("service_account_file", required=False)
        google_client = self.get_google_client(service_account_file=service_account_file)

        # Initialize Cloud Resource Manager
        cloud_resource_manager = google_client.get_service("cloudresourcemanager", "v1")

        try:
            self.logger.info("Retrieving organization ID for the service account...")
            request = cloud_resource_manager.organizations().search(body={})
            response = request.execute()

            if "organizations" not in response or not response["organizations"]:
                raise ValueError("No organizations found for the authenticated service account.")

            organization_id = response["organizations"][0]["name"].split("/")[-1]
            self.logger.info(f"Retrieved organization ID: {organization_id}")

        except googleapiclient.errors.HttpError as http_err:
            self.logger.error(f"HTTP error while retrieving organization ID: {http_err}")
            raise
        except ssl.SSLError as ssl_err:
            self.logger.error(f"SSL error while retrieving organization ID: {ssl_err}")
            raise
        except ConnectionError as conn_err:
            self.logger.error(f"Connection error while retrieving organization ID: {conn_err}")
            raise
        except Exception as generic_err:
            self.logger.error(f"Unexpected error while retrieving organization ID: {generic_err}")
            raise

        # Return organization ID in plaintext
        return self.exit_run(
            results=organization_id,
            format_results=False,
            key="organization_id",
            exit_on_completion=exit_on_completion,
        )

    def get_google_billing_account_for_project(
        self,
        project_id: Optional[str] = None,
        service_account_file: Optional[Mapping] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[int] = None,
        exit_on_completion: bool = True,
    ):
        """
        Retrieves the billing account associated with a specific GCP project.

        generator=key: billing_account_id, plaintext_output: true, module_class: google

        name: project_id, required: true, type: string
        name: service_account_file, required: false, json_encode: true, base64_encode: true
        name: max_retries, required: false, type: integer, default: 3
        name: retry_delay, required: false, type: integer, default: 2
        """

        # Decode inputs
        project_id = project_id or self.get_input("project_id", required=True)
        service_account_file = service_account_file or self.decode_input("service_account_file", required=False)
        max_retries = max_retries or self.get_input("max_retries", required=False, default=3, is_integer=True)
        retry_delay = retry_delay or self.get_input("retry_delay", required=False, default=2, is_integer=True)

        google_client = self.get_google_client(service_account_file=service_account_file)

        # Get Billing API Service
        billing = google_client.get_service("cloudbilling", "v1")

        # Initialize variables for error tracking
        http_err = None

        # Retrieve the billing account for the project with retries
        attempt = 0
        while attempt < max_retries:
            try:
                self.logger.info(
                    f"Attempt {attempt + 1}/{max_retries}: Retrieving billing account for project '{project_id}'..."
                )
                billing_info = billing.projects().getBillingInfo(name=f"projects/{project_id}").execute()

                # Extract the billing account ID, if it exists
                billing_account_id = billing_info.get("billingAccountName", "").split("/")[-1] or None
                if billing_account_id:
                    self.logger.info(f"Retrieved billing account '{billing_account_id}' for project '{project_id}'.")
                else:
                    self.logger.info(f"No billing account found for project '{project_id}'.")

                return self.exit_run(
                    results=billing_account_id,
                    format_results=False,
                    key="billing_account_id",
                    exit_on_completion=exit_on_completion,
                )

            except googleapiclient.errors.HttpError as err:
                http_err = err
                if err.resp.status == 429:  # Rate-limited
                    retry_after = int(err.resp.get("Retry-After", retry_delay))
                    self.logger.warning(
                        f"Rate-limited on attempt {attempt + 1}/{max_retries} for project '{project_id}'. "
                        f"Retrying after {retry_after} seconds."
                    )
                    time.sleep(retry_after)
                elif err.resp.status == 404:
                    self.logger.info(f"Project '{project_id}' not found or does not have billing information.")
                    return None
                else:
                    self.logger.error(
                        f"HTTP error on attempt {attempt + 1}/{max_retries} for project '{project_id}': {err}"
                    )
                    raise
            except ssl.SSLError as ssl_err:
                self.logger.error(
                    f"SSL error on attempt {attempt + 1}/{max_retries} for project '{project_id}': {ssl_err}"
                )
                raise
            except (ConnectionError, IncompleteRead) as conn_err:
                self.logger.warning(
                    f"Connection error on attempt {attempt + 1}/{max_retries} for project '{project_id}': {conn_err}"
                )
            except Exception as generic_err:
                self.logger.error(
                    f"Unexpected error on attempt {attempt + 1}/{max_retries} for project '{project_id}': {generic_err}"
                )
                raise

            attempt += 1

        # If retries exhausted and last error was rate-limiting, raise RequestRateLimitedError
        if http_err and http_err.resp.status == 429:
            self.logger.error(f"Rate-limiting exceeded for project '{project_id}' after {max_retries} attempts.")
            raise RequestRateLimitedError(
                response=http_err.resp,
                retry_after=retry_delay,
                additional_information=f"Rate-limited for project '{project_id}' after {max_retries} attempts.",
            )

        # If retries exhausted and the issue is not rate-limiting, raise a generic RuntimeError
        self.logger.error(
            f"Failed to retrieve billing account for project '{project_id}' after {max_retries} attempts."
        )
        raise RuntimeError(
            f"Failed to retrieve billing account for project '{project_id}' after {max_retries} attempts."
        )

    def get_google_billing_accounts(
        self,
        service_account_file: Optional[Mapping] = None,
        exit_on_completion: bool = True,
    ):
        """
        Retrieves all billing accounts for the authenticated service account.

        generator=key: billing_accounts, module_class: google

        name: service_account_file, required: false, json_encode: true, base64_encode: true
        """

        service_account_file = service_account_file or self.decode_input("service_account_file", required=False)

        # Initialize Google Client
        google_client = self.get_google_client(service_account_file=service_account_file)
        billing = google_client.get_service("cloudbilling", "v1")

        billing_accounts = {}

        # Fetch billing accounts
        try:
            self.logger.info("Retrieving billing accounts...")
            request = billing.billingAccounts().list()
            while request:
                response = request.execute()
                for account in response.get("billingAccounts", []):
                    billing_account_id = account.get("name").split("/")[-1]
                    billing_accounts[billing_account_id] = account
                request = billing.billingAccounts().list_next(previous_request=request, previous_response=response)

            self.logger.info(f"Retrieved {len(billing_accounts)} billing accounts.")
        except googleapiclient.errors.HttpError as http_err:
            self.logger.error(f"HTTP error while retrieving billing accounts: {http_err}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error while retrieving billing accounts: {e}")
            raise

        return self.exit_run(
            results=billing_accounts,
            key="billing_accounts",
            format_results=True,
            exit_on_completion=exit_on_completion,
        )

    def get_storage_buckets_for_google_project(
        self,
        project_id: str,
        service_account_file: Optional[Mapping] = None,
        exit_on_completion: bool = True,
    ) -> dict[str, Any]:
        """
        Retrieves storage buckets for a given Google Cloud project, keyed by bucket name.

        generator=key: storage_buckets, module_class: google

        name: project_id, required: true, type: string
        name: service_account_file, required: false, json_encode: true, base64_encode: true
        """

        service_account_file = service_account_file or self.decode_input("service_account_file", required=False)

        google_client = self.get_google_client(service_account_file=service_account_file)
        storage_client = google_client.get_service("storage", "v1")

        buckets_map = {}
        try:
            self.logger.info(f"Retrieving storage buckets for project '{project_id}'...")
            request = storage_client.buckets().list(project=project_id)
            while request:
                response = request.execute()
                for bucket in response.get("items", []):
                    bucket_name = bucket.get("name")
                    if bucket_name:
                        buckets_map[bucket_name] = bucket
                request = storage_client.buckets().list_next(previous_request=request, previous_response=response)
            self.logger.info(f"Found {len(buckets_map)} storage buckets for project '{project_id}'.")
        except Exception as e:
            self.logger.warning(f"Error retrieving storage buckets for project '{project_id}': {e}")

        return self.exit_run(
            results=buckets_map,
            key="storage_buckets",
            format_results=True,
            exit_on_completion=exit_on_completion,
        )

    def get_gke_clusters_for_google_project(
        self,
        project_id: str,
        service_account_file: Optional[Mapping] = None,
        exit_on_completion: bool = True,
    ) -> dict[str, Any]:
        """
        Retrieves GKE clusters for a given Google Cloud project, keyed by cluster names.

        generator=key: gke_clusters, module_class: google

        name: project_id, required: true, type: string
        name: service_account_file, required: false, json_encode: true, base64_encode: true
        """

        service_account_file = service_account_file or self.decode_input("service_account_file", required=False)

        google_client = self.get_google_client(service_account_file=service_account_file)
        container_client = google_client.get_service("container", "v1")

        clusters_map = {}
        try:
            self.logger.info(f"Retrieving GKE clusters for project '{project_id}'...")
            parent = f"projects/{project_id}/locations/-"
            clusters = (
                container_client.projects().locations().clusters().list(parent=parent).execute().get("clusters", [])
            )
            for cluster in clusters:
                cluster_name = cluster.get("name")
                if cluster_name:
                    clusters_map[cluster_name] = cluster
            self.logger.info(f"Found {len(clusters_map)} GKE clusters for project '{project_id}'.")
        except Exception as e:
            self.logger.warning(f"Error retrieving GKE clusters for project '{project_id}': {e}")

        return self.exit_run(
            results=clusters_map,
            key="gke_clusters",
            format_results=True,
            exit_on_completion=exit_on_completion,
        )

    def get_compute_instances_for_google_project(
        self,
        project_id: str,
        service_account_file: Optional[Mapping] = None,
        exit_on_completion: bool = True,
    ) -> dict[str, Any]:
        """
        Retrieves Compute Engine instances for a given Google Cloud project, keyed by instance names.

        generator=key: compute_instances, module_class: google

        name: project_id, required: true, type: string
        name: service_account_file, required: false, json_encode: true, base64_encode: true
        """

        service_account_file = service_account_file or self.decode_input("service_account_file", required=False)

        google_client = self.get_google_client(service_account_file=service_account_file)
        compute_client = google_client.get_service("compute", "v1")

        instances_map = {}
        try:
            self.logger.info(f"Retrieving Compute Engine instances for project '{project_id}'...")
            zones = compute_client.zones().list(project=project_id).execute().get("items", [])
            for zone in zones:
                zone_name = zone.get("name")
                if zone_name:
                    instances = (
                        compute_client.instances().list(project=project_id, zone=zone_name).execute().get("items", [])
                    )
                    for instance in instances:
                        instance_name = instance.get("name")
                        if instance_name:
                            instances_map[instance_name] = instance
            self.logger.info(f"Found {len(instances_map)} Compute Engine instances for project '{project_id}'.")
        except Exception as e:
            self.logger.warning(f"Error retrieving Compute Engine instances for project '{project_id}': {e}")

        return self.exit_run(
            results=instances_map,
            key="compute_instances",
            format_results=True,
            exit_on_completion=exit_on_completion,
        )

    def get_service_accounts_for_google_project(
        self,
        project_id: str,
        service_account_file: Optional[Mapping] = None,
        exit_on_completion: bool = True,
    ) -> dict[str, Any]:
        """
        Retrieves IAM service accounts for a given Google Cloud project, keyed by service account email.

        generator=key: service_accounts, module_class: google

        name: project_id, required: true, type: string
        name: service_account_file, required: false, json_encode: true, base64_encode: true
        """

        service_account_file = service_account_file or self.decode_input("service_account_file", required=False)

        google_client = self.get_google_client(service_account_file=service_account_file)
        iam_client = google_client.get_service("iam", "v1")

        service_accounts_map = {}
        try:
            self.logger.info(f"Retrieving IAM service accounts for project '{project_id}'...")
            request = iam_client.projects().serviceAccounts().list(name=f"projects/{project_id}")
            while request:
                response = request.execute()
                for account in response.get("accounts", []):
                    account_email = account.get("email")
                    if account_email:
                        service_accounts_map[account_email] = account
                request = (
                    iam_client.projects()
                    .serviceAccounts()
                    .list_next(previous_request=request, previous_response=response)
                )
            self.logger.info(f"Found {len(service_accounts_map)} IAM service accounts for project '{project_id}'.")
        except Exception as e:
            self.logger.warning(f"Error retrieving IAM service accounts for project '{project_id}': {e}")

        return self.exit_run(
            results=service_accounts_map,
            key="service_accounts",
            format_results=True,
            exit_on_completion=exit_on_completion,
        )

    def get_users_for_google_project(
        self,
        project_id: str,
        service_account_file: Optional[Mapping] = None,
        exit_on_completion: bool = True,
    ) -> dict[str, Any]:
        """
        Retrieves users (non-service accounts) for a given Google Cloud project, keyed by user email.

        generator=key: users, module_class: google

        name: project_id, required: true, type: string
        name: service_account_file, required: false, json_encode: true, base64_encode: true
        """

        service_account_file = service_account_file or self.decode_input("service_account_file", required=False)

        google_client = self.get_google_client(service_account_file=service_account_file)
        cloud_resource_manager = google_client.get_service("cloudresourcemanager", "v1")

        users_map = {}
        try:
            self.logger.info(f"Retrieving users for project '{project_id}'...")
            request = cloud_resource_manager.projects().getIamPolicy(resource=project_id, body={})
            response = request.execute()

            bindings = response.get("bindings", [])
            for binding in bindings:
                role = binding.get("role", "")
                members = binding.get("members", [])
                for member in members:
                    if member.startswith("user:"):
                        user_email = member.split("user:")[1]
                        if user_email not in users_map:
                            users_map[user_email] = {"roles": []}
                        users_map[user_email]["roles"].append(role)

            self.logger.info(f"Found {len(users_map)} users for project '{project_id}'.")
        except Exception as e:
            self.logger.warning(f"Error retrieving users for project '{project_id}': {e}")

        return self.exit_run(
            results=users_map,
            key="users",
            format_results=True,
            exit_on_completion=exit_on_completion,
        )

    def get_sql_instances_for_google_project(
        self,
        project_id: str,
        service_account_file: Optional[Mapping] = None,
        exit_on_completion: bool = True,
    ):
        """
        Retrieves Cloud SQL instances for a given Google Cloud project, keyed by instance name.

        generator=key: sql_instances, module_class: google

        name: project_id, required: true, type: string
        name: service_account_file, required: false, json_encode: true, base64_encode: true
        """

        service_account_file = service_account_file or self.decode_input("service_account_file", required=False)

        google_client = self.get_google_client(service_account_file=service_account_file)
        sqladmin_client = google_client.get_service("sqladmin", "v1")

        sql_instances_map = {}
        try:
            self.logger.info(f"Retrieving Cloud SQL instances for project '{project_id}'...")
            request = sqladmin_client.instances().list(project=project_id)
            while request:
                response = request.execute()
                for instance in response.get("items", []):
                    instance_name = instance.get("name")
                    if instance_name:
                        sql_instances_map[instance_name] = instance
                request = sqladmin_client.instances().list_next(previous_request=request, previous_response=response)
            self.logger.info(f"Found {len(sql_instances_map)} Cloud SQL instances for project '{project_id}'.")
        except Exception as e:
            self.logger.warning(f"Error retrieving Cloud SQL instances for project '{project_id}': {e}")

        return self.exit_run(
            results=sql_instances_map,
            key="sql_instances",
            format_results=True,
            exit_on_completion=exit_on_completion,
        )

    def get_pubsub_queues_for_google_project(
        self,
        project_id: str,
        service_account_file: Optional[Mapping] = None,
        exit_on_completion: bool = True,
    ):
        """
        Retrieves Pub/Sub topics and subscriptions for a given Google Cloud project, keyed by topic name.

        generator=key: pubsub_queues, module_class: google

        name: project_id, required: true, type: string
        name: service_account_file, required: false, json_encode: true, base64_encode: true
        """

        service_account_file = service_account_file or self.decode_input("service_account_file", required=False)

        google_client = self.get_google_client(service_account_file=service_account_file)
        pubsub_client = google_client.get_service("pubsub", "v1")

        pubsub_queues_map = {}
        try:
            self.logger.info(f"Retrieving Pub/Sub topics for project '{project_id}'...")
            request = pubsub_client.projects().topics().list(project=f"projects/{project_id}")
            while request:
                response = request.execute()
                for topic in response.get("topics", []):
                    topic_name = topic.get("name")
                    if topic_name:
                        pubsub_queues_map[topic_name] = {"type": "topic", "details": topic}
                request = (
                    pubsub_client.projects().topics().list_next(previous_request=request, previous_response=response)
                )

            self.logger.info(f"Retrieving Pub/Sub subscriptions for project '{project_id}'...")
            request = pubsub_client.projects().subscriptions().list(project=f"projects/{project_id}")
            while request:
                response = request.execute()
                for subscription in response.get("subscriptions", []):
                    subscription_name = subscription.get("name")
                    if subscription_name:
                        pubsub_queues_map[subscription_name] = {"type": "subscription", "details": subscription}
                request = (
                    pubsub_client.projects()
                    .subscriptions()
                    .list_next(previous_request=request, previous_response=response)
                )

            self.logger.info(
                f"Found {len(pubsub_queues_map)} Pub/Sub topics and subscriptions for project '{project_id}'."
            )
        except Exception as e:
            self.logger.warning(f"Error retrieving Pub/Sub topics or subscriptions for project '{project_id}': {e}")

        return self.exit_run(
            results=pubsub_queues_map,
            key="pubsub_queues",
            format_results=True,
            exit_on_completion=exit_on_completion,
        )

    def get_enabled_apis_for_google_project(
        self,
        project_id: Optional[str] = None,
        service_account_file: Optional[Mapping] = None,
        exit_on_completion: bool = True,
    ) -> list[dict]:
        """
        Retrieves the list of enabled APIs for a Google Cloud project.

        generator=module_class: google, key: enabled_apis

        name: project_id, required: true, type: string
        name: service_account_file, required: false, json_encode: true, base64_encode: true
        """

        # Decode inputs
        project_id = project_id or self.get_input("project_id", required=True)
        service_account_file = service_account_file or self.decode_input("service_account_file", required=False)

        # Initialize Google client and service
        google_client = self.get_google_client(service_account_file=service_account_file)
        service_usage = google_client.get_service("serviceusage", "v1")

        # Fetch enabled APIs
        try:
            self.logger.info(f"Fetching enabled APIs for project '{project_id}'...")
            request = service_usage.services().list(parent=f"projects/{project_id}", filter="state:ENABLED")
            enabled_apis = []
            while request is not None:
                response = request.execute()
                enabled_apis.extend(response.get("services", []))
                request = service_usage.services().list_next(previous_request=request, previous_response=response)

            self.logger.info(f"Retrieved {len(enabled_apis)} enabled APIs for project '{project_id}'.")
            return self.exit_run(
                results=enabled_apis,
                key="enabled_apis",
                format_results=True,
                exit_on_completion=exit_on_completion,
            )
        except Exception as e:
            self.logger.error(f"Failed to fetch enabled APIs for project '{project_id}': {e}")
            raise

    def _check_org_level_billing(self, google_client, project_id: str) -> Optional[bool]:
        """
        Check project billing status at organization level.
        Returns:
            - True if billing enabled (not empty)
            - False if billing disabled
            - None if can't determine

        # NOPARSE
        """

        try:
            cloudbilling = google_client.get_service("cloudbilling", "v1")
            billing_info = cloudbilling.projects().getBillingInfo(name=f"projects/{project_id}").execute()
            if billing_info.get("billingEnabled"):
                self.logger.info("Project has billing enabled, indicating potential resource usage.")
                return True
            return False
        except Exception as e:
            self.logger.debug(f"Could not check billing info: {e}")
            return None

    def _check_org_level_iam(
        self, google_client, project_id: str, current_service_account_email: str
    ) -> Optional[bool]:
        """
        Check IAM bindings at organization level.
        Returns:
            - True if non-exempt bindings found (not empty)
            - False if only exempt bindings or no bindings
            - None if can't determine

        # NOPARSE
        """
        try:
            resource_manager = google_client.get_service("cloudresourcemanager", "v3")
            policy_request = resource_manager.projects().getIamPolicy(
                resource=f"projects/{project_id}",
                body={"options": {"requestedPolicyVersion": 3, "includeInheritedRoles": True}},
            )
            policy = policy_request.execute()

            bindings = policy.get("bindings", [])
            if not bindings:
                return False

            for binding in bindings:
                role = binding.get("role", "Unknown role")
                members = binding.get("members", [])

                for member in members:
                    if not (
                        current_service_account_email and member == f"serviceAccount:{current_service_account_email}"
                    ):
                        self.logger.info(f"Found non-exempt IAM binding - Role: {role}, Member: {member}")
                        return True

            return False
        except Exception as e:
            self.logger.debug(f"Could not check IAM bindings: {e}")
            return None

    def _check_org_level_logs(self, google_client, project_id: str, organization_id: str) -> Optional[bool]:
        """
        Check organization-level audit logs.
        Returns:
            - True if activity found (not empty)
            - False if no activity
            - None if can't determine

        # NOPARSE
        """
        try:
            logging_service = google_client.get_service("logging", "v2")
            thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat() + "Z"

            org_activity_filter = f"""
                resource.labels.project_id="{project_id}"
                AND timestamp >= "{thirty_days_ago}"
                AND NOT protoPayload.methodName:("get" OR "list")
                AND (
                    resource.type=("gce_network" OR "gce_firewall" OR "gce_route" OR "dns_managed_zone")
                    OR protoPayload.serviceName=("compute.googleapis.com" OR "container.googleapis.com" 
                       OR "cloudresourcemanager.googleapis.com")
                    OR protoPayload.methodName:("CreateService" OR "DeleteService" OR "UpdateService")
                    OR severity=("ERROR" OR "CRITICAL")
                )
            """

            request = logging_service.entries().list(
                body={
                    "resourceNames": [f"organizations/{organization_id}"],
                    "filter": org_activity_filter,
                    "pageSize": 10,
                }
            )

            response = request.execute()
            if response.get("entries"):
                self._log_entries(response.get("entries")[:5])
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error checking organization-level logs: {str(e)}")
            return None

    def _get_checkable_resources(self) -> dict:
        """
        Returns mapping of APIs to their resource types and usage indicators.

        The mapping includes:
        - name: Human-readable service name
        - indicates_usage: Whether enabling this API strongly indicates project usage
        - enables_checks: List of resource types to check using Cloud Asset API

        # NOPARSE
        """

        return {
            # Core Infrastructure APIs
            "compute.googleapis.com": {
                "name": "Compute Engine",
                "indicates_usage": True,
                "enables_checks": [
                    "compute.googleapis.com/Address",
                    "compute.googleapis.com/Autoscaler",
                    "compute.googleapis.com/BackendService",
                    "compute.googleapis.com/Disk",
                    "compute.googleapis.com/Firewall",
                    "compute.googleapis.com/ForwardingRule",
                    "compute.googleapis.com/HealthCheck",
                    "compute.googleapis.com/Instance",
                    "compute.googleapis.com/InstanceGroup",
                    "compute.googleapis.com/InstanceGroupManager",
                    "compute.googleapis.com/InstanceTemplate",
                    "compute.googleapis.com/Network",
                    "compute.googleapis.com/Router",
                    "compute.googleapis.com/Snapshot",
                    "compute.googleapis.com/SslCertificate",
                    "compute.googleapis.com/Subnetwork",
                    "compute.googleapis.com/TargetHttpProxy",
                    "compute.googleapis.com/TargetHttpsProxy",
                    "compute.googleapis.com/TargetPool",
                    "compute.googleapis.com/UrlMap",
                ],
            },
            "container.googleapis.com": {
                "name": "Google Kubernetes Engine",
                "indicates_usage": True,
                "enables_checks": ["container.googleapis.com/Cluster", "container.googleapis.com/NodePool"],
            },
            # Serverless APIs
            "cloudfunctions.googleapis.com": {
                "name": "Cloud Functions",
                "indicates_usage": True,
                "enables_checks": ["cloudfunctions.googleapis.com/CloudFunction"],
            },
            "run.googleapis.com": {
                "name": "Cloud Run",
                "indicates_usage": True,
                "enables_checks": ["run.googleapis.com/Service", "run.googleapis.com/Revision"],
            },
            "workflows.googleapis.com": {
                "name": "Cloud Workflows",
                "indicates_usage": True,
                "enables_checks": ["workflows.googleapis.com/Workflow"],
            },
            # Data Storage APIs
            "sqladmin.googleapis.com": {
                "name": "Cloud SQL",
                "indicates_usage": True,
                "enables_checks": ["sqladmin.googleapis.com/Instance"],
            },
            "bigquery.googleapis.com": {
                "name": "BigQuery",
                "indicates_usage": False,  # Often enabled by default
                "enables_checks": [
                    "bigquery.googleapis.com/Dataset",
                    "bigquery.googleapis.com/Table",
                    "bigquery.googleapis.com/Model",
                ],
            },
            "storage.googleapis.com": {
                "name": "Cloud Storage",
                "indicates_usage": False,  # Often enabled by default
                "enables_checks": ["storage.googleapis.com/Bucket"],
            },
            "redis.googleapis.com": {
                "name": "Redis",
                "indicates_usage": True,
                "enables_checks": ["redis.googleapis.com/Instance"],
            },
            "memcache.googleapis.com": {
                "name": "Memorystore for Memcached",
                "indicates_usage": True,
                "enables_checks": ["memcache.googleapis.com/Instance"],
            },
            "filestore.googleapis.com": {
                "name": "Filestore",
                "indicates_usage": True,
                "enables_checks": ["file.googleapis.com/Instance"],
            },
            # Security and Identity APIs
            "secretmanager.googleapis.com": {
                "name": "Secret Manager",
                "indicates_usage": True,
                "enables_checks": ["secretmanager.googleapis.com/Secret"],
            },
            "cloudkms.googleapis.com": {
                "name": "Cloud KMS",
                "indicates_usage": True,
                "enables_checks": ["cloudkms.googleapis.com/CryptoKey", "cloudkms.googleapis.com/KeyRing"],
            },
            "iam.googleapis.com": {
                "name": "Identity and Access Management",
                "indicates_usage": False,  # Core service
                "enables_checks": [
                    "iam.googleapis.com/Role",
                    "iam.googleapis.com/ServiceAccount",
                    "iam.googleapis.com/ServiceAccountKey",
                ],
            },
            # DevOps and Artifacts APIs
            "artifactregistry.googleapis.com": {
                "name": "Artifact Registry",
                "indicates_usage": True,
                "enables_checks": [
                    "artifactregistry.googleapis.com/Repository",
                    "artifactregistry.googleapis.com/DockerImage",
                ],
            },
            "cloudbuild.googleapis.com": {
                "name": "Cloud Build",
                "indicates_usage": True,
                "enables_checks": ["cloudbuild.googleapis.com/Trigger", "cloudbuild.googleapis.com/WorkerPool"],
            },
            # Networking APIs
            "servicenetworking.googleapis.com": {
                "name": "Service Networking",
                "indicates_usage": True,
                "enables_checks": ["servicenetworking.googleapis.com/Connection"],
            },
            "vpcaccess.googleapis.com": {
                "name": "VPC Access",
                "indicates_usage": True,
                "enables_checks": ["vpcaccess.googleapis.com/Connector"],
            },
            "dns.googleapis.com": {
                "name": "Cloud DNS",
                "indicates_usage": True,
                "enables_checks": ["dns.googleapis.com/ManagedZone", "dns.googleapis.com/Policy"],
            },
            "networksecurity.googleapis.com": {
                "name": "Network Security",
                "indicates_usage": True,
                "enables_checks": [
                    "networksecurity.googleapis.com/ClientTlsPolicy",
                    "networksecurity.googleapis.com/ServerTlsPolicy",
                ],
            },
            # Messaging and Task Management APIs
            "pubsub.googleapis.com": {
                "name": "Pub/Sub",
                "indicates_usage": True,
                "enables_checks": ["pubsub.googleapis.com/Topic", "pubsub.googleapis.com/Subscription"],
            },
            "cloudscheduler.googleapis.com": {
                "name": "Cloud Scheduler",
                "indicates_usage": True,
                "enables_checks": ["cloudscheduler.googleapis.com/Job"],
            },
            "cloudtasks.googleapis.com": {
                "name": "Cloud Tasks",
                "indicates_usage": True,
                "enables_checks": ["cloudtasks.googleapis.com/Queue"],
            },
            # Data Processing APIs
            "dataflow.googleapis.com": {
                "name": "Dataflow",
                "indicates_usage": True,
                "enables_checks": ["dataflow.googleapis.com/Job", "dataflow.googleapis.com/Snapshot"],
            },
            "dataproc.googleapis.com": {
                "name": "Dataproc",
                "indicates_usage": True,
                "enables_checks": ["dataproc.googleapis.com/Cluster", "dataproc.googleapis.com/WorkflowTemplate"],
            },
            # Monitoring and Logging APIs
            "monitoring.googleapis.com": {
                "name": "Cloud Monitoring",
                "indicates_usage": False,  # Often auto-enabled
                "enables_checks": [
                    "monitoring.googleapis.com/AlertPolicy",
                    "monitoring.googleapis.com/Group",
                    "monitoring.googleapis.com/NotificationChannel",
                ],
            },
            "logging.googleapis.com": {
                "name": "Cloud Logging",
                "indicates_usage": False,  # Often auto-enabled
                "enables_checks": [
                    "logging.googleapis.com/LogMetric",
                    "logging.googleapis.com/LogSink",
                    "logging.googleapis.com/LogBucket",
                ],
            },
            # Core Management APIs
            "cloudapis.googleapis.com": {
                "name": "Google Cloud APIs",
                "indicates_usage": False,  # Core service
                "enables_checks": ["cloudapis.googleapis.com/ApiKey"],
            },
            "serviceusage.googleapis.com": {
                "name": "Service Usage",
                "indicates_usage": False,  # Core service
                "enables_checks": [],
            },
        }

    def _convert_to_log_resource_types(self, cloud_asset_types: list) -> list:
        """Convert Cloud Asset resource types to Log resource types.

        # NOPARSE"""
        log_resource_types = []
        for resource_type in cloud_asset_types:
            if "compute.googleapis.com/" in resource_type:
                log_type = resource_type.split("/")[-1].lower()
                log_resource_types.append(f"gce_{log_type}")
            elif "container.googleapis.com/" in resource_type:
                log_type = resource_type.split("/")[-1].lower()
                log_resource_types.append(f"k8s_{log_type}")
            elif "cloudfunctions.googleapis.com/" in resource_type:
                log_resource_types.append("cloudfunctions_function")
            elif "run.googleapis.com/" in resource_type:
                log_resource_types.append("cloud_run_revision")
            elif "bigquery.googleapis.com/" in resource_type:
                log_type = resource_type.split("/")[-1].lower()
                log_resource_types.append(f"bigquery_{log_type}")
            elif "storage.googleapis.com/" in resource_type:
                log_resource_types.append("gcs_bucket")
            else:
                log_type = resource_type.split("/")[-1].lower()
                log_resource_types.append(log_type)
        return log_resource_types

    def _log_entries(self, entries: list) -> None:
        """Helper to consistently log entry details.

        # NOPARSE"""
        for entry in entries:
            resource_type = entry.get("resource", {}).get("type", "unknown resource type")
            timestamp = entry.get("timestamp", "no timestamp")
            severity = entry.get("severity", "unknown severity")
            service = entry.get("protoPayload", {}).get("serviceName", "unknown service")
            operation = entry.get("protoPayload", {}).get("methodName", "unknown method")

            self.logger.info(
                f"  Entry:\n"
                f"    Timestamp: {timestamp}\n"
                f"    Resource Type: {resource_type}\n"
                f"    Service: {service}\n"
                f"    Severity: {severity}\n"
                f"    Operation: {operation}"
            )

    def _check_project_resources(
        self, google_client, project_id: str, enabled_api_names: set, checkable_resource_types: list
    ) -> Optional[bool]:
        """
        Check for project-level resources using Cloud Asset API.
        Returns:
            - True if resources found (not empty)
            - False if no resources found
            - None if can't determine

        # NOPARSE
        """
        if "cloudasset.googleapis.com" not in enabled_api_names or not checkable_resource_types:
            return None

        try:
            asset_service = google_client.get_service("cloudasset", "v1")
            parent = f"projects/{project_id}"

            request = asset_service.assets().list(
                parent=parent, contentType="RESOURCE", assetTypes=checkable_resource_types, pageSize=10
            )
            response = request.execute()
            if response.get("assets"):
                self.logger.info("Found active resources using Cloud Asset API. Details:")
                for asset in response.get("assets", [])[:5]:
                    self.logger.info(f"  Resource Type: {asset.get('assetType')}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error checking Cloud Asset inventory: {str(e)}")
            return None

    def _check_project_logs(self, google_client, project_id: str, checkable_resource_types: list) -> Optional[bool]:
        """
        Check project-level logs for activity.
        Returns:
            - True if activity found (not empty)
            - False if no activity found
            - None if can't determine

        # NOPARSE
        """
        try:
            logging_service = google_client.get_service("logging", "v2")
            thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat() + "Z"

            log_resource_types = self._convert_to_log_resource_types(checkable_resource_types)
            log_filter = f"""
                timestamp >= "{thirty_days_ago}"
                AND NOT protoPayload.methodName:("get" OR "list")
                AND NOT resource.type="project"
                AND ({' OR '.join(f'resource.type="{t}"' for t in log_resource_types)})
            """

            self.logger.info(f"Using log filter:\n{log_filter}")

            project_request = logging_service.entries().list(
                body={
                    "resourceNames": [f"projects/{project_id}"],
                    "filter": log_filter,
                    "pageSize": 10,
                }
            )

            project_response = project_request.execute()
            if project_response.get("entries"):
                self._log_entries(project_response.get("entries")[:5])
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error checking project-level logs: {str(e)}")
            return None

    def is_google_project_empty(
        self,
        project_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        service_account_file: Optional[Mapping] = None,
        exit_on_completion: bool = True,
    ) -> bool:
        """
        Checks if a Google Cloud project is empty by querying organization-level logs for activity.

        generator=module_class: google, key: is_empty, plaintext_output: true

        name: project_id, required: true, type: string
        name: organization_id, required: false, type: string
        name: service_account_file, required: false, json_encode: true, base64_encode: true
        """
        project_id = project_id or self.get_input("project_id", required=True)
        organization_id = organization_id or self.get_input("organization_id", required=False)
        service_account_file = service_account_file or self.decode_input("service_account_file", required=False)

        # Resolve organization ID if not provided
        if not organization_id:
            self.logger.info("No organization ID provided. Attempting to resolve dynamically...")
            organization_id = self.get_google_organization_id(
                service_account_file=service_account_file,
                exit_on_completion=False,
            )
            if not organization_id:
                raise ValueError("Organization ID could not be resolved and is required.")
            self.logger.info(f"Resolved organization ID: {organization_id}")

        # Initialize Google client
        self.logger.info("Initializing Google clients...")
        google_client = self.get_google_client(service_account_file=service_account_file)
        current_service_account_email = google_client.subject
        if current_service_account_email:
            self.logger.info(f"Current service account: {current_service_account_email}")
        else:
            self.logger.warning("Unable to determine the active service account email.")

        try:
            # 1. Organization-level checks
            self.logger.info("Performing organization-level checks...")

            # Check billing status
            billing_result = self._check_org_level_billing(google_client, project_id)
            if billing_result is True:
                return self.exit_run(
                    results=False,  # Not empty
                    key="is_empty",
                    format_results=False,
                    exit_on_completion=exit_on_completion,
                )

            # Check IAM bindings
            iam_result = self._check_org_level_iam(google_client, project_id, current_service_account_email)
            if iam_result is True:
                return self.exit_run(
                    results=False,  # Not empty
                    key="is_empty",
                    format_results=False,
                    exit_on_completion=exit_on_completion,
                )

            # Check org-level logs
            log_result = self._check_org_level_logs(google_client, project_id, organization_id)
            if log_result is True:
                return self.exit_run(
                    results=False,  # Not empty
                    key="is_empty",
                    format_results=False,
                    exit_on_completion=exit_on_completion,
                )

            # 2. Check enabled APIs
            self.logger.info("Checking enabled APIs...")
            try:
                enabled_apis = self.get_enabled_apis_for_google_project(
                    project_id=project_id, service_account_file=service_account_file, exit_on_completion=False
                )
            except Exception as e:
                self.logger.warning(
                    f"Unable to determine enabled APIs for project '{project_id}'. "
                    f"No organization-level activity found and cannot check project-level resources: {e}"
                )
                return self.exit_run(
                    results=False,  # Fail safe - assume not empty
                    key="is_empty",
                    format_results=False,
                    exit_on_completion=exit_on_completion,
                )

            enabled_api_names = {api.get("name", "").split("/")[-1] for api in enabled_apis}

            # No APIs = Empty project
            if not enabled_api_names:
                self.logger.info(f"Project '{project_id}' has no enabled APIs. Project is definitely empty.")
                return self.exit_run(
                    results=True,
                    key="is_empty",
                    format_results=False,
                    exit_on_completion=exit_on_completion,
                )

            self.logger.info(f"Found enabled APIs: {', '.join(sorted(enabled_api_names))}")

            # 3. Check for APIs that indicate usage
            checkable_resources = self._get_checkable_resources()
            usage_indicating_apis = {
                api for api, info in checkable_resources.items() if api in enabled_api_names and info["indicates_usage"]
            }

            if usage_indicating_apis:
                self.logger.info(
                    f"Project has APIs enabled that indicate active usage: "
                    f"{', '.join(checkable_resources[api]['name'] for api in usage_indicating_apis)}"
                )
                return self.exit_run(
                    results=False,
                    key="is_empty",
                    format_results=False,
                    exit_on_completion=exit_on_completion,
                )

            # 4. Build list of what we can check based on enabled APIs
            self.logger.info("Determining which resource types we can check...")
            checkable_resource_types = []
            for api in enabled_api_names:
                if api in checkable_resources:
                    checkable_resource_types.extend(checkable_resources[api]["enables_checks"])

            if not checkable_resource_types:
                self.logger.info(
                    "No APIs enabled that allow resource checking. "
                    "Since no usage-indicating APIs are enabled, project is likely empty."
                )
                return self.exit_run(
                    results=True,
                    key="is_empty",
                    format_results=False,
                    exit_on_completion=exit_on_completion,
                )

            self.logger.info(
                f"Can check for the following resource types: {', '.join(sorted(checkable_resource_types))}"
            )

            # 5. Check for resources using Cloud Asset API
            resource_result = self._check_project_resources(
                google_client, project_id, enabled_api_names, checkable_resource_types
            )
            if resource_result is True:
                return self.exit_run(
                    results=False,
                    key="is_empty",
                    format_results=False,
                    exit_on_completion=exit_on_completion,
                )

            # 6. Final check: project-level logs
            log_result = self._check_project_logs(google_client, project_id, checkable_resource_types)
            if log_result is True:
                return self.exit_run(
                    results=False,
                    key="is_empty",
                    format_results=False,
                    exit_on_completion=exit_on_completion,
                )

            # If we get here, nothing indicating usage was found
            self.logger.info(
                f"No resources or activity found in project '{project_id}'. "
                f"Checked organization-level activity, project APIs, and available resource types. "
                f"Project is empty."
            )
            return self.exit_run(
                results=True,
                key="is_empty",
                format_results=False,
                exit_on_completion=exit_on_completion,
            )

        except Exception as e:
            self.logger.error(f"Error checking project '{project_id}' status: {e}")
            return self.exit_run(
                results=False,  # Assume not empty if checks fail
                key="is_empty",
                format_results=False,
                exit_on_completion=exit_on_completion,
            )

    def get_google_projects(
        self,
        organization_id: Optional[str] = None,
        service_account_file: Optional[Mapping] = None,
        key_results_by: Optional[str] = None,
        exit_on_completion: bool = True,
    ):
        """
        Retrieves all GCP projects under the specified organization and associates them with their billing accounts.

        generator=key: projects, module_class: google

        name: organization_id, required: false, type: string
        name: service_account_file, required: false, json_encode: true, base64_encode: true
        name: key_results_by, required: false, type: string, default: None
        """

        # Decode inputs
        service_account_file = service_account_file or self.decode_input("service_account_file", required=False)
        organization_id = organization_id or self.get_input("organization_id", required=False)
        key_results_by = key_results_by or self.get_input("key_results_by", required=False, default="projectId")

        # Resolve organization ID
        if not organization_id:
            organization_id = self.get_google_organization_id(
                service_account_file=service_account_file,
                exit_on_completion=False,
            )

        # Initialize Google Client and services
        google_client = self.get_google_client(service_account_file=service_account_file)
        cloud_resource_manager = google_client.get_service("cloudresourcemanager", "v1")
        cloud_billing = google_client.get_service("cloudbilling", "v1")

        # Fetch all billing accounts
        billing_accounts = self.get_google_billing_accounts(
            service_account_file=service_account_file,
            exit_on_completion=False,
        )

        # Map billing account to projects
        billing_account_projects = {}
        for account_id in billing_accounts.keys():
            try:
                request = cloud_billing.billingAccounts().projects().list(name=f"billingAccounts/{account_id}")
                while request:
                    response = request.execute()
                    for project in response.get("projectBillingInfo", []):
                        project_id = project.get("projectId")
                        if project_id:
                            billing_account_projects[project_id] = account_id
                    request = (
                        cloud_billing.billingAccounts()
                        .projects()
                        .list_next(previous_request=request, previous_response=response)
                    )
            except googleapiclient.errors.HttpError as http_err:
                self.logger.warning(
                    f"HTTP error while retrieving projects for billing account '{account_id}': {http_err}"
                )

        # Retrieve and process projects
        projects_map = {}
        try:
            self.logger.info(f"Retrieving projects under organization '{organization_id}'...")
            request = cloud_resource_manager.projects().list()
            while request:
                response = request.execute()

                # Process each project
                for project in response.get("projects", []):
                    project_id = project.get("projectId")
                    if not project_id:
                        raise ValueError(f"Missing 'projectId' for project: {project}")

                    # Add billing account info or None
                    project["billingAccountID"] = billing_account_projects.get(project_id, None)

                    # Key project by specified field
                    project_key = project.get(key_results_by)
                    if not project_key:
                        raise ValueError(f"Key '{key_results_by}' not found for project: {project}")

                    if project_key in projects_map:
                        self.logger.warning(f"Duplicate project key '{project_key}' encountered. Skipping...")
                        continue

                    projects_map[project_key] = project

                # Get next page of projects
                request = cloud_resource_manager.projects().list_next(
                    previous_request=request, previous_response=response
                )

            self.logger.info(f"Retrieved {len(projects_map)} projects under organization '{organization_id}'.")

        except googleapiclient.errors.HttpError as http_err:
            self.logger.error(f"HTTP error while retrieving projects: {http_err}")
            raise
        except Exception as err:
            self.logger.error(f"Unexpected error while retrieving projects: {err}")
            raise

        # Return the map of projects
        return self.exit_run(
            results=projects_map,
            key="projects",
            format_results=True,
            exit_on_completion=exit_on_completion,
        )

    def get_google_billing_account(
        self,
        billing_account_name: Optional[str] = None,
        service_account_file: Optional[Mapping] = None,
        exit_on_completion: bool = True,
    ):
        """
        Gets the billing account ID by name.

        generator=key: billing_account_id, plaintext_output: true, module_class: google

        name: billing_account_name, required: false, type: string, default: "Primary"
        name: service_account_file, required: false, json_encode: true, base64_encode: true
        """

        billing_account_name = (
            billing_account_name or self.get_input("billing_account_name", required=False) or "Primary"
        )

        # Decode service_account_file if provided
        service_account_file = service_account_file or self.decode_input("service_account_file", required=False)

        # Log inputs
        self.logger.info(f"Retrieving billing account ID...")
        self.logger.debug(
            f"Inputs - Billing Account Name: {billing_account_name}, "
            f"Service Account File: {service_account_file is not None}"
        )

        # Get Google Client
        google_client = self.get_google_client(service_account_file=service_account_file)

        # Log client information
        self.logger.info(f"Google Client initialized with subject: {google_client.subject}")
        self.logger.debug(f"Google Client scopes: {google_client.scopes}")

        # Get Billing API Service
        billing = google_client.get_service("cloudbilling", "v1")

        # Retrieve and log the billing accounts
        try:
            self.logger.info("Listing billing accounts...")
            billing_accounts = billing.billingAccounts().list().execute().get("billingAccounts", [])
            self.logger.debug(f"Billing Accounts Retrieved: {billing_accounts}")

            # Match billing account by display name
            for account in billing_accounts:
                self.logger.debug(f"Checking account: {account}")
                if account.get("displayName") == billing_account_name:
                    billing_account_id = account.get("name").split("/")[-1]
                    self.logger.info(f"Found billing account: {billing_account_id}")
                    return self.exit_run(
                        results=billing_account_id,
                        format_results=False,
                        key="billing_account_id",
                        exit_on_completion=exit_on_completion,
                    )

            # If no match found
            self.logger.warning(f"No billing account found for name: {billing_account_name}")
        except Exception as e:
            self.logger.error(f"Failed to retrieve billing accounts: {e}")
            raise

        raise ValueError(f"Billing account '{billing_account_name}' not found.")

    def get_google_bigquery_billing_dataset(
        self,
        project_id: Optional[str] = None,
        billing_account_name: Optional[str] = None,
        dataset_name: Optional[str] = None,
        service_account_file: Optional[Mapping] = None,
        exit_on_completion: bool = True,
    ):
        """
        Gets or creates the BigQuery billing dataset for the specified project and ensures billing export is configured.

        generator=key: dataset, plaintext_output: true, module_class: google

        name: project_id, required: false, type: string, default: "flipside-security-admin"
        name: billing_account_name, required: false, type: string, default: "Primary"
        name: dataset_name, required: false, type: string, default: "billing_dataset"
        name: service_account_file, required: false, json_encode: true, base64_encode: true
        """

        # Initialize inputs or defaults
        project_id = project_id or self.get_input("project_id", required=False) or "flipside-security-admin"
        dataset_name = dataset_name or self.get_input("dataset_name", required=False) or "billing_dataset"

        # Retrieve the billing account ID using the datasource
        billing_account_id = self.get_google_billing_account(
            billing_account_name=billing_account_name,
            service_account_file=service_account_file,
            exit_on_completion=False,
        )
        self.logger.info(f"Using billing account ID: {billing_account_id}")

        # Get Google Client and BigQuery service
        google_client = self.get_google_client(service_account_file=service_account_file)
        bigquery = google_client.get_service("bigquery", "v2")
        billing = google_client.get_service("cloudbilling", "v1")

        # Dataset ID in the correct format
        dataset_id = f"{project_id}.{dataset_name}"  # Use '.' for BigQuery references

        # Check if the dataset exists
        try:
            bigquery.datasets().get(projectId=project_id, datasetId=dataset_name).execute()
            self.logger.info(f"BigQuery dataset '{dataset_id}' already exists.")
        except googleapiclient.errors.HttpError as e:
            if e.resp.status == 404:
                self.logger.info(f"Creating BigQuery dataset '{dataset_id}'...")
                try:
                    bigquery.datasets().insert(
                        projectId=project_id,
                        body={
                            "datasetReference": {"projectId": project_id, "datasetId": dataset_name},
                            "description": "Billing export dataset for project costs",
                        },
                    ).execute()
                    self.logger.info(f"BigQuery dataset '{dataset_id}' created successfully.")
                except Exception as inner_e:
                    self.logger.error(f"Failed to create BigQuery dataset '{dataset_id}': {inner_e}")
                    raise
            else:
                self.logger.error(f"Failed to check if BigQuery dataset '{dataset_id}' exists: {e}")
                raise

        # Ensure billing export is configured
        try:
            self.logger.info(f"Checking existing billing export configuration for project '{project_id}'...")
            current_billing_info = billing.projects().getBillingInfo(name=f"projects/{project_id}").execute()

            self.logger.debug(f"Current billing export info: {current_billing_info}")

            if current_billing_info.get("billingAccountName") != f"billingAccounts/{billing_account_id}":
                self.logger.info(f"Billing account mismatch. Updating export for project '{project_id}'...")
                billing.projects().updateBillingInfo(
                    name=f"projects/{project_id}",
                    body={"billingAccountName": f"billingAccounts/{billing_account_id}"},
                ).execute()
                self.logger.info(
                    f"Billing export successfully configured for project '{project_id}' and dataset '{dataset_id}'."
                )
            else:
                self.logger.info(
                    f"Billing export already correctly configured for project '{project_id}' with billing account '{billing_account_id}'."
                )

        except Exception as e:
            self.logger.error(f"Failed to configure billing export for dataset '{dataset_id}': {e}")
            raise

        # Return the dataset ID
        return self.exit_run(
            results=dataset_id,
            format_results=False,
            key="dataset",
            exit_on_completion=exit_on_completion,
        )

    def get_dead_google_projects(
        self,
        inactivity_period_days: Optional[int] = None,
        billing_dataset: Optional[str] = None,
        project_id: Optional[str] = None,
        dataset_name: Optional[str] = None,
        service_account_file: Optional[Mapping] = None,
        exit_on_completion: bool = True,
    ):
        """
        Identifies GCP projects with no billing activity in the specified period.

        generator=key: dead_projects, module_class: google

        name: inactivity_period_days, required: false, type: integer, default: 30
        name: billing_dataset, required: false, type: string
        name: project_id, required: false, type: string, default: "flipside-security-admin"
        name: dataset_name, required: false, type: string, default: "billing_dataset"
        name: service_account_file, required: false, json_encode: true, base64_encode: true
        """

        # Initialize inputs or defaults
        inactivity_period_days = (
            inactivity_period_days or self.get_input("inactivity_period_days", required=False) or 30
        )
        project_id = project_id or self.get_input("project_id", required=False) or "flipside-security-admin"
        dataset_name = dataset_name or self.get_input("dataset_name", required=False) or "billing_dataset"

        # Decode service_account_file if provided
        service_account_file = service_account_file or self.decode_input("service_account_file", required=False)

        # Ensure billing dataset is configured
        billing_dataset = billing_dataset or self.get_google_bigquery_billing_dataset(
            project_id=project_id,
            dataset_name=dataset_name,
            service_account_file=service_account_file,
            exit_on_completion=False,
        )

        # Get Google Client and BigQuery service
        google_client = self.get_google_client(service_account_file=service_account_file)
        bigquery = google_client.get_service("bigquery", "v2")

        # Log tables in the dataset
        try:
            tables = bigquery.tables().list(projectId=project_id, datasetId=dataset_name).execute()
            self.logger.debug(f"Tables in dataset '{dataset_name}': {tables.get('tables', [])}")
        except Exception as e:
            self.logger.error(f"Failed to list tables in dataset '{dataset_name}': {e}")
            raise

        # Construct the query
        query = f"""
            SELECT project.id AS project_id, SUM(cost) AS total_cost
            FROM `{project_id}.{dataset_name}.*`
            WHERE usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {inactivity_period_days} DAY)
            GROUP BY project.id
            HAVING total_cost IS NULL OR total_cost = 0
        """

        # Execute the query and process results
        try:
            self.logger.info(
                f"Executing BigQuery to identify dead projects with inactivity period: {inactivity_period_days} days"
            )
            self.logger.debug(f"BigQuery query: {query}")

            results = (
                bigquery.jobs()
                .query(
                    projectId=project_id,
                    body={"query": query, "useLegacySql": False},
                )
                .execute()
            )

            rows = results.get("rows", [])
            if not rows:
                self.logger.info(f"No dead projects found for dataset '{billing_dataset}'.")
                return self.exit_run(
                    results=[],
                    key="dead_projects",
                    format_results=True,
                    exit_on_completion=exit_on_completion,
                )

            projects = [row["project_id"] for row in rows]
            self.logger.info(f"Found {len(projects)} dead projects: {projects}")

        except Exception as e:
            self.logger.error(f"Failed to identify dead projects: {e}")
            raise

        # Return the list of dead projects
        return self.exit_run(
            results=projects,
            key="dead_projects",
            format_results=True,
            exit_on_completion=exit_on_completion,
        )

    def get_google_org_units(
        self,
        unhump_org_units: Optional[bool] = None,
        flatten_nested_org_units: Optional[bool] = None,
        use_basename: Optional[bool] = None,
        allowed_ou_types: Optional[tuple[str, ...]] = None,
        denied_ou_types: Optional[tuple[str, ...]] = None,
        include_root: Optional[bool] = None,
        exit_on_completion: bool = True,
    ):
        """Gets Google organizational units for the organization

        generator=key: org_units, module_class: google

        name: unhump_org_units, required: false, default: true
        name: flatten_nested_org_units, required: false, default: false
        name: use_basename, required: false, default: false
        name: allowed_ou_types, required: false, default: [], json_encode: true
        name: denied_ou_types, required: false, default: [], json_encode: true
        name: include_root, required: false, default: true
        """

        if unhump_org_units is None:
            unhump_org_units = self.get_input("unhump_org_units", required=False, default=True, is_bool=True)

        if flatten_nested_org_units is None:
            flatten_nested_org_units = self.get_input(
                "flatten_nested_org_units", required=False, default=False, is_bool=True
            )

        if use_basename is None:
            use_basename = self.get_input("use_basename", required=False, default=False, is_bool=True)

        if allowed_ou_types is None:
            allowed_ou_types = self.decode_input(
                "allowed_ou_types", required=False, default=[], decode_from_base64=False, allow_none=False
            )
            allowed_ou_types = tuple(allowed_ou_types)

        if denied_ou_types is None:
            denied_ou_types = self.decode_input(
                "denied_ou_types", required=False, default=[], decode_from_base64=False, allow_none=False
            )
            denied_ou_types = tuple(denied_ou_types)

        if include_root is None:
            include_root = self.get_input("include_root", required=False, default=True, is_bool=True)

        google_client = self.get_google_client()
        directory = google_client.get_service("admin", "directory_v1")
        google_org_units = {}

        self.logger.info(
            f"Getting Google organizational units. Include root: {include_root}, "
            f"Flatten nested: {flatten_nested_org_units}, Use basename: {use_basename}, "
            f"Allowed types: {allowed_ou_types}, Denied types: {denied_ou_types}"
        )

        def get_org_units(org_unit_path: str = "/"):
            kwargs = utils.get_google_call_params(
                no_max_results=True,
                customerId="my_customer",
                orgUnitPath=org_unit_path,
            )

            results = directory.orgunits().list(**kwargs).execute()

            org_units = results.get("organizationUnits", [])

            for org_unit in org_units:
                ou_path = org_unit["orgUnitPath"]
                ou_name = org_unit["name"]

                # Skip root OU if not included
                if not include_root and ou_path == "/":
                    self.logger.warning(f"Skipping root OU {ou_path}")
                    continue

                # Check allowed/denied types (if specific OU types are specified)
                if allowed_ou_types and ou_name not in allowed_ou_types:
                    self.logger.warning(f"OU {ou_path} ({ou_name}) not in allowed types")
                    continue

                if denied_ou_types and ou_name in denied_ou_types:
                    self.logger.warning(f"OU {ou_path} ({ou_name}) in denied types")
                    continue

                google_org_units[ou_path] = org_unit

                # Recursively get child OUs
                try:
                    get_org_units(ou_path)
                except Exception as e:
                    self.logger.warning(f"Could not fetch child OUs for {ou_path}: {e}")

        get_org_units()

        # If flatten_nested_org_units is True, restructure the data
        if flatten_nested_org_units:
            google_org_units = self._flatten_org_unit_hierarchy(google_org_units, use_basename)

        return self.exit_run(
            google_org_units,
            key="org_units",
            encode_to_base64=True,
            format_json=False,
            unhump_results=unhump_org_units,
            exit_on_completion=exit_on_completion,
        )

    def _flatten_org_unit_hierarchy(self, org_units: dict, use_basename: bool = False) -> dict:
        """
        Restructures org units so that each top-level OU contains its children
        nested under a 'units' key, recursively.

        # NOPARSE
        """

        def get_basename(path: str) -> str:
            """Get the basename of an org unit path using pathlib"""

            if path == "/":
                return "root"
            # Use pathlib to get the basename and convert to lowercase
            return Path(path).name.lower()

        def get_display_key(path: str) -> str:
            """Get the key to use for display - either full path or basename"""
            if use_basename:
                return get_basename(path)
            return path.lower()

        def build_hierarchy(parent_path: str, all_units: dict) -> dict:
            """Recursively build hierarchy for children of parent_path"""
            children = {}
            for ou_path, ou_data in all_units.items():
                if ou_data.get("parentOrgUnitPath") == parent_path:
                    # Keep all fields except the specific read-only ones
                    clean_ou_data = {k: v for k, v in ou_data.items() if k not in ["etag", "kind", "orgUnitPath"]}

                    # Recursively add children
                    child_units = build_hierarchy(ou_path, all_units)
                    if child_units:
                        clean_ou_data["units"] = child_units

                    display_key = get_display_key(ou_path)
                    children[display_key] = clean_ou_data

            return children

        # Get top-level OUs (parent is "/")
        flattened_units = {}

        for ou_path, ou_data in org_units.items():
            if ou_data.get("parentOrgUnitPath") == "/":
                # Keep all fields except the specific read-only ones
                clean_ou_data = {k: v for k, v in ou_data.items() if k not in ["etag", "kind", "orgUnitPath"]}

                # Add nested children
                child_units = build_hierarchy(ou_path, org_units)
                if child_units:
                    clean_ou_data["units"] = child_units

                display_key = get_display_key(ou_path)
                flattened_units[display_key] = clean_ou_data

        return flattened_units

    def get_google_users(
        self,
        unhump_users: Optional[bool] = None,
        flatten_name: Optional[bool] = None,
        allowed_ous: Optional[tuple[str, ...]] = None,
        denied_ous: Optional[tuple[str, ...]] = None,
        active_only: Optional[bool] = None,
        include_bots: Optional[bool] = None,
        exit_on_completion: bool = True,
    ):
        """Gets Google users for the organization

        generator=key: users, module_class: google

        name: unhump_users, required: false, default: true
        name: flatten_name, required: false, default: false
        name: allowed_ous, required: false, default: [], json_encode: true
        name: denied_ous, required: false, default: [], json_encode: true
        name: active_only, required: false, default: false
        name: include_bots, required: false, default: true
        """
        if unhump_users is None:
            unhump_users = self.get_input("unhump_users", required=False, default=True, is_bool=True)

        if flatten_name is None:
            flatten_name = self.get_input("flatten_name", required=False, default=False, is_bool=True)

        if allowed_ous is None:
            allowed_ous = self.decode_input(
                "allowed_ous", required=False, default=[], decode_from_base64=False, allow_none=False
            )
            allowed_ous = tuple(allowed_ous)

        if denied_ous is None:
            denied_ous = self.decode_input(
                "denied_ous", required=False, default=[], decode_from_base64=False, allow_none=False
            )
            denied_ous = tuple(denied_ous)

        if active_only is None:
            active_only = self.get_input("active_only", required=False, default=False, is_bool=True)

        if include_bots is None:
            include_bots = self.get_input("include_bots", required=False, default=True, is_bool=True)

        google_client = self.get_google_client()
        directory = google_client.get_service("admin", "directory_v1")
        google_users = {}

        self.logger.info(
            f"Getting Google users. Active only: {active_only}, Allowlist: {allowed_ous}, Denylist: {denied_ous}"
        )

        def get_users(last_token: Optional[str] = None):
            kwargs = utils.get_google_call_params(domain="flipsidecrypto.com", pageToken=last_token)

            results = directory.users().list(**kwargs).execute()

            users = results.get("users", [])

            for user in users:
                primary_email = user["primaryEmail"]
                suspended = user.get("suspended")
                archived = user.get("archived")
                org_unit_path = user.get("orgUnitPath")

                if active_only and (suspended or archived):
                    self.logger.warning(
                        f"Skipping suspended [{suspended}] or archived [{archived}] user {primary_email}"
                    )
                    continue

                if (allowed_ous and org_unit_path not in allowed_ous) or org_unit_path in denied_ous:
                    self.logger.warning(f"User {primary_email} either not in allowlist or in denylist")
                    continue

                if not include_bots and org_unit_path.startswith("/Automation"):
                    self.logger.warning(f"Skipping bot user {primary_email}")
                    continue

                if flatten_name:
                    user_name = user.pop("name", {})
                    user = self.merger.merge(user, user_name)

                google_users[primary_email] = user

            return results.get("nextPageToken")

        next_page_token = get_users()

        while not utils.is_nothing(next_page_token):
            self.logger.info("More users remain to be fetched...")
            next_page_token = get_users(next_page_token)

        return self.exit_run(
            google_users,
            key="users",
            encode_to_base64=True,
            format_json=False,
            unhump_results=unhump_users,
            exit_on_completion=exit_on_completion,
        )

    def get_google_client_for_user(self, primary_email: str) -> GoogleClient:
        """Gets a Google client for a specific user

        # NOPARSE
        """
        if primary_email in self._google_user_clients:
            return self._google_user_clients[primary_email]

        self._google_user_clients[primary_email] = GoogleClient.impersonate_subject(
            new_subject=primary_email,
            scopes=SCOPES,
            original_subject=SUBJECT,
            service_account_file=self.GOOGLE_SERVICE_ACCOUNT,
            **self.kwargs,
        )

        return self._google_user_clients[primary_email]

    def get_google_groups(
        self,
        unhump_groups: Optional[bool] = None,
        members_only: Optional[bool] = None,
        only_status_for_members: Optional[str] = None,
        only_type_for_members: Optional[str] = None,
        flatten_members: Optional[bool] = None,
        group_keys: Optional[list[str]] = None,
        group_names: Optional[list[str]] = None,  # New parameter for filtering by group names
        user_key: Optional[str] = None,
        sort_by_name: Optional[bool] = None,
        exit_on_completion: bool = True,
    ):
        """Gets Google groups for the organization

        generator=key: groups, module_class: google

        name: unhump_groups, required: false, default: true
        name: members_only, required: false, default: false
        name: only_status_for_members, required: false, type: string
        name: only_type_for_members, required: false, type: string
        name: flatten_members, required: false, default: false
        name: group_keys, required: false, default: [], json_encode: true
        name: group_names, required: false, json_encode: true
        name: user_key, required: false, type: string
        name: sort_by_name, required: false, default: false
        """

        if unhump_groups is None:
            unhump_groups = self.get_input("unhump_groups", required=False, default=True, is_bool=True)

        if members_only is None:
            members_only = self.get_input("members_only", required=False, default=False, is_bool=True)

        if only_status_for_members is None:
            only_status_for_members = self.get_input("only_status_for_members", required=False)

        if only_type_for_members is None:
            only_type_for_members = self.get_input("only_type_for_members", required=False)

        if flatten_members is None:
            flatten_members = self.get_input("flatten_members", required=False, default=False, is_bool=True)

        if group_keys is None:
            group_keys = self.decode_input(
                "group_keys",
                required=False,
                default=[],
                decode_from_base64=False,
                allow_none=False,
            )

        if group_names is None:
            group_names = self.decode_input("group_names", required=False, decode_from_base64=False)

        if user_key is None:
            user_key = self.get_input("user_key", required=False)

        if sort_by_name is None:
            sort_by_name = self.get_input("sort_by_name", required=False, default=False, is_bool=True)

        google_client = self.get_google_client()
        directory = google_client.get_service("admin", "directory_v1")
        settings = google_client.get_service("groupssettings", "v1")
        google_groups = {}
        remaining_group_keys = copy(group_keys)

        def get_groups(last_token: Optional[str] = None, last_group_key: Optional[str] = None):
            def add_group(g: Any):
                if utils.is_nothing(g):
                    raise RuntimeError("No group data to process when getting Google groups")

                group_key = g["email"]

                group_settings = settings.groups().get(groupUniqueId=group_key).execute()
                if utils.is_nothing(group_settings):
                    raise RuntimeError(f"Unable to retrieve group settings for {group_key}")

                g = self.merger.merge(g, group_settings)

                group_members = {}

                def get_group_members(members_last_token: Optional[str] = None):
                    kwargs = utils.get_google_call_params(groupKey=group_key, pageToken=members_last_token)

                    results = directory.members().list(**kwargs).execute()

                    for member in results.get("members", []):
                        if (
                            not utils.is_nothing(only_status_for_members)
                            and member.get("status") != only_status_for_members
                        ):
                            self.logged_statement(
                                f"Rejecting member, does not meet status {only_status_for_members}",
                                json_data=member,
                                verbose=True,
                                verbosity=2,
                            )
                            continue

                        if not utils.is_nothing(only_type_for_members) and member.get("type") != only_type_for_members:
                            self.logged_statement(
                                f"Rejecting member, does not meet type {only_type_for_members}",
                                json_data=member,
                                verbose=True,
                                verbosity=2,
                            )
                            continue

                        group_members[member["email"]] = member

                    return results.get("nextPageToken")

                members_next_page_token = get_group_members()

                while not utils.is_nothing(members_next_page_token):
                    self.logger.info("More group_members remain to be fetched...")
                    members_next_page_token = get_group_members(members_next_page_token)

                if flatten_members:
                    group_members = list(group_members.keys())

                if members_only:
                    google_groups[group_key] = group_members
                else:
                    google_groups[group_key] = g
                    google_groups[group_key]["members"] = group_members

            if utils.is_nothing(group_keys):
                kwargs = utils.get_google_call_params(
                    domain="flipsidecrypto.com", userKey=user_key, pageToken=last_token
                )

                results = directory.groups().list(**kwargs).execute()

                for group in results.get("groups", []):
                    if group_names and group["name"] not in group_names and group["email"] not in group_names:
                        continue
                    add_group(group)

                return results.get("nextPageToken"), None
            else:
                if utils.is_nothing(last_group_key):
                    if utils.is_nothing(remaining_group_keys):
                        return None, None

                    last_group_key = remaining_group_keys.pop()

                if utils.is_nothing(last_group_key):
                    return None, None

                results = directory.groups().get(groupKey=last_group_key).execute()
                add_group(results)

                if utils.is_nothing(remaining_group_keys):
                    return None, None

                return None, remaining_group_keys.pop()

        next_page_token, next_group_key = get_groups()

        while not utils.is_nothing(next_page_token) or not utils.is_nothing(next_group_key):
            self.logger.info("More groups remain to be fetched...")
            next_page_token, next_group_key = get_groups(next_page_token, next_group_key)

        return self.exit_run(
            google_groups,
            key="groups",
            encode_to_base64=True,
            format_json=False,
            unhump_results=unhump_groups,
            prefix_allowlist=[
                "email",
                "name",
                "id",
            ],
            sort_by_field="name" if sort_by_name else None,
            exit_on_completion=exit_on_completion,
        )

    def get_flipsidecrypto_team_calendar_shares(
        self,
        exit_on_completion: bool = True,
    ):
        """Gets FlipsideCrypto team calendar shares

        generator=key: shares, module_class: gitops

        """
        self.logger.info("Getting FlipsideCrypto team calendar shares")
        google_client = self.get_google_client()

        calendar = google_client.get_service("calendar", "v3")
        shares = {}

        def get_shares(last_token: Optional[str] = None):
            kwargs = utils.get_google_call_params(calendarId=self.TEAM_CALENDAR_ID, pageToken=last_token)

            results = calendar.acl().list(**kwargs).execute()

            rules = results.get("items", [])

            npt = results.get("nextPageToken")

            for rule in rules:
                rule_id = rule.get("id")
                if rule_id.endswith("group.calendar.google.com"):
                    self.logger.warning(f"Skipping the rule for self-ownership: {rule_id}")
                    continue

                if not rule_id:
                    raise ValueError(f"Malformed ACL rule {rule} has no ID in team calendar")

                scope = rule.get("scope", {})
                if not scope:
                    user_id = rule_id.partition(":")[2]
                else:
                    user_id = scope["value"]

                shares[user_id] = {
                    "id": rule_id,
                    "role": rule.get("role"),
                    "type": scope.get("type"),
                }

            return npt

        next_page_token = get_shares()

        while not utils.is_nothing(next_page_token):
            self.logger.info("More rules remain to be fetched...")
            next_page_token = get_shares(next_page_token)

        self.log_results(shares, log_file_name="rules.log.json")

        return self.exit_run(
            shares,
            key="shares",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def get_remote_terraform_variables(
        self,
        repository_name: Optional[str] = None,
        repository_tag: Optional[str] = None,
        local_module_source: Optional[str] = None,
        variable_files: Optional[list[str]] = None,
        defaults: Optional[dict[str, Any]] = None,
        overrides: Optional[dict[str, Any]] = None,
        parameter_generators: Optional[dict[str, Any]] = None,
        map_name_to: Optional[dict[str, Any]] = None,
        map_sanitized_name_to: Optional[dict[str, Any]] = None,
        requires_github_authentication: Optional[bool] = None,
        exit_on_completion: Optional[bool] = True,
    ):
        """Gets remote Terraform variables for variable files

        generator=key: variables, module_class: terraform

        name: repository_name, required: true
        name: repository_tag, required: true
        name: local_module_source, required: false
        name: variable_files, required: true, json_encode: true
        name: defaults, required: false, default: {}, json_encode: true, base64_encode: true
        name: overrides, required: false, default: {}, json_encode: true, base64_encode: true
        name: parameter_generators, required: false, default: {}, json_encode: true, base64_encode: true
        name: map_name_to, required: false, default: {}, json_encode: true, base64_encode: true
        name: map_sanitized_name_to, required: false, default: {}, json_encode: true, base64_encode: true
        name: requires_github_authentication, required: false, default: false"""
        if repository_name is None:
            repository_name = self.get_input("repository_name", required=True)

        if repository_tag is None:
            repository_tag = self.get_input("repository_tag", required=True)

        if local_module_source is None:
            local_module_source = self.get_input("local_module_source", required=False)

        if variable_files is None:
            variable_files = self.decode_input("variable_files", required=True, decode_from_base64=False)

        if defaults is None:
            defaults = self.decode_input("defaults", required=False, default={})

        if overrides is None:
            overrides = self.decode_input("overrides", required=False, default={})

        if parameter_generators is None:
            parameter_generators = self.decode_input("parameter_generators", required=False, default={})

        if map_name_to is None:
            map_name_to = self.decode_input("map_name_to", required=False, default={})

        if map_sanitized_name_to is None:
            map_sanitized_name_to = self.decode_input("map_sanitized_name_to", required=False, default={})

        if requires_github_authentication is None:
            requires_github_authentication = self.get_input(
                "requires_github_authentication",
                required=False,
                default=False,
                is_bool=True,
            )

        variables = TerraformRemoteModuleVariables(
            repository_name=repository_name,
            repository_tag=repository_tag,
            local_module_source=local_module_source,
            variable_files=variable_files,
            defaults=defaults,
            overrides=overrides,
            parameter_generators=parameter_generators,
            map_name_to=map_name_to,
            map_sanitized_name_to=map_sanitized_name_to,
            requires_github_authentication=requires_github_authentication,
            logger=self.logger,
            **self.kwargs,
        )

        return self.exit_run(
            variables.convert(),
            key="variables",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def get_slack_users(
        self,
        include_locale: Optional[bool] = None,
        limit: Optional[int] = None,
        team_id: Optional[str] = None,
        include_deleted: Optional[bool] = None,
        include_bots: Optional[bool] = None,
        include_app_users: Optional[bool] = None,
        flatten_profile: Optional[bool] = None,
        flipsidecrypto_users_only: Optional[bool] = None,
        exit_on_completion: bool = True,
    ):
        """Gets Slack users for the authenticated Slack token

        generator=key: users, module_class: slack

        name: include_locale, required: false
        name: limit, required: false
        name: team_id, required: false
        name: include_deleted, required: false, default: false
        name: include_bots, required: false, default: false
        name: include_app_users, required: false, default: false
        name: flatten_profile, required: false, default: false
        name: flipsidecrypto_users_only, required: false, default: false
        """
        if include_locale is None:
            include_locale = self.get_input("include_locale", required=False, is_bool=True)

        if limit is None:
            limit = self.get_input("limit", required=False)

        if team_id is None:
            team_id = self.get_input("team_id", required=False)

        if include_deleted is None:
            include_deleted = self.get_input("include_deleted", required=False, default=False, is_bool=True)

        if include_bots is None:
            include_bots = self.get_input("include_bots", required=False, default=False, is_bool=True)

        if include_app_users is None:
            include_app_users = self.get_input("include_app_users", required=False, default=False, is_bool=True)

        if flatten_profile is None:
            flatten_profile = self.get_input("flatten_profile", required=False, default=False, is_bool=True)

        if flipsidecrypto_users_only is None:
            flipsidecrypto_users_only = self.get_input(
                "flipsidecrypto_users_only", required=False, default=False, is_bool=True
            )

        if flipsidecrypto_users_only:
            flatten_profile = True

        slack_client = self.get_slack_client()
        users = slack_client.list_users(
            include_locale=include_locale,
            limit=limit,
            team_id=team_id,
            include_deleted=include_deleted,
            include_bots=include_bots,
            include_app_users=include_app_users,
        )

        if not flipsidecrypto_users_only:
            return self.exit_run(
                users,
                key="users",
                encode_to_base64=True,
                format_json=False,
                exit_on_completion=exit_on_completion,
            )

        sorted = {}

        for user_id, user_data in users.items():
            if flatten_profile:
                user_profile = user_data.pop("profile", {})
                user_data = {k: v for k, v in user_data.items() if "id" not in k and not k.startswith("is")}
                user_data = self.merger.merge(user_data, user_profile)
                user_data["slack_userid"] = user_id

                full_name = utils.first_non_empty_value_from_map(
                    user_data,
                    "real_name_normalized",
                    "real_name",
                    "display_name_normalized",
                    "display_name",
                )
                first_name = user_data.get("first_name")
                last_name = user_data.get("last_name")

                if utils.is_nothing(full_name):
                    if not utils.is_nothing(first_name):
                        full_name = first_name.split(" ")[0]

                    if not utils.is_nothing(last_name) and last_name != first_name:
                        full_name += f" {last_name.split(" ")[0]}"

                if not utils.is_nothing(full_name):
                    user_data["full_name"] = full_name.title()

            if not flipsidecrypto_users_only:
                sorted[user_id] = user_data
                continue

            user_email = user_data.get("email", "")

            if not user_email.endswith("@flipsidecrypto.com"):
                self.logged_statement(
                    f"Skipping user {user_id}, not a flipsidecrypto user:\n{user_data}", verbose=True, verbosity=2
                )
                continue

            if user_email in sorted:
                sorted[user_email] = self.merger.merge(sorted[user_email], user_data)
                continue

            sorted[user_email] = user_data

        return self.exit_run(
            sorted,
            key="users",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def get_slack_usergroups(
        self,
        include_count: Optional[bool] = None,
        include_disabled: Optional[bool] = None,
        include_users: Optional[bool] = None,
        expand_users: Optional[bool] = None,
        team_id: Optional[str] = None,
        sort_by_name: Optional[bool] = None,
        user_identifiers_file: Optional[FilePath] = None,
        channel_identifiers_file: Optional[FilePath] = None,
        prefix: Optional[bool] = None,
        exit_on_completion: Optional[bool] = True,
    ):
        """Gets Slack user groups for the authenticated Slack token

        generator=key: user_groups, module_class: slack

        name: include_count, required: false
        name: include_disabled, required: false
        name: include_users, required: false
        name: expand_users, required: false, default: false
        name: team_id, required: false
        name: sort_by_name, required: false, default: false
        name: user_identifiers_file, required: false, type: string
        name: channel_identifiers_file, required: false, type: string
        name: prefix, required: false, type: bool
        """
        if include_count is None:
            include_count = self.get_input("include_count", required=False, is_bool=True)

        if include_disabled is None:
            include_disabled = self.get_input("include_disabled", required=False, is_bool=True)

        if include_users is None:
            include_users = self.get_input("include_users", required=False, is_bool=True)

        if expand_users is None:
            expand_users = self.get_input("expand_users", required=False, default=False, is_bool=True)

        if team_id is None:
            team_id = self.get_input("team_id", required=False)

        if sort_by_name is None:
            sort_by_name = self.get_input("sort_by_name", required=False, default=False, is_bool=True)

        if user_identifiers_file is None:
            user_identifiers_file = self.get_input("user_identifiers_file", required=False)

        if channel_identifiers_file is None:
            channel_identifiers_file = self.get_input("channel_identifiers_file", required=False)

        if prefix is None:
            prefix = self.get_input("prefix", required=False, default=False, is_bool=True)

        if user_identifiers_file is None:
            user_identifiers_map = self.map_entities_to_property(blueprint_id="user", property_id="slack_userid")
        else:
            local_user_identifiers_file = self.local_path(user_identifiers_file)
            if not local_user_identifiers_file.exists():
                raise FileNotFoundError(f"User identifiers file {local_user_identifiers_file} does not exist")

            user_identifiers_map = self.get_file(local_user_identifiers_file)

        if channel_identifiers_file is None:
            channel_identifiers_map = self.map_entities_to_property(blueprint_id="slack_channel", property_id="id")
        else:
            local_channel_identifiers_file = self.local_path(channel_identifiers_file)
            if not local_channel_identifiers_file.exists():
                raise FileNotFoundError(f"channel identifiers file {local_channel_identifiers_file} does not exist")

            channel_identifiers_map = self.get_file(local_channel_identifiers_file)

        self.logger.info("Getting Slack usergroups")

        slack_client = self.get_slack_client()
        user_groups = slack_client.list_usergroups(
            include_count=include_count,
            include_disabled=include_disabled,
            include_users=include_users,
            expand_users=expand_users,
            team_id=team_id,
        )

        for group_id, group_data in deepcopy(user_groups).items():
            users = utils.all_non_empty(*utils.flatten_list(group_data.get("users", [])))
            self.logger.info(f"{group_id} users: {users}")

            user_groups[group_id]["slack_users" if prefix else "users"] = [
                user_identifiers_map[user] for user in users if user in user_identifiers_map
            ]

            user_groups[group_id]["external_slack_users" if prefix else "external_users"] = [
                user for user in users if user not in user_identifiers_map
            ]

            channels = utils.all_non_empty(*utils.flatten_list(group_data.get("prefs", {}).get("channels", [])))
            self.logger.info(f"{group_id} channels: {channels}")

            user_groups[group_id]["slack_channels" if prefix else "channels"] = [
                channel_identifiers_map[channel] for channel in channels if channel in channel_identifiers_map
            ]

            user_groups[group_id]["external_slack_channels" if prefix else "external_channels"] = [
                channel for channel in channels if channel not in channel_identifiers_map
            ]

        return self.exit_run(
            user_groups,
            key="user_groups",
            encode_to_base64=True,
            format_json=False,
            prefix="slack_usergroup" if prefix else None,
            prefix_allowlist=[
                "name",
                "id",
            ],
            sort_by_field="name" if sort_by_name else None,
            exit_on_completion=exit_on_completion,
        )

    def get_slack_conversations(
        self,
        exclude_archived: Optional[bool] = None,
        limit: Optional[int] = None,
        team_id: Optional[str] = None,
        types: Optional[Union[str, Sequence[str]]] = None,
        get_members: Optional[bool] = None,
        channels_only: Optional[bool] = None,
        sort_by_name: Optional[bool] = None,
        user_identifiers_file: Optional[FilePath] = None,
        exit_on_completion: Optional[bool] = True,
    ):
        """Gets Slack conversations for the authenticated Slack token

        generator=key: conversations, module_class: slack

        name: exclude_archived, required: false
        name: limit, required: false
        name: team_id, required: false
        name: types, required: false, json_encode: true, base64_encode: true
        name: get_members, required: false, default: false
        name: channels_only, required: false, default: false
        name: sort_by_name, required: false, default: false
        name: user_identifiers_file, required: false, type: string
        """
        if exclude_archived is None:
            exclude_archived = self.get_input("exclude_archived", required=False, is_bool=True)

        if limit is None:
            limit = self.get_input("limit", required=False)

        if team_id is None:
            team_id = self.get_input("team_id", required=False)

        if types is None:
            types = self.decode_input("types", required=False)

        if get_members is None:
            get_members = self.get_input("get_members", required=False, default=False, is_bool=True)

        if channels_only is None:
            channels_only = self.get_input("channels_only", required=False, default=False, is_bool=True)

        if sort_by_name is None:
            sort_by_name = self.get_input("sort_by_name", required=False, default=False, is_bool=True)

        if user_identifiers_file is None:
            user_identifiers_file = self.get_input("user_identifiers_file", required=False)

        self.logger.info("Getting Slack conversations")

        self.logger.info("Getting user identifiers...")

        if user_identifiers_file is None:
            user_identifiers_map = self.map_entities_to_property(blueprint_id="user", property_id="slack_userid")
        else:
            local_user_identifiers_file = self.local_path(user_identifiers_file)
            if not local_user_identifiers_file.exists():
                raise FileNotFoundError(f"User identifiers file {local_user_identifiers_file} does not exist")

            user_identifiers_map = self.get_file(local_user_identifiers_file)

        self.logger.info("Fetching conversations from API...")
        slack_client = self.get_slack_client()
        conversations = slack_client.list_conversations(
            exclude_archived=exclude_archived,
            limit=limit,
            team_id=team_id,
            types=types,
            get_members=get_members,
            channels_only=channels_only,
        )

        for conversation_id, conversation_data in deepcopy(conversations).items():
            name = conversation_data.get("name", conversation_id)

            members = conversation_data.get("members", [])
            self.logger.info(f"{name} members: {members}")

            members = utils.all_non_empty(*utils.flatten_list(members))
            self.logger.info(f"{name} members, after flattening and removing empties: {members}")

            conversations[conversation_id]["members"] = [
                user_identifiers_map[member] for member in members if member in user_identifiers_map
            ]

            conversations[conversation_id]["external_members"] = [
                member for member in members if member not in user_identifiers_map
            ]

            self.logged_statement(
                f"{name} Slack conversation processed",
                json_data=conversations[conversation_id],
            )

        self.log_results(conversations, "conversations")

        return self.exit_run(
            conversations,
            key="conversations",
            encode_to_base64=True,
            format_json=False,
            sort_by_field="name" if sort_by_name else None,
            exit_on_completion=exit_on_completion,
        )

    def get_doppler_aws_iam_role(
        self,
        workplace_slug: Optional[str] = None,
        unhump_role: Optional[bool] = None,
        execution_role_arn: Optional[str] = None,
        role_session_name: Optional[str] = None,
        exit_on_completion: bool = True,
    ):
        """Gets the Doppler AWS IAM role for an account

        generator=key: role, module_class: doppler

        name: workplace_slug, required: true, type: string
        name: unhump_role, required: false, default: false
        name: execution_role_arn, required: false, type: string
        name: role_session_name, required: false, type: string"""
        doppler_aws_account_id = "299900769157"

        if workplace_slug is None:
            workplace_slug = self.get_input("workplace_slug", required=True)

        if unhump_role is None:
            unhump_role = self.get_input("unhump_role", required=False, default=False, is_bool=True)

        if execution_role_arn is None:
            execution_role_arn = self.get_input("execution_role_arn", required=False)

        if role_session_name is None:
            role_session_name = self.get_input("role_session_name", required=False)

        # Assume Role Policy Document
        assume_role_policy_document = json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": f"arn:aws:iam::{doppler_aws_account_id}:root"},
                        "Action": "sts:AssumeRole",
                        "Condition": {
                            "StringEquals": {
                                "sts:ExternalId": workplace_slug,
                            }
                        },
                    }
                ],
            }
        )

        # Role Policy Document for Doppler
        doppler_role_policy_document = json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "secretsmanager:CreateSecret",
                            "secretsmanager:UpdateSecret",
                            "secretsmanager:DeleteSecret",
                            "secretsmanager:DescribeSecret",
                            "secretsmanager:PutSecretValue",
                            "secretsmanager:GetSecretValue",
                        ],
                        "Resource": "arn:aws:secretsmanager:*:*:secret:/*",
                    }
                ],
            }
        )

        aws_client_args = {
            "execution_role_arn": execution_role_arn,
            "role_session_name": role_session_name,
        }

        # Initialize AWS clients
        iam_client = self.get_aws_client(client_name="iam", **aws_client_args)

        sts = self.get_aws_client(client_name="sts", **aws_client_args)
        try:
            caller_identity = sts.get_caller_identity()
            caller_account_id = caller_identity.get("Account")
            if not caller_account_id:
                raise RuntimeError("Unable to retrieve AWS account ID")
        except AWSClientError as e:
            self.logger.error(f"Failed to get caller identity: {e}")
            raise

        role_name = f"doppler-integration-role-{caller_account_id}"
        policy_name = f"{role_name}-policy"
        policy_arn = f"arn:aws:iam::{caller_account_id}:policy/{policy_name}"

        # Validate the policy document
        try:
            access_analyzer = self.get_aws_client(client_name="accessanalyzer", **aws_client_args)
            validation_findings = access_analyzer.validate_policy(
                locale="EN",
                policyDocument=doppler_role_policy_document,
                policyType="IDENTITY_POLICY",
            ).get("findings", [])
            if validation_findings:
                err = ["Findings detected during policy validation:"]
                for idx, finding in enumerate(validation_findings):
                    finding_type = finding["findingType"]
                    finding_details = finding["findingDetails"]
                    err.append(f"[Finding {idx}] {finding_type}: {finding_details}")
                raise RuntimeError("\n".join(err))
        except AWSClientError as e:
            self.logger.error(f"Failed to validate policy: {e}")
            raise

        # Create or update the IAM Role
        try:
            iam_client.create_role(
                AssumeRolePolicyDocument=assume_role_policy_document,
                Path="/",
                RoleName=role_name,
            )
            self.logger.info(f"Created IAM role {role_name}")
        except iam_client.exceptions.EntityAlreadyExistsException:
            self.logger.info(f"IAM role {role_name} already exists")
        except AWSClientError as e:
            self.logger.error(f"Failed to create IAM role {role_name}: {e}")
            raise

        # Get existing role details
        try:
            role = iam_client.get_role(RoleName=role_name)
            current_assume_role_policy = role["Role"]["AssumeRolePolicyDocument"]
        except AWSClientError as e:
            self.logger.error(f"Failed to retrieve IAM role {role_name}: {e}")
            raise

        # Update Assume Role Policy if necessary
        if current_assume_role_policy != json.loads(assume_role_policy_document):
            try:
                iam_client.update_assume_role_policy(RoleName=role_name, PolicyDocument=assume_role_policy_document)
                self.logger.info(f"Updated assume role policy for {role_name}")
            except AWSClientError as e:
                self.logger.error(f"Failed to update assume role policy for {role_name}: {e}")
                raise
        else:
            self.logger.info(f"Assume role policy for {role_name} is up-to-date")

        # Create or update the managed policy
        try:
            iam_client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=doppler_role_policy_document,
            )
            self.logger.info(f"Created managed policy {policy_name}")
        except iam_client.exceptions.EntityAlreadyExistsException:
            self.logger.info(f"Managed policy {policy_name} already exists")
        except AWSClientError as e:
            self.logger.error(f"Failed to create managed policy {policy_name}: {e}")
            raise

        # Get the existing policy document
        try:
            policy = iam_client.get_policy(PolicyArn=policy_arn)
            default_version_id = policy["Policy"]["DefaultVersionId"]
            policy_version = iam_client.get_policy_version(PolicyArn=policy_arn, VersionId=default_version_id)[
                "PolicyVersion"
            ]["Document"]
        except AWSClientError as e:
            self.logger.error(f"Failed to get policy {policy_name}: {e}")
            raise

        # Update policy if necessary
        if policy_version != json.loads(doppler_role_policy_document):
            # Check the number of policy versions
            try:
                versions = iam_client.list_policy_versions(PolicyArn=policy_arn)["Versions"]
                non_default_versions = [v for v in versions if not v["IsDefaultVersion"]]
                if len(versions) >= 5:
                    # Delete the oldest non-default version
                    oldest_version = sorted(non_default_versions, key=lambda x: x["CreateDate"])[0]
                    iam_client.delete_policy_version(PolicyArn=policy_arn, VersionId=oldest_version["VersionId"])
                    self.logger.info(f"Deleted old policy version {oldest_version['VersionId']} for {policy_name}")

                # Create a new policy version
                iam_client.create_policy_version(
                    PolicyArn=policy_arn, PolicyDocument=doppler_role_policy_document, SetAsDefault=True
                )
                self.logger.info(f"Created new policy version and set as default for {policy_name}")
            except AWSClientError as e:
                self.logger.error(f"Failed to update managed policy {policy_name}: {e}")
                raise
        else:
            self.logger.info(f"Managed policy {policy_name} is up-to-date")

        # Attach the managed policy to the role if not already attached
        try:
            attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)["AttachedPolicies"]
            if not any(p["PolicyArn"] == policy_arn for p in attached_policies):
                iam_client.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
                self.logger.info(f"Attached managed policy {policy_name} to role {role_name}")
            else:
                self.logger.info(f"Managed policy {policy_name} already attached to role {role_name}")
        except AWSClientError as e:
            self.logger.error(f"Failed to attach managed policy {policy_name} to role {role_name}: {e}")
            raise

        # Return the role information
        return self.exit_run(
            results=role["Role"],
            key="role",
            unhump_results=unhump_role,
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def get_vault_aws_iam_roles(self, exit_on_completion: bool = True):
        """Gets the Vault IAM roles across all AWS accounts

        generator=module_class: vault

        generator=key: roles, module_class: vault
        """

        self.logger.info("Getting the Vault AWS IAM role across AWS accounts")

        aws_accounts = self.get_gitops_repository_file(file_path="records/metadata/accounts_by_identifier.json")

        admin_principals = self.get_gitops_repository_file(file_path="records/metadata/admin_principals.json")

        if utils.is_nothing(admin_principals):
            raise RuntimeError("No admin principals found")

        assume_role_policy_document = utils.wrap_raw_data_for_export(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": admin_principals,
                            "Service": ["ec2.amazonaws.com"],
                        },
                        "Action": "sts:AssumeRole",
                    }
                ],
            },
            allow_encoding=False,
        )

        vault_role_policy_document = utils.wrap_raw_data_for_export(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "VaultSecrets",
                        "Effect": "Allow",
                        "Resource": ["*"],
                        "Action": [
                            "kms:Encrypt",
                            "kms:Decrypt",
                            "kms:DescribeKey",
                            "ec2:DescribeInstances",
                            "ssm:PutParameter",
                            "ssm:GetParameter",
                        ],
                    },
                    {
                        "Sid": "allowQueryingIAM",
                        "Effect": "Allow",
                        "Action": [
                            "iam:GetRole",
                            "iam:GetUser",
                            "sts:AssumeRole",
                        ],
                        "Resource": [
                            "arn:aws:iam::*:user/*",
                            "arn:aws:iam::*:role/*",
                        ],
                    },
                    {
                        "Sid": "allowGettingCallerIdentity",
                        "Effect": "Allow",
                        "Action": ["sts:GetCallerIdentity"],
                        "Resource": ["*"],
                    },
                    {
                        "Sid": "allowStsTagging",
                        "Effect": "Allow",
                        "Action": ["sts:TagSession"],
                        "Resource": ["*"],
                    },
                ],
            },
            allow_encoding=False,
        )

        access_analyzer = self.get_aws_client(client_name="accessanalyzer")

        validation_findings = access_analyzer.validate_policy(
            locale="EN",
            policyDocument=vault_role_policy_document,
            policyType="IDENTITY_POLICY",
        ).get("findings", [])

        if not utils.is_nothing(validation_findings):
            err = [
                "At least one finding found when running the access analyzer:",
            ]

            for idx, finding in enumerate(validation_findings):
                finding_type = finding["findingType"]
                finding_details = finding["findingDetails"]
                err.append(
                    self.logged_statement(
                        f"[Finding {idx}] {finding_type} {finding_details}",
                        json_data=finding,
                    )
                )

            err.append("Policy document:")
            err.append(utils.wrap_raw_data_for_export(vault_role_policy_document, allow_encoding=True))

            raise RuntimeError(os.linesep.join(err))

        def get_vault_role_for_account(ei: str, ed: Any):
            self.logger.info(f"Injecting Vault AWS IAM auth role for {ei}")
            jk = ed["json_key"]
            name = f"vault-auth-{jk}"
            execution_role_arn = ed.get("execution_role_arn")

            self.logger.info(f"Getting Vault role for account {jk}, execution role {execution_role_arn}")

            iam_client = self.get_aws_client(client_name="iam", execution_role_arn=execution_role_arn)

            try:
                iam_client.create_role(
                    AssumeRolePolicyDocument=assume_role_policy_document,
                    Path="/",
                    RoleName=name,
                )
            except iam_client.exceptions.EntityAlreadyExistsException:
                self.logger.warning(f"Role {name} already exists", exc_info=True)

            iam_rsrc = self.get_aws_resource(service_name="iam", execution_role_arn=execution_role_arn)

            role = iam_rsrc.Role(name)

            assume_role_policy = role.AssumeRolePolicy()
            assume_role_policy.update(PolicyDocument=assume_role_policy_document)

            role_policy = role.Policy(name)
            role_policy.put(PolicyDocument=vault_role_policy_document)

            managed_policies = [
                f"arn:aws:iam::aws:policy/{policy_name}"
                for policy_name in [
                    "AmazonSSMManagedInstanceCore",
                    "SecretsManagerReadWrite",
                ]
            ]

            policy_iterator = role.attached_policies.all()

            for policy in policy_iterator:
                policy_arn = policy.arn

                if policy_arn in managed_policies:
                    self.logger.info(f"{policy_arn} already attached to {name}")
                    managed_policies.remove(policy_arn)
                else:
                    self.logger.warning(f"Removing rogue policy {policy_arn} from {name}")
                    policy.detach_role(RoleName=role.name)

            for policy_arn in managed_policies:
                self.logger.info(f"Attaching {policy_arn} to {name}")
                role.attach_policy(PolicyArn=policy_arn)

            instance_profile_iterator = role.instance_profiles.all()

            instance_profile_attached_to_role = False
            for instance_profile in instance_profile_iterator:
                instance_profile_name = instance_profile.name

                if instance_profile_name != name:
                    self.logger.warning(
                        f"Rogue instance profile {instance_profile_name} is attached to the Vault role, removing it"
                    )
                    instance_profile.remove_role(RoleName=role.name)

                    if instance_profile.roles is None:
                        self.logger.warning(f"Removing instance profile {instance_profile_name}")
                        instance_profile.delete()
                else:
                    instance_profile_attached_to_role = True

            if not instance_profile_attached_to_role:
                try:
                    iam_client.create_instance_profile(
                        InstanceProfileName=name,
                    )
                except iam_client.exceptions.EntityAlreadyExistsException:
                    self.logger.warning(f"Instance profile {name} already exists", exc_info=True)

                instance_profile = iam_rsrc.InstanceProfile(name)
                self.logger.info(f"Attaching instance profile to {name}")
                instance_profile.add_role(RoleName=role.name)

            return jk, {
                "iam_role_name": role.name,
                "iam_role_arn": role.arn,
            }

        vault_roles = {}
        tic = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []

            for entity_id, entity_data in aws_accounts.items():
                if entity_data.get("unit") == "Suspended" or entity_data.get("status") == "SUSPENDED":
                    self.logger.warning(f"Skipping suspended account {entity_id}")
                    continue

                futures.append(executor.submit(get_vault_role_for_account, entity_id, entity_data))

            for future in concurrent.futures.as_completed(futures):
                try:
                    json_key, role_data = future.result()
                    if not utils.is_nothing(json_key) and not utils.is_nothing(role_data):
                        self.logger.info(f"Successfully read {json_key} role")
                        vault_roles[json_key] = role_data
                    else:
                        raise RuntimeError("Failed to get at least one Vault role")
                except Exception as exc:
                    executor.shutdown(wait=False, cancel_futures=True)
                    if isinstance(exc, AWSClientError):
                        raise FailedResponseError(exc, f"Failed to get roles: {vault_roles}") from exc

                    raise RuntimeError(f"Failed to get roles: {vault_roles}") from exc

        toc = time.perf_counter()
        self.logger.info(f"Getting Vault roles took {toc - tic:0.2f} seconds to run")

        return self.exit_run(
            results=vault_roles,
            key="roles",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def list_available_google_workspace_licenses(self, exit_on_completion: bool = True):
        """
        Lists all available license products and SKUs in Google Workspace

        generator=key: licenses, module_class: google
        """

        google_client = self.get_google_client()
        licensing = google_client.get_service("licensing", "v1")
        licenses = {}
        customer_id = "flipsidecrypto.com"

        # Enterprise Plus and Gemini Enterprise product IDs
        products = [
            {"productId": "101034", "name": "Google Workspace Enterprise Plus"},  # Google Workspace Enterprise Plus
            {"productId": "101047", "name": "Gemini Enterprise"},  # Gemini Enterprise
        ]

        try:
            for product in products:
                product_id = product["productId"]
                product_name = product["name"]

                self.logger.info(f"\nTrying Product: {product_name}")
                self.logger.info(f"Product ID: {product_id}")

                # Initialize product in licenses dictionary
                licenses[product_id] = {"name": product_name, "skus": {}}

                try:
                    # List licenses for the product
                    response = (
                        licensing.licenseAssignments()
                        .listForProduct(productId=product_id, customerId=customer_id)
                        .execute()
                    )

                    self.logger.info(f"Found licenses for {product_name}")

                    for item in response.get("items", []):
                        sku_id = item.get("skuId", "")
                        if not sku_id:
                            continue

                        if sku_id not in licenses[product_id]["skus"]:
                            licenses[product_id]["skus"][sku_id] = {
                                "name": sku_id,
                                "assignments": {"total": 0, "users": []},
                            }

                        # Add user to assignments
                        user_data = {
                            "user_id": item.get("userId", ""),
                            "self_link": item.get("selfLink", ""),
                            "sku_id": sku_id,
                            "product_id": product_id,
                        }

                        licenses[product_id]["skus"][sku_id]["assignments"]["users"].append(user_data)
                        licenses[product_id]["skus"][sku_id]["assignments"]["total"] += 1

                except googleapiclient.errors.HttpError as e:
                    error_message = str(e)
                    if "Resource Not Found" in error_message:
                        self.logger.info(f"Product {product_id} not found or not available")
                    else:
                        self.logger.error(f"Error listing licenses for product {product_id}: {error_message}")
                        licenses[product_id]["error"] = error_message

        except googleapiclient.errors.HttpError as e:
            raise RuntimeError("Error listing licenses") from e

        # Remove products with no data
        licenses = {
            k: v
            for k, v in licenses.items()
            if v.get("skus") or (v.get("error") and "Resource Not Found" not in v.get("error", ""))
        }

        return self.exit_run(
            results=licenses,
            key="licenses",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    # User Status & Type Management
    def _get_user_params(self, user_data: Dict) -> Tuple[str, bool, bool]:
        """Gets user parameters from user data.
        # NOPARSE
        """
        return (
            user_data.get("orgUnitPath", ""),
            user_data.get("archived", False),
            user_data.get("suspended", False),
        )

    def _get_user_type(self, user_data: Dict) -> Tuple[str, bool, bool, str]:
        """Determines user type and status.
        # NOPARSE
        """
        org_unit_path, archived, suspended = self._get_user_params(user_data)
        if org_unit_path.startswith("/Automation"):
            calculated_user_type = "bot"
        elif archived or suspended:
            calculated_user_type = "inactive"
        else:
            calculated_user_type = "active"
        return org_unit_path, archived, suspended, calculated_user_type

    def _onboard_new_users(
        self,
        directory_client,
        slack_client,
        onboard_users: Dict,
        existing_google_users: Dict,
    ) -> None:
        """Onboards new users to Google Workspace.
        # NOPARSE
        """

        def generate_password(length=12):
            characters = string.ascii_letters + string.digits + string.punctuation
            return "".join(secrets.choice(characters) for _ in range(length))

        for new_email, new_user_data in onboard_users.items():
            self.logger.info(f"Checking if {new_email} needs to be onboarded")
            if new_email in existing_google_users:
                self.logger.info(f"{new_email} has already been onboarded")
                continue

            initial_password = generate_password()
            try:
                user_body = self.merger.merge(
                    {
                        "primaryEmail": new_email,
                        "suspended": False,
                        "password": initial_password,
                        "changePasswordAtNextLogin": True,
                        "orgUnitPath": "/Users",
                        "includeInGlobalAddressList": True,
                    },
                    deepcopy(new_user_data),
                )

                existing_google_users[new_email] = directory_client.users().insert(body=user_body).execute()

                slack_client.send_message(
                    text="New Onboarding Event!",
                    channel_id="C07FCAX8Y2J",
                    lines=[
                        f"{new_email} has been onboarded at FlipsideCrypto",
                        f"Their initial password has been set as '{initial_password}', without the quotes.",
                        "A member of this channel will need to email them with their login instructions.",
                        "CC @Kerri @Will",
                    ],
                )
            except Exception as e:
                self.errors.append(f"Failed to onboard user {new_email} or notify channel: {e}")

    # License Management
    def _get_license_allocations(self, google_client) -> pd.DataFrame:
        """Gets and processes license allocations from the Google Sheet.
        # NOPARSE
        """
        google_client_credentials = google_client.get_credentials()
        sheets = gspread.Client(auth=google_client_credentials)
        license_allocations_worksheet = sheets.open_by_key("1mX6Z8hyOCarIkiOw7BuHqhb4Q_Jc9G5WBr3zSRS8-mQ")
        license_allocations_sheet = license_allocations_worksheet.sheet1
        return pd.DataFrame(license_allocations_sheet.get_all_records())

    def _manage_gemini_licenses(
        self,
        licensing_client,
        license_allocations: pd.DataFrame,
        existing_google_users: Dict,
        slack_users: Dict,
    ) -> list[str]:
        """Manages Gemini license assignments and returns Slack user IDs for the Gemini channel.
        # NOPARSE
        """
        current_licenses = self.list_available_google_workspace_licenses(exit_on_completion=False)
        gemini_assignments = set()
        if "101047" in current_licenses:
            for sku_data in current_licenses["101047"]["skus"].values():
                for assignment in sku_data["assignments"].get("users", []):
                    gemini_assignments.add(assignment["user_id"].lower())

        self._cleanup_inactive_gemini_licenses(licensing_client, gemini_assignments, existing_google_users)
        return self._process_gemini_assignments(
            licensing_client,
            license_allocations,
            existing_google_users,
            slack_users,
            gemini_assignments,
        )

    def _cleanup_inactive_gemini_licenses(
        self,
        licensing_client,
        gemini_assignments: Set[str],
        existing_google_users: Dict,
    ) -> None:
        """Removes Gemini licenses from inactive or old users.
        # NOPARSE
        """
        for email in gemini_assignments:
            if (
                email.endswith("-old@flipsidecrypto.com")
                or email not in existing_google_users
                or existing_google_users[email].get("archived")
                or existing_google_users[email].get("suspended")
            ):
                try:
                    licensing_client.licenseAssignments().delete(
                        productId="101047", skuId="1010470001", userId=email
                    ).execute()
                    self.logger.info(f"Removed Gemini license from inactive/old user: {email}")
                except googleapiclient.errors.HttpError as e:
                    self.errors.append(f"Failed to remove Gemini license from user {email}: {e}")

    def _process_gemini_assignments(
        self,
        licensing_client,
        license_allocations: pd.DataFrame,
        existing_google_users: Dict,
        slack_users: Dict,
        gemini_assignments: Set[str],
    ) -> list[str]:
        """Process Gemini license assignments and returns list of Slack user IDs.
        # NOPARSE
        """
        gemini_channel_user_ids = []
        for email in license_allocations["Email"]:
            email = email.strip().lower()

            # Handle Slack channel membership
            if email not in slack_users:
                self.logger.warning(f"Email {email} not found in Slack and must be added manually")
            else:
                slack_userid = slack_users[email]["slack_userid"]
                self.logger.info(f"User {email} found on Slack: {slack_userid}")
                gemini_channel_user_ids.append(slack_userid)

            # Skip license assignment for inactive users
            if (
                email not in existing_google_users
                or existing_google_users[email].get("archived")
                or existing_google_users[email].get("suspended")
            ):
                self.logger.warning(f"Skipping Gemini license for inactive user: {email}")
                continue

            # Skip if already licensed
            if email in gemini_assignments:
                self.logger.info(f"{email} already has a Gemini license")
                continue

            try:
                licensing_client.licenseAssignments().insert(
                    productId="101047", skuId="1010470001", body={"userId": email}
                ).execute()
                self.logger.info(f"Assigned Gemini license to user {email}")
            except googleapiclient.errors.HttpError as e:
                self.errors.append(f"Failed to assign Gemini license to user {email}: {e}")

        return gemini_channel_user_ids

    # Vendor Integration Management
    def _handle_aws_account_assignment(
        self,
        directory_client,
        group_name: str,
        member_email: str,
        existing_google_users: Dict,
    ) -> None:
        """Assigns AWS account name to user's custom schema.
        # NOPARSE
        """
        aws_username = "User-" + member_email.split("@")[0].lower().replace(".", "_")

        custom_schemas = deepcopy(existing_google_users[member_email].get("customSchemas", {}))
        if "VendorAttributes" not in custom_schemas:
            custom_schemas["VendorAttributes"] = {}

        if not custom_schemas["VendorAttributes"].get("awsAccountName"):
            custom_schemas["VendorAttributes"]["awsAccountName"] = aws_username
            try:
                directory_client.users().update(userKey=member_email, body={"customSchemas": custom_schemas}).execute()
                self.logger.info(f"Assigned AWS username {aws_username} to {member_email}")
            except googleapiclient.errors.HttpError as e:
                self.errors.append(f"Failed to assign AWS username to {member_email}: {e}")

    def _populate_custom_schema_field(
        self,
        schema_user_email: str,
        field_schema_name: str,
        schema_field_name: str,
        field_value: str,
        existing_google_users: dict[str, Any],
    ) -> bool:
        """Populates a custom schema field for a user.
        # NOPARSE
        """
        if not field_value:
            return False

        custom_schemas = deepcopy(existing_google_users[schema_user_email].get("customSchemas", {}))
        if field_schema_name not in custom_schemas:
            custom_schemas[field_schema_name] = {}

        stored_schema_value = custom_schemas[field_schema_name].get(schema_field_name)
        if not utils.is_nothing(stored_schema_value):
            self.logger.warning(
                f"User {schema_user_email} custom schema {field_schema_name} field {schema_field_name} already has a value: '{stored_schema_value}'"
            )
            return False

        custom_schemas[field_schema_name][schema_field_name] = field_value
        existing_google_users[schema_user_email]["customSchemas"] = custom_schemas
        return True

    def _ensure_custom_schemas(self, directory_client) -> None:
        """Ensures required custom schemas exist and are up to date.
        # NOPARSE
        """
        existing_schemas = {
            schema["schemaName"]: schema
            for schema in directory_client.schemas().list(customerId="my_customer").execute().get("schemas", [])
        }

        required_schemas = {
            "VendorAttributes": ["githubUsername", "awsAccountName"],
        }

        for schema_name, schema_fields in required_schemas.items():
            self.logger.info(f"Ensuring that custom schema {schema_name} exists and is up to date")
            existing_schema = existing_schemas.get(schema_name)

            if existing_schema:
                # Track updates and deletions needed
                fields_to_add = []
                fields_to_delete = []
                existing_fields = {field["fieldName"]: field for field in existing_schema.get("fields", [])}

                # Identify fields to add
                for required_field in schema_fields:
                    if required_field not in existing_fields:
                        fields_to_add.append(
                            {
                                "fieldName": required_field,
                                "fieldType": "STRING",
                                "multiValued": False,
                                "readAccessType": "ADMINS_AND_SELF",
                            }
                        )

                # Identify fields to delete
                for existing_field_name in existing_fields.keys():
                    if existing_field_name not in schema_fields:
                        fields_to_delete.append(existing_field_name)

                # Remove extra fields if any
                if fields_to_delete:
                    self.logger.warning(f"Removing extra fields from {schema_name}: {fields_to_delete}")
                    for field_to_delete in fields_to_delete:
                        try:
                            directory_client.schemas().delete(
                                customerId="my_customer",
                                schemaKey=existing_schema["schemaId"],
                                body={"fields": [{"fieldName": field_to_delete}]},
                            ).execute()
                            self.logger.info(f"Field {field_to_delete} removed from {schema_name}")
                        except googleapiclient.errors.HttpError as e:
                            self.errors.append(f"Failed to delete field {field_to_delete} in {schema_name}: {e}")

                # Add missing fields if any
                if fields_to_add:
                    self.logger.info(f"Adding new fields to {schema_name}: {fields_to_add}")
                    try:
                        directory_client.schemas().patch(
                            customerId="my_customer",
                            schemaKey=existing_schema["schemaId"],
                            body={"fields": fields_to_add},
                        ).execute()
                        self.logger.info(f"New fields added to {schema_name}: {fields_to_add}")
                    except googleapiclient.errors.HttpError as e:
                        self.errors.append(f"Failed to add fields in {schema_name}: {e}")
            else:
                # Schema does not exist, create it
                self.logger.info(f"Creating {schema_name} custom schema")
                schema_body = {
                    "schemaName": schema_name,
                    "fields": [
                        {
                            "fieldName": field_name,
                            "fieldType": "STRING",
                            "multiValued": False,
                            "readAccessType": "ADMINS_AND_SELF",
                        }
                        for field_name in schema_fields
                    ],
                }
                try:
                    directory_client.schemas().insert(customerId="my_customer", body=schema_body).execute()
                    self.logger.info(f"{schema_name} custom schema created successfully.")
                except googleapiclient.errors.HttpError as e:
                    self.errors.append(f"Failed to create {schema_name} custom schema: {e}")

    def get_flipsidecrypto_users_and_groups_with_github(
        self,
        existing_google_users: Optional[Dict[str, Any]] = None,
        existing_github_users: Optional[Dict[str, Any]] = None,
        exit_on_completion: bool = True,
    ):
        """Syncs FlipsideCrypto users and groups with GitHub data

        generator=key: users_with_github, module_class: gitops

        name: existing_google_users, required: false, json_encode: true, base64_encode: true
        name: existing_github_users, required: false, json_encode: true, base64_encode: true
        """

        self.logger.info("Syncing FlipsideCrypto users with GitHub data")

        # Handle inputs
        if existing_google_users is None:
            existing_google_users = self.decode_input(
                "existing_google_users",
                required=False,
                default={},
                allow_none=False,
            )

        if existing_github_users is None:
            existing_github_users = self.decode_input(
                "existing_github_users",
                required=False,
                default={},
                allow_none=False,
            )

        # If inputs are empty, fetch them
        if not existing_google_users:
            existing_google_users = self.get_google_users(unhump_users=False, exit_on_completion=False)

        if not existing_github_users:
            existing_github_users = self.get_github_users(
                exit_on_completion=False,
            )

        # Get directory service for updating custom schemas
        google_client = self.get_google_client()
        directory = google_client.get_service("admin", "directory_v1")

        # Build GitHub users by email map
        github_users_by_email = {
            user_data["primary_email"]: user_data
            for user_data in existing_github_users.values()
            if user_data.get("primary_email")
        }

        # Ensure custom schemas exist
        self._ensure_custom_schemas(
            directory,
            existing_google_users,
            required_schemas={
                "VendorAttributes": ["githubUsername", "awsAccountName"],
            },
        )

        # Track users with schema updates
        users_with_schema_updates = set()

        # Process each user for GitHub integration
        for google_email, user_data in deepcopy(existing_google_users).items():
            org_unit_path, archived, suspended, user_type = self._get_user_type(user_data)

            # Skip bot users
            if user_type == "bot":
                self.logger.warning(f"Skipping bot user {google_email}")
                continue

            # Handle GitHub username in custom schema
            github_user_data = github_users_by_email.get(google_email)
            if github_user_data:
                github_username = github_user_data.get("login")
                if github_username:
                    if self._populate_custom_schema_field(
                        google_email,
                        "VendorAttributes",
                        "githubUsername",
                        github_username,
                        existing_google_users,
                    ):
                        users_with_schema_updates.add(google_email)

        # Update users with schema changes
        for email in users_with_schema_updates:
            try:
                user_custom_schema_data = existing_google_users[email].get("customSchemas", {})
                directory.users().update(userKey=email, body={"customSchemas": user_custom_schema_data}).execute()
                self.logger.info(f"Updated GitHub schema for user {email}")
            except googleapiclient.errors.HttpError as e:
                self.errors.append(f"Failed to update GitHub schema for {email}: {e}")

        # Return updated users with GitHub data
        return self.exit_run(
            results=existing_google_users,
            key="users_with_github",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def get_flipsidecrypto_users_and_groups_with_zoom(
        self,
        existing_google_users: Optional[Dict[str, Any]] = None,
        exit_on_completion: bool = True,
    ):
        """Syncs FlipsideCrypto users with Zoom

        generator=key: users_with_zoom, module_class: gitops

        name: existing_google_users, required: false, json_encode: true, base64_encode: true
        """
        self.logger.info("Syncing FlipsideCrypto users with Zoom")

        # Handle inputs
        if existing_google_users is None:
            existing_google_users = self.decode_input(
                "existing_google_users",
                required=False,
                default={},
                allow_none=False,
            )

        # If inputs are empty, fetch them
        if not existing_google_users:
            existing_google_users = self.get_google_users(unhump_users=False, exit_on_completion=False)

        # Get Zoom client
        zoom_client = self.get_zoom_client()
        zoom_users = zoom_client.get_zoom_users()

        # Track errors
        errors = []

        # Process each user for Zoom integration
        for google_email, user_data in deepcopy(existing_google_users).items():
            org_unit_path, archived, suspended, user_type = self._get_user_type(user_data)

            # Skip bot users
            if user_type == "bot":
                self.logger.warning(f"Skipping bot user {google_email}")
                continue

            # Get user name information
            first_name = user_data.get("name", {}).get("givenName", "")
            last_name = user_data.get("name", {}).get("familyName", "")

            # Handle Zoom access
            if google_email in zoom_users:
                if suspended or archived:
                    self.logger.warning(f"Removing suspended/archived user {google_email} from Zoom")
                    try:
                        zoom_client.remove_zoom_user(google_email)
                    except Exception as e:
                        errors.append(f"Failed to remove {google_email} from Zoom: {e}")
                else:
                    self.logger.info(f"User {google_email} already exists in Zoom")
                    # Update Zoom user information if needed
                    try:
                        zoom_client.update_zoom_user(google_email, first_name, last_name)
                    except Exception as e:
                        self.logger.warning(f"Failed to update Zoom user {google_email}: {e}")
            elif not suspended and not archived:
                self.logger.info(f"Creating Zoom user {google_email}")
                try:
                    zoom_client.create_zoom_user(google_email, first_name, last_name)
                    user_data["has_zoom_access"] = True
                except Exception as e:
                    errors.append(f"Failed to create Zoom user {google_email}: {e}")

            # Update user data with Zoom access information
            user_data["has_zoom_access"] = google_email in zoom_users and not (suspended or archived)

        # Add errors to self.errors
        for error in errors:
            self.errors.append(error)

        # Return updated users with Zoom data
        return self.exit_run(
            results=existing_google_users,
            key="users_with_zoom",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def get_flipsidecrypto_team_membership(
        self,
        existing_google_users: Optional[Dict[str, Any]] = None,
        existing_google_groups: Optional[Dict[str, Any]] = None,
        calendar_shares_by_email: Optional[Dict[str, Any]] = None,
        exit_on_completion: bool = True,
    ):
        """Syncs FlipsideCrypto team membership and calendar access

        generator=key: team_membership, module_class: gitops

        name: existing_google_users, required: false, json_encode: true, base64_encode: true
        name: existing_google_groups, required: false, json_encode: true, base64_encode: true
        name: calendar_shares_by_email, required: false, json_encode: true, base64_encode: true
        """
        self.logger.info("Syncing FlipsideCrypto team membership and calendar access")

        # Handle inputs
        if existing_google_users is None:
            existing_google_users = self.decode_input(
                "existing_google_users",
                required=False,
                default={},
                allow_none=False,
            )

        if existing_google_groups is None:
            existing_google_groups = self.decode_input(
                "existing_google_groups",
                required=False,
                default={},
                allow_none=False,
            )

        if calendar_shares_by_email is None:
            calendar_shares_by_email = self.decode_input(
                "calendar_shares_by_email",
                required=False,
                default={},
                allow_none=False,
            )

        # If inputs are empty, fetch them
        if not existing_google_users:
            existing_google_users = self.get_google_users(unhump_users=False, exit_on_completion=False)

        if not existing_google_groups:
            existing_google_groups = self.get_google_groups(
                unhump_groups=False,
                sort_by_name=True,
                prefix=False,
                exit_on_completion=False,
            )

        if not calendar_shares_by_email:
            calendar_shares_by_email = self.get_flipsidecrypto_team_calendar_shares(exit_on_completion=False)

        # Get Google clients
        google_client = self.get_google_client()
        directory = google_client.get_service("admin", "directory_v1")
        calendar = google_client.get_service("calendar", "v3")

        # 3. Group memberships - Fixed to handle list structure
        group_memberships = defaultdict(set)
        for group_name, group_data in existing_google_groups.items():
            self.logger.info(f"Checking group memberships for {group_name}")
            for member in group_data.get("members", []):
                member_email = member.get("email")

                if not member_email:
                    continue

                if member.get("status") != "ACTIVE":
                    self.logger.warning(f"Skipping {group_name} member {member_email}, member not active: {member}")
                    continue

                if member.get("type") != "USER":
                    self.logger.warning(f"Skipping {group_name} member {member_email}, member not a user: {member}")
                    continue

                group_memberships[member_email].add(group_name)

        # Track errors
        errors = []

        # Process each user for team membership and calendar access
        for google_email, user_data in deepcopy(existing_google_users).items():
            org_unit_path, archived, suspended, user_type = self._get_user_type(user_data)

            # Skip bot users
            if user_type == "bot":
                self.logger.warning(f"Skipping bot user {google_email}")
                continue

            # Add group membership data to user_data
            user_data["groups"] = list(group_memberships.get(google_email, set()))

            # Handle Team group membership
            if not suspended and not archived:
                try:
                    directory.members().insert(
                        groupKey="team@flipsidecrypto.com",
                        body={"email": google_email, "role": "MEMBER"},
                    ).execute()
                    self.logger.info(f"Added {google_email} to Team")
                except googleapiclient.errors.HttpError as e:
                    if "Member already exists" in str(e):
                        self.logger.info(f"{google_email} is already a member of Team")
                    else:
                        errors.append(f"Failed to add {google_email} to Team: {e}")

            # Handle Team calendar access
            is_in_calendar = google_email in calendar_shares_by_email

            if is_in_calendar:
                rule_id = calendar_shares_by_email[google_email]["id"]
                if suspended or archived:
                    self.logger.warning(f"Removing suspended/archived user {google_email} from Team calendar")
                    try:
                        calendar.acl().delete(calendarId=self.TEAM_CALENDAR_ID, ruleId=rule_id).execute()
                    except Exception as e:
                        errors.append(f"Failed to remove {google_email} from calendar: {e}")
                else:
                    self.logger.info(f"{google_email} is already in the Team calendar")
            elif not suspended and not archived:
                self.logger.info(f"Adding {google_email} to team calendar")
                rule = {
                    "scope": {
                        "type": "user",
                        "value": google_email,
                    },
                    "role": "writer",
                }
                try:
                    created_rule = calendar.acl().insert(calendarId=self.TEAM_CALENDAR_ID, body=rule).execute()
                    self.logger.info(f"Created new calendar rule: {created_rule['id']}")
                except Exception as e:
                    errors.append(f"Failed to add {google_email} to calendar: {e}")

            # Update user data with calendar access information
            user_data["has_calendar_access"] = google_email in calendar_shares_by_email and not (suspended or archived)

        # Clean up group memberships (remove suspended/archived users from groups)
        for group_name, group_data in existing_google_groups.items():
            self.logger.info(f"Syncing Google group {group_name}")
            group_email = group_data["email"]

            for member in group_data.get("members", []):
                member_email = member.get("email")

                if not member_email:
                    continue

                if not member_email.endswith("@flipsidecrypto.com"):
                    self.logger.warning(f"Ignoring external member {member_email}")
                    continue

                member_data = existing_google_users.get(member_email, {})
                if member_data:
                    _, member_archived, member_suspended, _ = self._get_user_type(member_data)

                    if member_suspended or member_archived:
                        self.logger.warning(f"Member {member_email} is suspended or archived")
                        try:
                            directory.members().delete(groupKey=group_email, memberKey=member_email).execute()
                            self.logger.info(f"Removed {member_email} from {group_name}")
                        except googleapiclient.errors.HttpError as e:
                            errors.append(f"Failed to remove {member_email} from {group_name}: {e}")
                else:
                    self.logger.warning(f"Member {member_email} is not a user")
                    try:
                        directory.members().delete(groupKey=group_email, memberKey=member_email).execute()
                        self.logger.info(f"Removed {member_email} from {group_name}")
                    except googleapiclient.errors.HttpError as e:
                        errors.append(f"Failed to remove {member_email} from {group_name}: {e}")

        # Add errors to self.errors
        for error in errors:
            self.errors.append(error)

        # Return updated users and groups with team and calendar info
        team_membership = {
            "users": existing_google_users,
            "groups": existing_google_groups,
            "calendar_shares": calendar_shares_by_email,
        }

        return self.exit_run(
            results=team_membership,
            key="team_membership",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    # Main Sync Method
    def get_flipsidecrypto_users_and_groups(
        self,
        get_team_membership: Optional[bool] = None,
        get_github: Optional[bool] = None,
        get_zoom: Optional[bool] = None,
        ensure_schemas: Optional[bool] = None,
        exit_on_completion: bool = True,
    ):
        """Syncs FlipsideCrypto users and groups with configurable options to enable/disable features

        generator=key: users_and_groups, module_class: gitops

        name: get_team_membership, required: false, default: false, type: bool
        name: get_github, required: false, default: false, type: bool
        name: get_zoom, required: false, default: false, type: bool
        name: ensure_schemas, required: false, default: true, type: bool
        """

        self.logger.info("Starting FlipsideCrypto users and groups sync")

        # Handle optional boolean inputs
        if get_team_membership is None:
            get_team_membership = self.get_input("get_team_membership", required=False, default=False, is_bool=True)

        if get_github is None:
            get_github = self.get_input("get_github", required=False, default=False, is_bool=True)

        if get_zoom is None:
            get_zoom = self.get_input("get_zoom", required=False, default=False, is_bool=True)

        if ensure_schemas is None:
            ensure_schemas = self.get_input("ensure_schemas", required=False, default=True, is_bool=True)

        # Initialize Google client (always needed)
        google_client = self.get_google_client()
        directory = google_client.get_service("admin", "directory_v1")

        # Get user data (always needed)
        existing_google_users = self.get_google_users(unhump_users=False, exit_on_completion=False)

        # Process users and handle status changes - this is the core functionality
        failed_to_archive = []

        for google_email, user_data in deepcopy(existing_google_users).items():
            # Get user status
            org_unit_path, archived, suspended, user_type = self._get_user_type(user_data)

            # Skip bot users
            if user_type == "bot":
                self.logger.warning(f"Skipping bot user {google_email}")
                continue

            # Handle user status changes - limited access moves
            if (suspended or archived) and not org_unit_path.endswith("LimitedAccess"):
                try:
                    directory.users().update(userKey=google_email, body={"orgUnitPath": "/LimitedAccess"}).execute()
                    self.logger.info(f"Moved user {google_email} to LimitedAccess")
                    org_unit_path = "/LimitedAccess"
                except googleapiclient.errors.HttpError as e:
                    self.errors.append(f"Failed to move user {google_email} to LimitedAccess: {e}")
                    continue

            # Handle archiving
            if org_unit_path.endswith("LimitedAccess") and not archived:
                try:
                    directory.users().update(
                        userKey=google_email,
                        body={"archived": True, "suspended": False},
                    ).execute()
                    self.logger.info(f"Archived user: {google_email}")
                    archived = True
                    suspended = False
                except googleapiclient.errors.HttpError as e:
                    self.logger.error(f"Failed to archive user {google_email}: {e}")
                    failed_to_archive.append(google_email)

        # Handle archive failures
        if failed_to_archive:
            raise RuntimeError(
                f"Users: {', '.join(failed_to_archive)}, failed to archive. Please purchase {len(failed_to_archive)} archive licenses and rerun."
            )

        # Process custom schemas if enabled
        if ensure_schemas:
            # Call the _ensure_custom_schemas method or inline the schema check code
            self._ensure_custom_schemas(directory)

        # Prepare to collect data sources for merging
        data_sources = []

        # Optional: Sync team membership and calendar access
        if get_team_membership:
            self.logger.info("Syncing team membership and calendar access")
            team_result = self.get_flipsidecrypto_team_membership(
                existing_google_users=existing_google_users, exit_on_completion=False
            )
            data_sources.append(team_result.get("users", {}))

        # Optional: Sync GitHub integration
        if get_github:
            self.logger.info("Syncing GitHub integration")
            github_result = self.get_flipsidecrypto_users_and_groups_with_github(
                existing_google_users=existing_google_users, exit_on_completion=False
            )
            data_sources.append(github_result)

        # Optional: Sync Zoom integration
        if get_zoom:
            self.logger.info("Syncing Zoom integration")
            zoom_result = self.get_flipsidecrypto_users_and_groups_with_zoom(
                existing_google_users=existing_google_users, exit_on_completion=False
            )
            data_sources.append(zoom_result)

        # Merge all data sources with the original user data
        if data_sources:
            self.logger.info(f"Merging {len(data_sources)} data sources with user data")

            # Use deepmerge to combine all sources
            merged_users = self.deepmerge(source_maps=data_sources + [existing_google_users], exit_on_completion=False)

            existing_google_users = merged_users

        # Get group data (needed for final output)
        existing_google_groups = self.get_google_groups(
            unhump_groups=False,
            sort_by_name=True,
            prefix=False,
            exit_on_completion=False,
        )

        # Build group memberships map
        group_memberships = defaultdict(set)
        for group_name, group_data in existing_google_groups.items():
            for member in group_data.get("members", []):
                member_email = member.get("email")

                if not member_email:
                    continue

                if member.get("status") != "ACTIVE" or member.get("type") != "USER":
                    continue

                group_memberships[member_email].add(group_name)

        # Filter active users and build Terraform-like structure
        active_users = {}

        for google_email, user_data in existing_google_users.items():
            org_unit_path, archived, suspended, user_type = self._get_user_type(user_data)

            is_in_allowed_ou = org_unit_path in ["/Contract", "/Users"] or org_unit_path.startswith("/Users/")
            is_active = not suspended and not archived

            if is_in_allowed_ou and is_active:
                first_name = user_data.get("name", {}).get("givenName", "")
                last_name = user_data.get("name", {}).get("familyName", "")

                # Create a structure similar to what Terraform would produce
                active_users[google_email] = {
                    "id": user_data.get("id", ""),
                    "primary_email": google_email,
                    "name": {
                        "given_name": first_name,
                        "family_name": last_name,
                        "full_name": f"{first_name} {last_name}",
                    },
                    "org_unit_path": org_unit_path,
                    "suspended": suspended,
                    "archived": archived,
                    "groups": list(group_memberships.get(google_email, set())),
                    "has_calendar_access": user_data.get("has_calendar_access", False),
                    "has_zoom_access": user_data.get("has_zoom_access", False),
                    "github_username": user_data.get("github_username", ""),
                    "custom_attributes": user_data.get("customSchemas", {}),
                }

        # Create the groups structure
        groups = {
            group_name: {
                "id": group_data.get("id", ""),
                "email": group_data.get("email", ""),
                "name": group_name,
                "description": group_data.get("description", ""),
                "members": [
                    member.get("email")
                    for member in group_data.get("members", [])
                    if member.get("status") == "ACTIVE"
                    and member.get("type") == "USER"
                    and member.get("email") in active_users
                ],
            }
            for group_name, group_data in existing_google_groups.items()
        }

        # Final data structure
        users_and_groups = {"active_users": active_users, "groups": groups}

        return self.exit_run(
            results=users_and_groups,
            key="users_and_groups",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )

    def get_terraform_pipeline_providers_config(
        self,
        workspaces_template_variables_config: Optional[dict[str, Any]] = None,
        workspace_sops_config: Optional[dict[str, Any]] = None,
        exit_on_completion: bool = True,
    ):
        """Processes ALL terraform-pipeline provider configurations, replacing all complex Terraform logic with Python

        generator=key: providers_tf_json, module_class: terraform

        name: workspaces_template_variables_config, required: true, json_encode: true, base64_encode: true
        name: workspace_sops_config, required: false, default: {}, json_encode: true, base64_encode: true
        """
        if workspaces_template_variables_config is None:
            workspaces_template_variables_config = self.decode_input(
                "workspaces_template_variables_config", required=True, allow_none=False
            )

        if workspace_sops_config is None:
            workspace_sops_config = self.decode_input(
                "workspace_sops_config", required=False, default={}, allow_none=False
            )

        self.logger.info("Processing ALL terraform-pipeline provider configurations in Python")

        def process_vendor_params_recursive(
            params: dict[str, Any], max_depth: int = 3, current_depth: int = 0
        ) -> dict[str, Any]:
            """Recursively process vendor parameters with depth limit"""
            result = {}

            if not params or current_depth >= max_depth:
                return result

            for key, value in params.items():
                if isinstance(value, dict):
                    result[key] = process_vendor_params_recursive(value, max_depth, current_depth + 1)
                elif isinstance(value, str):
                    result[key] = f"${{local.vendors_data.{value}}}"
                else:
                    result[key] = value

            return result

        # Process all workspace configurations
        providers_tf_json = {}

        for workspace_name, workspace_config in workspaces_template_variables_config.items():
            self.logger.info(f"Processing workspace: {workspace_name}")

            # 1. Build AWS provider configurations
            aws_providers = []

            # Base AWS provider for each region
            for aws_region in workspace_config.get("aws_provider_regions", []):
                base_config = {
                    "region": aws_region,
                    "skip_metadata_api_check": True,
                    "skip_region_validation": True,
                    "skip_credentials_validation": True,
                }

                # Add ignore_tags if configured
                ignore_tags = workspace_config.get("aws_provider_ignore_tags", {})
                if ignore_tags.get("keys") or ignore_tags.get("key_prefixes"):
                    base_config["ignore_tags"] = ignore_tags

                # Add alias if not the backend region
                if aws_region != workspace_config.get("backend_region"):
                    base_config["alias"] = aws_region

                # Add assume_role if bind_to_account is configured
                bind_to_account = workspace_config.get("bind_to_account")
                if bind_to_account:
                    base_config["assume_role"] = {"role_arn": bind_to_account}

                aws_providers.append(base_config)

                # Create aliased providers for each account
                for account_alias, execution_role_arn in workspace_config.get("accounts", {}).items():
                    alias_config = base_config.copy()
                    if "alias" in base_config:
                        alias_config["alias"] = f"{account_alias}_{base_config['alias']}"
                    else:
                        alias_config["alias"] = account_alias

                    if execution_role_arn:
                        alias_config["assume_role"] = {"role_arn": execution_role_arn}

                    aws_providers.append(alias_config)

            # 2. Process vendor providers
            vendor_providers = {}
            aliased_vendor_providers = []

            providers_config = workspace_config.get("provider_config", {})
            enabled_providers = workspace_config.get("providers", [])

            for provider_name in enabled_providers:
                if provider_name == "aws":
                    continue  # AWS handled separately

                provider_config = providers_config.get(provider_name, {})
                parameters = provider_config.get("parameters", {})

                if not parameters:
                    continue

                # Check if provider has aliases
                aliases = parameters.get("aliases", {})

                if aliases:
                    # Handle aliased provider
                    default_alias_config = None

                    for alias_name, alias_params in aliases.items():
                        config = {}

                        # Add base static config
                        config.update(parameters.get("static", {}))

                        # Add alias-specific static config
                        config.update(alias_params.get("static", {}))

                        # Process base vendor parameters
                        base_vendor = parameters.get("vendor", {})
                        if base_vendor:
                            config.update(process_vendor_params_recursive(base_vendor))

                        # Process alias-specific vendor parameters
                        alias_vendor = alias_params.get("vendor", {})
                        if alias_vendor:
                            config.update(process_vendor_params_recursive(alias_vendor))

                        # Process base vendor_blocks
                        base_vendor_blocks = parameters.get("vendor_blocks", {})
                        for k, v in base_vendor_blocks.items():
                            config[k] = {i: f"${{local.vendors_data.{j}}}" for i, j in v.items()}

                        # Process alias-specific vendor_blocks
                        alias_vendor_blocks = alias_params.get("vendor_blocks", {})
                        for k, v in alias_vendor_blocks.items():
                            config[k] = {i: f"${{local.vendors_data.{j}}}" for i, j in v.items()}

                        # Add alias
                        config["alias"] = alias_name

                        aliased_vendor_providers.append({"provider_name": provider_name, "config": config})

                        # Check if this alias is marked as default
                        is_default = alias_params.get("default", False)
                        if is_default:
                            self.logger.info(
                                f"Alias '{alias_name}' for provider '{provider_name}' is marked as default"
                            )
                            # Save this config for creating a non-aliased version
                            default_alias_config = config.copy()

                    # If we found a default alias, create a non-aliased provider with its config
                    if default_alias_config:
                        # Remove the alias from the config to make it the default provider
                        default_config = {k: v for k, v in default_alias_config.items() if k != "alias"}
                        vendor_providers[provider_name] = default_config
                        self.logger.info(
                            f"Created default (non-aliased) provider for '{provider_name}' from default alias"
                        )
                else:
                    # Handle regular (non-aliased) provider
                    config = {}

                    # Add static config
                    config.update(parameters.get("static", {}))

                    # Process vendor parameters
                    vendor_params = parameters.get("vendor", {})
                    if vendor_params:
                        config.update(process_vendor_params_recursive(vendor_params))

                    # Process vendor_blocks
                    vendor_blocks = parameters.get("vendor_blocks", {})
                    for k, v in vendor_blocks.items():
                        config[k] = {i: f"${{local.vendors_data.{j}}}" for i, j in v.items()}

                    if config:  # Only add if we have configuration
                        vendor_providers[provider_name] = config

            # 3. Transform aliased providers to expected format and merge with defaults
            aliased_providers_by_name = {}
            for aliased_config in aliased_vendor_providers:
                provider_name = aliased_config["provider_name"]
                if provider_name not in aliased_providers_by_name:
                    aliased_providers_by_name[provider_name] = []
                aliased_providers_by_name[provider_name].append(aliased_config["config"])

            # Merge default (non-aliased) providers with aliased providers
            for provider_name, default_config in vendor_providers.items():
                if provider_name in aliased_providers_by_name:
                    # Provider has both default and aliases - prepend default to the list
                    self.logger.info(
                        f"Merging default provider '{provider_name}' with its {len(aliased_providers_by_name[provider_name])} aliases"
                    )
                    aliased_providers_by_name[provider_name].insert(0, default_config)
                else:
                    # Provider only has default config - keep as dict, not list
                    aliased_providers_by_name[provider_name] = default_config

            # 4. Add SOPS provider if configured
            sops_config = workspace_sops_config.get(workspace_name, {})
            sops_provider = {}
            if sops_config:
                sops_provider = {"sops": [{"kms": sops_config}]}

            # 5. Handle enable/disable logic
            disable_providers_requiring_secrets = workspace_config.get(
                "disable_providers_requiring_secrets", False
            ) or workspace_config.get("disable_vendors_module", False)

            disable_providers = workspace_config.get("disable_providers", False)

            # 6. Build required_providers configuration
            required_providers = {}
            for provider_name in enabled_providers:
                provider_info = providers_config.get(provider_name, {})
                if not provider_info:
                    continue

                # Check if we should include this provider
                should_include = True
                if disable_providers_requiring_secrets:
                    if provider_name == "aws":
                        should_include = True  # AWS always included
                    else:
                        # Check if provider has vendor configs that would be disabled
                        has_vendor = provider_info.get("parameters", {}).get("vendor") is not None
                        has_vendor_blocks = provider_info.get("parameters", {}).get("vendor_blocks") is not None
                        if has_vendor or has_vendor_blocks:
                            should_include = False

                if should_include:
                    required_providers[provider_name] = {
                        "source": provider_info["source"],
                        "version": f"{workspace_config.get('provider_version_constraint', '~>')} {provider_info['version']}",
                    }

            # 7. Build final provider configuration
            final_config = {}

            if not disable_providers:
                # Providers enabled
                providers_config_final = {}

                # Add AWS providers
                providers_config_final["aws"] = aws_providers

                # Add vendor providers (if not disabled)
                if not disable_providers_requiring_secrets:
                    providers_config_final.update(aliased_providers_by_name)

                # Add SOPS provider
                providers_config_final.update(sops_provider)

                final_config = {
                    "provider": providers_config_final,
                    "terraform": {"required_providers": required_providers},
                }
            else:
                # Providers disabled - only terraform config
                final_config = {"terraform": {"required_providers": required_providers}}

            providers_tf_json[workspace_name] = final_config

        self.log_results(providers_tf_json, "processed terraform-pipeline providers config")

        return self.exit_run(
            results=providers_tf_json,
            key="providers_tf_json",
            encode_to_base64=True,
            format_json=False,
            exit_on_completion=exit_on_completion,
        )
