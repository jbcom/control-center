"""VendorConnectors - Public API with caching like TerraformDataSource."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Any, Optional

from directed_inputs_class import DirectedInputsClass
from extended_data_types import get_default_dict, get_unique_signature, make_hashable
from lifecyclelogging import Logging

from vendor_connectors.aws import AWSConnector
from vendor_connectors.github import GithubConnector
from vendor_connectors.google import GoogleConnector
from vendor_connectors.slack import SlackConnector
from vendor_connectors.vault import VaultConnector
from vendor_connectors.zoom import ZoomConnector

if TYPE_CHECKING:
    import boto3
    import hvac
    from boto3.resources.base import ServiceResource
    from botocore.config import Config


class VendorConnectors(DirectedInputsClass):
    """Public API for vendor connectors with client caching.

    This class provides cached access to all vendor connectors, similar to
    how TerraformDataSource works in the FlipsideCrypto terraform-modules.

    Usage:
        vc = VendorConnectors()
        slack = vc.get_slack_client(token="...", bot_token="...")
        github = vc.get_github_client(github_owner="org", github_token="...")
        aws_client = vc.get_aws_client("s3")
    """

    def __init__(
        self,
        logger: Optional[Logging] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.logging = logger or Logging(logger_name=get_unique_signature(self))
        self.logger = self.logging.logger

        # Client cache - nested dict for different client types and their params
        self._client_cache: dict[str, dict[Any, Any]] = get_default_dict(levels=2)

    def _get_cache_key(self, **kwargs) -> frozenset:
        """Generate a hashable cache key from kwargs."""
        hashable_kwargs = {k: make_hashable(v) for k, v in kwargs.items()}
        return frozenset(hashable_kwargs.items())

    def _get_cached_client(self, client_type: str, **kwargs) -> Optional[Any]:
        """Retrieve a client from cache."""
        cache_key = self._get_cache_key(**kwargs)
        return self._client_cache[client_type].get(cache_key)

    def _set_cached_client(self, client_type: str, client: Any, **kwargs) -> None:
        """Store a client in cache."""
        cache_key = self._get_cache_key(**kwargs)
        self._client_cache[client_type][cache_key] = client

    # -------------------------------------------------------------------------
    # AWS
    # -------------------------------------------------------------------------

    def get_aws_connector(
        self,
        execution_role_arn: Optional[str] = None,
    ) -> AWSConnector:
        """Get a cached AWSConnector instance."""
        execution_role_arn = execution_role_arn or self.get_input("EXECUTION_ROLE_ARN", required=False)

        cached = self._get_cached_client("aws_connector", execution_role_arn=execution_role_arn)
        if cached:
            return cached

        connector = AWSConnector(
            execution_role_arn=execution_role_arn,
            logger=self.logging,
            inputs=self.inputs,
        )
        self._set_cached_client("aws_connector", connector, execution_role_arn=execution_role_arn)
        return connector

    def get_aws_client(
        self,
        client_name: str,
        execution_role_arn: Optional[str] = None,
        role_session_name: Optional[str] = None,
        config: Optional[Config] = None,
        **client_args,
    ) -> boto3.client:
        """Get a cached boto3 client."""
        execution_role_arn = execution_role_arn or self.get_input("EXECUTION_ROLE_ARN", required=False)
        role_session_name = role_session_name or self.get_input("ROLE_SESSION_NAME", required=False)

        cached = self._get_cached_client(
            "aws_client",
            client_name=client_name,
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
        )
        if cached:
            return cached

        connector = self.get_aws_connector(execution_role_arn)
        client = connector.get_aws_client(
            client_name=client_name,
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
            config=config,
            **client_args,
        )
        self._set_cached_client(
            "aws_client",
            client,
            client_name=client_name,
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
        )
        return client

    def get_aws_resource(
        self,
        service_name: str,
        execution_role_arn: Optional[str] = None,
        role_session_name: Optional[str] = None,
        config: Optional[Config] = None,
        **resource_args,
    ) -> ServiceResource:
        """Get a cached boto3 resource."""
        execution_role_arn = execution_role_arn or self.get_input("EXECUTION_ROLE_ARN", required=False)
        role_session_name = role_session_name or self.get_input("ROLE_SESSION_NAME", required=False)

        cached = self._get_cached_client(
            "aws_resource",
            service_name=service_name,
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
        )
        if cached:
            return cached

        connector = self.get_aws_connector(execution_role_arn)
        resource = connector.get_aws_resource(
            service_name=service_name,
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
            config=config,
            **resource_args,
        )
        self._set_cached_client(
            "aws_resource",
            resource,
            service_name=service_name,
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
        )
        return resource

    def get_aws_session(
        self,
        execution_role_arn: Optional[str] = None,
        role_session_name: Optional[str] = None,
    ) -> boto3.Session:
        """Get a cached boto3 session."""
        execution_role_arn = execution_role_arn or self.get_input("EXECUTION_ROLE_ARN", required=False)
        role_session_name = role_session_name or self.get_input("ROLE_SESSION_NAME", required=False)

        cached = self._get_cached_client(
            "aws_session",
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
        )
        if cached:
            return cached

        connector = self.get_aws_connector(execution_role_arn)
        session = connector.get_aws_session(
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
        )
        self._set_cached_client(
            "aws_session",
            session,
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
        )
        return session

    # -------------------------------------------------------------------------
    # GitHub
    # -------------------------------------------------------------------------

    def get_github_client(
        self,
        github_owner: Optional[str] = None,
        github_repo: Optional[str] = None,
        github_branch: Optional[str] = None,
        github_token: Optional[str] = None,
    ) -> GithubConnector:
        """Get a cached GithubConnector instance."""
        github_owner = github_owner or self.get_input("GITHUB_OWNER", required=True)
        github_repo = github_repo or self.get_input("GITHUB_REPO", required=False)
        github_branch = github_branch or self.get_input("GITHUB_BRANCH", required=False)
        github_token = github_token or self.get_input("GITHUB_TOKEN", required=True)

        cached = self._get_cached_client(
            "github",
            github_owner=github_owner,
            github_repo=github_repo,
            github_branch=github_branch,
            github_token=github_token,
        )
        if cached:
            return cached

        connector = GithubConnector(
            github_owner=github_owner,
            github_repo=github_repo,
            github_branch=github_branch,
            github_token=github_token,
            logger=self.logging,
            inputs=self.inputs,
        )
        self._set_cached_client(
            "github",
            connector,
            github_owner=github_owner,
            github_repo=github_repo,
            github_branch=github_branch,
            github_token=github_token,
        )
        return connector

    # -------------------------------------------------------------------------
    # Google
    # -------------------------------------------------------------------------

    def get_google_client(
        self,
        service_account_info: Optional[dict[str, Any] | str] = None,
        scopes: Optional[list[str]] = None,
        subject: Optional[str] = None,
    ) -> GoogleConnector:
        """Get a cached GoogleConnector instance."""
        service_account_info = service_account_info or self.get_input("GOOGLE_SERVICE_ACCOUNT", required=True)

        # For caching, use a hash to avoid exposing sensitive data
        cache_sa = hashlib.sha256(str(service_account_info).encode()).hexdigest()[:16] if service_account_info else None

        cached = self._get_cached_client(
            "google",
            service_account=cache_sa,
            subject=subject,
        )
        if cached:
            return cached

        connector = GoogleConnector(
            service_account_info=service_account_info,
            scopes=scopes,
            subject=subject,
            logger=self.logging,
            inputs=self.inputs,
        )
        self._set_cached_client(
            "google",
            connector,
            service_account=cache_sa,
            subject=subject,
        )
        return connector

    # -------------------------------------------------------------------------
    # Slack
    # -------------------------------------------------------------------------

    def get_slack_client(
        self,
        token: Optional[str] = None,
        bot_token: Optional[str] = None,
    ) -> SlackConnector:
        """Get a cached SlackConnector instance."""
        token = token or self.get_input("SLACK_TOKEN", required=True)
        bot_token = bot_token or self.get_input("SLACK_BOT_TOKEN", required=True)

        cached = self._get_cached_client("slack", token=token, bot_token=bot_token)
        if cached:
            return cached

        connector = SlackConnector(
            token=token,
            bot_token=bot_token,
            logger=self.logging,
            inputs=self.inputs,
        )
        self._set_cached_client("slack", connector, token=token, bot_token=bot_token)
        return connector

    # -------------------------------------------------------------------------
    # Vault
    # -------------------------------------------------------------------------

    def get_vault_client(
        self,
        vault_url: Optional[str] = None,
        vault_namespace: Optional[str] = None,
        vault_token: Optional[str] = None,
    ) -> hvac.Client:
        """Get a cached Vault hvac.Client instance."""
        vault_url = vault_url or self.get_input("VAULT_ADDR", required=False)
        vault_namespace = vault_namespace or self.get_input("VAULT_NAMESPACE", required=False)
        vault_token = vault_token or self.get_input("VAULT_TOKEN", required=False)

        cached = self._get_cached_client(
            "vault",
            vault_url=vault_url,
            vault_namespace=vault_namespace,
            vault_token=vault_token,
        )
        if cached:
            return cached

        connector = VaultConnector(
            vault_url=vault_url,
            vault_namespace=vault_namespace,
            vault_token=vault_token,
            logger=self.logging,
            inputs=self.inputs,
        )
        client = connector.vault_client
        self._set_cached_client(
            "vault",
            client,
            vault_url=vault_url,
            vault_namespace=vault_namespace,
            vault_token=vault_token,
        )
        return client

    def get_vault_connector(
        self,
        vault_url: Optional[str] = None,
        vault_namespace: Optional[str] = None,
        vault_token: Optional[str] = None,
    ) -> VaultConnector:
        """Get a cached VaultConnector instance."""
        vault_url = vault_url or self.get_input("VAULT_ADDR", required=False)
        vault_namespace = vault_namespace or self.get_input("VAULT_NAMESPACE", required=False)
        vault_token = vault_token or self.get_input("VAULT_TOKEN", required=False)

        cached = self._get_cached_client(
            "vault_connector",
            vault_url=vault_url,
            vault_namespace=vault_namespace,
            vault_token=vault_token,
        )
        if cached:
            return cached

        connector = VaultConnector(
            vault_url=vault_url,
            vault_namespace=vault_namespace,
            vault_token=vault_token,
            logger=self.logging,
            inputs=self.inputs,
        )
        self._set_cached_client(
            "vault_connector",
            connector,
            vault_url=vault_url,
            vault_namespace=vault_namespace,
            vault_token=vault_token,
        )
        return connector

    # -------------------------------------------------------------------------
    # Zoom
    # -------------------------------------------------------------------------

    def get_zoom_client(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        account_id: Optional[str] = None,
    ) -> ZoomConnector:
        """Get a cached ZoomConnector instance."""
        client_id = client_id or self.get_input("ZOOM_CLIENT_ID", required=True)
        client_secret = client_secret or self.get_input("ZOOM_CLIENT_SECRET", required=True)
        account_id = account_id or self.get_input("ZOOM_ACCOUNT_ID", required=True)

        cached = self._get_cached_client(
            "zoom",
            client_id=client_id,
            client_secret=client_secret,
            account_id=account_id,
        )
        if cached:
            return cached

        connector = ZoomConnector(
            client_id=client_id,
            client_secret=client_secret,
            account_id=account_id,
            logger=self.logging,
            inputs=self.inputs,
        )
        self._set_cached_client(
            "zoom",
            connector,
            client_id=client_id,
            client_secret=client_secret,
            account_id=account_id,
        )
        return connector
