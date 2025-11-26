from typing import Any, Optional, Union

from github import Auth, Github
from github.GithubException import GithubException, UnknownObjectException
from python_graphql_client import GraphqlClient

from cloud_connectors.base import utils
from cloud_connectors.base.utils import Utils, FilePath, wrap_raw_data_for_export, is_nothing, get_encoding_for_file_path


def get_github_api_error(exc):
    data = getattr(exc, "data", {})

    return data.get("message", None)


DEFAULT_PER_PAGE = 100


class GithubConnector(Utils):
    def __init__(
            self,
            github_owner: str,
            github_repo: Optional[str] = None,
            github_branch: Optional[str] = None,
            github_token: Optional[str] = None,
            per_page: int = DEFAULT_PER_PAGE,
            **kwargs,
    ):
        super().__init__(**kwargs)

        self.GITHUB_OWNER = github_owner
        self.GITHUB_REPO = github_repo
        self.GITHUB_TOKEN = github_token

        self.logger.info(
            f"Connecting to GitHub organization {self.GITHUB_OWNER}"
        )

        auth = Auth.Token(self.GITHUB_TOKEN)
        self.git = Github(auth=auth, per_page=per_page)
        self.org = self.git.get_organization(self.GITHUB_OWNER)

        self.repo = None
        if github_repo:
            try:
                self.repo = self.git.get_repo(f"{self.GITHUB_OWNER}/{self.GITHUB_REPO}")
                self.logger.info(f"Connecting to Git repository {self.GITHUB_OWNER}/{self.GITHUB_REPO}")
            except UnknownObjectException:
                self.logger.warning(f"Repository {self.GITHUB_OWNER}/{self.GITHUB_REPO} does not exist")

        if github_branch is None and self.repo:
            self.GITHUB_BRANCH = self.repo.default_branch
        else:
            self.GITHUB_BRANCH = github_branch

        self.graphql_client = GraphqlClient(endpoint="https://api.github.com/graphql")

    def get_repository_branch(self, branch_name: str):
        if self.repo is None:
            self.logger.warning(f"Repository not set for {self.GITHUB_OWNER}, cannot get branch {branch_name}")
            return None

        try:
            return self.repo.get_branch(branch_name)
        except UnknownObjectException:
            self.logger.warning(f"{branch_name} does not yet exist")
            return None

    def create_repository_branch(
            self, branch_name: str, parent_branch: Optional[str] = None
    ):
        if self.repo is None:
            self.logger.warning(f"Repository not set for {self.GITHUB_OWNER}, cannot create branch {branch_name}")
            return None

        parent_branch_ref = self.get_repository_branch(
            parent_branch or self.repo.default_branch
        )
        if utils.is_nothing(parent_branch_ref):
            raise RuntimeError(
                f"Cannot create Git branch {branch_name}, parent branch {parent_branch} does not yet exist"
            )

        try:
            return self.repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=parent_branch_ref.commit.sha,
            )
        except GithubException as exc:
            if get_github_api_error(exc) == "Reference already exists":
                self.logger.info(
                    f"Branch {branch_name} already exists in Git repository"
                )
                return self.get_repository_branch(branch_name)

            raise RuntimeError(f"Failed to create branch {branch_name}") from exc

    def get_repository_file(
            self,
            file_path: FilePath,
            decode: Optional[bool] = True,
            return_sha: Optional[bool] = False,
            return_path: Optional[bool] = False,
            charset: Optional[str] = "utf-8",
            errors: Optional[str] = "strict",
            raise_on_not_found: bool = False,
    ):
        if self.repo is None:
            self.logger.warning(f"Repository not set for {self.GITHUB_OWNER}, cannot get file {file_path}")
            return None

        def state_negative_result(result: str):
            self.logger.warning(result)

            if raise_on_not_found:
                raise FileNotFoundError(result)

        def get_retval(d: Optional[str], s: Optional[str], p: FilePath):
            retval = [d]
            if return_sha:
                retval.append(s)

            if return_path:
                retval.append(p)

            if len(retval) == 1:
                return retval[0]

            return tuple(retval)

        file_data = {} if decode else ""
        file_sha = None

        self.logged_statement(f"Getting repository file: {file_path}")

        try:
            raw_file_data = self.repo.get_contents(
                str(file_path), ref=self.GITHUB_BRANCH
            )
            file_sha = raw_file_data.sha
            if utils.is_nothing(raw_file_data.content):
                self.logger.warning(
                    f"{file_path} is empty of content: {self.GITHUB_BRANCH}"
                )
            else:
                file_data = raw_file_data.decoded_content.decode(charset, errors)
        except (UnknownObjectException, AttributeError):
            state_negative_result(f"{file_path} does not exist")
        except ValueError as exc:
            self.logger.warning(f"Reading {file_path} not supported: {exc}")
            decode = False

        if not decode or is_nothing(file_data):
            return get_retval(file_data, file_sha, file_path)

        return self.decode_file(file_data=file_data, file_path=file_path)

    def update_repository_file(
            self,
            file_path: FilePath,
            file_data: Any,
            file_sha: Optional[str] = None,
            msg: Optional[str] = None,
            allow_encoding: Optional[Union[bool, str]] = None,
            allow_empty: bool = False,
            **format_opts: Any
    ):
        if self.repo is None:
            self.logger.warning(f"Repository not set for {self.GITHUB_OWNER}, cannot update file {file_path}")
            return None

        if is_nothing(file_data) and not allow_empty:
            self.logger.warning(f"Empty file data for {file_path} not allowed")
            return None

        if msg:
            self.logger.info(msg)

        if allow_encoding is None:
            allow_encoding = get_encoding_for_file_path(file_path)
            self.logger.debug(f"Detected encoding for {file_path}: {allow_encoding}")

        file_data = wrap_raw_data_for_export(file_data,
                                             allow_encoding=allow_encoding,
                                             **format_opts)

        if not isinstance(file_data, str):
            file_data = str(file_data)

        self.logger.info(f"Updating repository file: {file_path}")

        if file_sha is None:
            _, file_sha = self.get_repository_file(file_path, return_sha=True)

        if file_sha is None:
            if msg is None:
                msg = f"Creating {file_path}"

            return self.repo.create_file(
                path=str(file_path),
                message=msg,
                branch=self.GITHUB_BRANCH,
                content=file_data,
            )
        else:
            if msg is None:
                msg = f"Updating {file_path}"

            return self.repo.update_file(
                path=str(file_path),
                message=msg,
                content=file_data,
                sha=file_sha,
                branch=self.GITHUB_BRANCH,
            )

    def delete_repository_file(
            self,
            file_path: FilePath,
            msg: Optional[str] = None,
    ):
        if self.repo is None:
            self.logger.warning(f"Repository not set for {self.GITHUB_OWNER}, cannot delete file {file_path}")
            return None

        self.logger.info(f"Deleting repository file: {file_path}")

        _, sha = self.get_repository_file(file_path=file_path, return_sha=True)
        if sha is None:
            return None

        if msg is None:
            msg = f"Deleting {file_path}"

        return self.repo.delete_file(
            path=str(file_path),
            message=msg,
            branch=self.GITHUB_BRANCH,
            sha=sha,
        )
