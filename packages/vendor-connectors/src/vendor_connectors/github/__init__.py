"""Github Connector using jbcom ecosystem packages."""

from __future__ import annotations

import os
from typing import Any, Optional, Union

from directed_inputs_class import DirectedInputsClass
from extended_data_types import (
    decode_json,
    decode_yaml,
    get_encoding_for_file_path,
    is_nothing,
    wrap_raw_data_for_export,
)
from github import Auth, Github
from github.GithubException import GithubException, UnknownObjectException
from lifecyclelogging import Logging
from python_graphql_client import GraphqlClient

FilePath = Union[str, bytes, os.PathLike[Any]]


def get_github_api_error(exc: GithubException) -> Optional[str]:
    """Extract error message from Github exception."""
    data = getattr(exc, "data", {})
    return data.get("message", None)


DEFAULT_PER_PAGE = 100


class GithubConnector(DirectedInputsClass):
    """Github connector for repository operations."""

    def __init__(
        self,
        github_owner: str,
        github_repo: Optional[str] = None,
        github_branch: Optional[str] = None,
        github_token: Optional[str] = None,
        per_page: int = DEFAULT_PER_PAGE,
        logger: Optional[Logging] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.logging = logger or Logging(logger_name="GithubConnector")
        self.logger = self.logging.logger

        self.GITHUB_OWNER = github_owner
        self.GITHUB_REPO = github_repo
        self.GITHUB_TOKEN = github_token

        self.logger.info(f"Connecting to GitHub organization {self.GITHUB_OWNER}")

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
        """Get a repository branch by name."""
        if self.repo is None:
            self.logger.warning(f"Repository not set for {self.GITHUB_OWNER}, cannot get branch {branch_name}")
            return None

        try:
            return self.repo.get_branch(branch_name)
        except UnknownObjectException:
            self.logger.warning(f"{branch_name} does not yet exist")
            return None

    def create_repository_branch(self, branch_name: str, parent_branch: Optional[str] = None):
        """Create a new repository branch."""
        if self.repo is None:
            self.logger.warning(f"Repository not set for {self.GITHUB_OWNER}, cannot create branch {branch_name}")
            return None

        parent_branch_ref = self.get_repository_branch(parent_branch or self.repo.default_branch)
        if is_nothing(parent_branch_ref):
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
                self.logger.info(f"Branch {branch_name} already exists in Git repository")
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
        """Get a file from the repository."""
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

        self.logger.debug(f"Getting repository file: {file_path}")

        try:
            raw_file_data = self.repo.get_contents(str(file_path), ref=self.GITHUB_BRANCH)
            file_sha = raw_file_data.sha
            if is_nothing(raw_file_data.content):
                self.logger.warning(f"{file_path} is empty of content: {self.GITHUB_BRANCH}")
            else:
                file_data = raw_file_data.decoded_content.decode(charset, errors)
        except (UnknownObjectException, AttributeError):
            state_negative_result(f"{file_path} does not exist")
        except ValueError as exc:
            self.logger.warning(f"Reading {file_path} not supported: {exc}")
            decode = False

        if not decode or is_nothing(file_data):
            return get_retval(file_data, file_sha, file_path)

        # Decode file content based on file type
        encoding = get_encoding_for_file_path(file_path)
        try:
            if encoding == "json":
                decoded_data = decode_json(file_data)
            elif encoding == "yaml":
                decoded_data = decode_yaml(file_data)
            else:
                # For raw or unknown types, return the string as-is
                decoded_data = file_data
        except Exception as exc:
            self.logger.warning(f"Failed to decode {file_path} as {encoding}: {exc}")
            decoded_data = file_data

        return get_retval(decoded_data, file_sha, file_path)

    def update_repository_file(
        self,
        file_path: FilePath,
        file_data: Any,
        file_sha: Optional[str] = None,
        msg: Optional[str] = None,
        allow_encoding: Optional[Union[bool, str]] = None,
        allow_empty: bool = False,
        **format_opts: Any,
    ):
        """Update a file in the repository."""
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

        file_data = wrap_raw_data_for_export(file_data, allow_encoding=allow_encoding, **format_opts)

        if not isinstance(file_data, str):
            file_data = str(file_data)

        self.logger.info(f"Updating repository file: {file_path}")

        if file_sha is None:
            result = self.get_repository_file(file_path, return_sha=True)
            if isinstance(result, tuple):
                _, file_sha = result

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

    def delete_repository_file(self, file_path: FilePath, msg: Optional[str] = None):
        """Delete a file from the repository."""
        if self.repo is None:
            self.logger.warning(f"Repository not set for {self.GITHUB_OWNER}, cannot delete file {file_path}")
            return None

        self.logger.info(f"Deleting repository file: {file_path}")

        result = self.get_repository_file(file_path=file_path, return_sha=True)
        sha = None
        if isinstance(result, tuple):
            _, sha = result

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

    # =========================================================================
    # Organization Members
    # =========================================================================

    def list_org_members(
        self,
        role: Optional[str] = None,
        include_pending: bool = False,
    ) -> dict[str, dict[str, Any]]:
        """List organization members.

        Args:
            role: Filter by role ('admin', 'member'). None returns all.
            include_pending: Include pending invitations. Defaults to False.

        Returns:
            Dictionary mapping usernames to member data.
        """
        self.logger.info(f"Listing members for organization: {self.GITHUB_OWNER}")

        members: dict[str, dict[str, Any]] = {}

        # Get active members
        filter_args = {}
        if role:
            filter_args["role"] = role

        for member in self.org.get_members(**filter_args):
            membership = self.org.get_user_membership(member)
            members[member.login] = {
                "id": member.id,
                "login": member.login,
                "name": member.name,
                "email": member.email,
                "role": membership.role,
                "state": membership.state,
                "avatar_url": member.avatar_url,
                "html_url": member.html_url,
            }

        # Include pending invitations
        if include_pending:
            for invite in self.org.invitations():
                login = invite.login or invite.email
                members[login] = {
                    "id": invite.id,
                    "login": invite.login,
                    "email": invite.email,
                    "role": invite.role,
                    "state": "pending",
                    "invited_at": str(invite.created_at) if invite.created_at else None,
                }

        self.logger.info(f"Retrieved {len(members)} organization members")
        return members

    def get_org_member(self, username: str) -> Optional[dict[str, Any]]:
        """Get a specific organization member.

        Args:
            username: GitHub username.

        Returns:
            Member data or None if not found.
        """
        try:
            member = self.git.get_user(username)
            membership = self.org.get_user_membership(member)
            return {
                "id": member.id,
                "login": member.login,
                "name": member.name,
                "email": member.email,
                "role": membership.role,
                "state": membership.state,
                "avatar_url": member.avatar_url,
                "html_url": member.html_url,
            }
        except UnknownObjectException:
            self.logger.warning(f"User not found: {username}")
            return None

    # =========================================================================
    # Repositories
    # =========================================================================

    def list_repositories(
        self,
        type_filter: str = "all",
        include_branches: bool = False,
    ) -> dict[str, dict[str, Any]]:
        """List organization repositories.

        Args:
            type_filter: Filter type ('all', 'public', 'private', 'forks', 'sources', 'member').
            include_branches: Include branch information. Defaults to False.

        Returns:
            Dictionary mapping repo names to repository data.
        """
        self.logger.info(f"Listing repositories for organization: {self.GITHUB_OWNER}")

        repos: dict[str, dict[str, Any]] = {}

        for repo in self.org.get_repos(type=type_filter):
            repo_data = {
                "id": repo.id,
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "private": repo.private,
                "archived": repo.archived,
                "default_branch": repo.default_branch,
                "html_url": repo.html_url,
                "clone_url": repo.clone_url,
                "ssh_url": repo.ssh_url,
                "language": repo.language,
                "topics": repo.topics,
                "created_at": str(repo.created_at) if repo.created_at else None,
                "updated_at": str(repo.updated_at) if repo.updated_at else None,
                "pushed_at": str(repo.pushed_at) if repo.pushed_at else None,
            }

            if include_branches:
                branches = []
                for branch in repo.get_branches():
                    branches.append(
                        {
                            "name": branch.name,
                            "protected": branch.protected,
                            "sha": branch.commit.sha,
                        }
                    )
                repo_data["branches"] = branches

            repos[repo.name] = repo_data

        self.logger.info(f"Retrieved {len(repos)} repositories")
        return repos

    def get_repository(self, repo_name: str) -> Optional[dict[str, Any]]:
        """Get a specific repository.

        Args:
            repo_name: Repository name.

        Returns:
            Repository data or None if not found.
        """
        try:
            repo = self.git.get_repo(f"{self.GITHUB_OWNER}/{repo_name}")
            return {
                "id": repo.id,
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "private": repo.private,
                "archived": repo.archived,
                "default_branch": repo.default_branch,
                "html_url": repo.html_url,
                "clone_url": repo.clone_url,
                "ssh_url": repo.ssh_url,
                "language": repo.language,
                "topics": repo.topics,
            }
        except UnknownObjectException:
            self.logger.warning(f"Repository not found: {repo_name}")
            return None

    # =========================================================================
    # Teams
    # =========================================================================

    def list_teams(
        self,
        include_members: bool = False,
        include_repos: bool = False,
    ) -> dict[str, dict[str, Any]]:
        """List organization teams.

        Args:
            include_members: Include team members. Defaults to False.
            include_repos: Include team repositories. Defaults to False.

        Returns:
            Dictionary mapping team slugs to team data.
        """
        self.logger.info(f"Listing teams for organization: {self.GITHUB_OWNER}")

        teams: dict[str, dict[str, Any]] = {}

        for team in self.org.get_teams():
            team_data = {
                "id": team.id,
                "name": team.name,
                "slug": team.slug,
                "description": team.description,
                "privacy": team.privacy,
                "permission": team.permission,
                "html_url": team.html_url,
                "members_count": team.members_count,
                "repos_count": team.repos_count,
            }

            if include_members:
                members = []
                for member in team.get_members():
                    members.append(
                        {
                            "login": member.login,
                            "id": member.id,
                            "name": member.name,
                        }
                    )
                team_data["members"] = members

            if include_repos:
                repos = []
                for repo in team.get_repos():
                    repos.append(
                        {
                            "name": repo.name,
                            "full_name": repo.full_name,
                            "permission": team.get_repo_permission(repo),
                        }
                    )
                team_data["repositories"] = repos

            teams[team.slug] = team_data

        self.logger.info(f"Retrieved {len(teams)} teams")
        return teams

    def get_team(self, team_slug: str) -> Optional[dict[str, Any]]:
        """Get a specific team.

        Args:
            team_slug: Team slug.

        Returns:
            Team data or None if not found.
        """
        try:
            team = self.org.get_team_by_slug(team_slug)
            return {
                "id": team.id,
                "name": team.name,
                "slug": team.slug,
                "description": team.description,
                "privacy": team.privacy,
                "permission": team.permission,
                "html_url": team.html_url,
                "members_count": team.members_count,
                "repos_count": team.repos_count,
            }
        except UnknownObjectException:
            self.logger.warning(f"Team not found: {team_slug}")
            return None

    def add_team_member(self, team_slug: str, username: str, role: str = "member") -> bool:
        """Add a member to a team.

        Args:
            team_slug: Team slug.
            username: GitHub username.
            role: Role ('member' or 'maintainer'). Defaults to 'member'.

        Returns:
            True if successful.
        """
        self.logger.info(f"Adding {username} to team {team_slug}")
        try:
            team = self.org.get_team_by_slug(team_slug)
            user = self.git.get_user(username)
            team.add_membership(user, role=role)
            self.logger.info(f"Added {username} to team {team_slug}")
            return True
        except (UnknownObjectException, GithubException) as e:
            self.logger.error(f"Failed to add {username} to team: {e}")
            return False

    def remove_team_member(self, team_slug: str, username: str) -> bool:
        """Remove a member from a team.

        Args:
            team_slug: Team slug.
            username: GitHub username.

        Returns:
            True if successful.
        """
        self.logger.info(f"Removing {username} from team {team_slug}")
        try:
            team = self.org.get_team_by_slug(team_slug)
            user = self.git.get_user(username)
            team.remove_membership(user)
            self.logger.info(f"Removed {username} from team {team_slug}")
            return True
        except (UnknownObjectException, GithubException) as e:
            self.logger.error(f"Failed to remove {username} from team: {e}")
            return False

    # =========================================================================
    # GraphQL Queries
    # =========================================================================

    def execute_graphql(self, query: str, variables: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Execute a GraphQL query against the GitHub API.

        Args:
            query: GraphQL query string.
            variables: Optional query variables.

        Returns:
            Query response data.
        """
        headers = {"Authorization": f"Bearer {self.GITHUB_TOKEN}"}
        return self.graphql_client.execute(
            query=query,
            variables=variables or {},
            headers=headers,
        )
