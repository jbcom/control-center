"""Vault Connector using jbcom ecosystem packages."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import hvac
from directed_inputs_class import DirectedInputsClass
from hvac.exceptions import VaultError
from lifecyclelogging import Logging

# Default Vault settings
VAULT_URL_ENV_VAR = "VAULT_ADDR"
VAULT_NAMESPACE_ENV_VAR = "VAULT_NAMESPACE"
VAULT_ROLE_ID_ENV_VAR = "VAULT_ROLE_ID"
VAULT_SECRET_ID_ENV_VAR = "VAULT_SECRET_ID"
VAULT_APPROLE_PATH_ENV_VAR = "VAULT_APPROLE_PATH"


class VaultConnector(DirectedInputsClass):
    """Vault connector with token and AppRole authentication."""

    def __init__(
        self,
        vault_url: Optional[str] = None,
        vault_namespace: Optional[str] = None,
        vault_token: Optional[str] = None,
        logger: Optional[Logging] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.logging = logger or Logging(logger_name="VaultConnector")
        self.logger = self.logging.logger

        self.vault_url = vault_url
        self.vault_namespace = vault_namespace
        self.vault_token = vault_token
        self._vault_client: Optional[hvac.Client] = None
        self._vault_token_expiration: Optional[datetime] = None

        self.logger.info("Initializing Vault connector")

    @property
    def vault_client(self) -> hvac.Client:
        """Lazy initialization of the Vault client."""
        if self._vault_client and self._is_token_valid():
            return self._vault_client

        self.logger.info("Initializing new Vault client connection")

        vault_url = self.vault_url or self.get_input(VAULT_URL_ENV_VAR, required=True)
        vault_namespace = self.vault_namespace or self.get_input(VAULT_NAMESPACE_ENV_VAR, required=False)
        vault_token = self.vault_token or self.get_input("VAULT_TOKEN", required=False)

        vault_opts: dict = {"url": vault_url}
        if vault_namespace:
            vault_opts["namespace"] = vault_namespace
        if vault_token:
            vault_opts["token"] = vault_token

        try:
            self._vault_client = hvac.Client(**vault_opts)

            if vault_token and self._vault_client.is_authenticated():
                self._set_token_expiration()
                self.logger.info("Authenticated with existing token")
                return self._vault_client

        except VaultError as e:
            self.logger.error(f"Error initializing Vault client with token: {e}")

        # Fallback to AppRole authentication
        self.logger.info("Attempting AppRole authentication")

        try:
            app_role_path = self.get_input(VAULT_APPROLE_PATH_ENV_VAR, required=False, default="approle")
            role_id = self.get_input(VAULT_ROLE_ID_ENV_VAR, required=False)
            secret_id = self.get_input(VAULT_SECRET_ID_ENV_VAR, required=False)

            if role_id and secret_id:
                vault_opts = {"url": vault_url}
                if vault_namespace:
                    vault_opts["namespace"] = vault_namespace

                self._vault_client = hvac.Client(**vault_opts)
                self._vault_client.auth.approle.login(
                    role_id=role_id,
                    secret_id=secret_id,
                    mount_point=app_role_path,
                    use_token=True,
                )

                if self._vault_client.is_authenticated():
                    self._set_token_expiration()
                    self.logger.info("AppRole authentication successful")
                    return self._vault_client

        except VaultError as e:
            self.logger.error(f"Error during AppRole authentication: {e}")
            raise

        raise RuntimeError("Vault authentication failed: no valid token or AppRole credentials provided")

    def _set_token_expiration(self):
        """Set the token expiration time."""
        if self._vault_client is None:
            return

        try:
            token_data = self._vault_client.auth.token.lookup_self()
            expire_time = token_data.get("data", {}).get("expire_time")

            if expire_time:
                expire_time_clean = expire_time.replace("Z", "+00:00")
                self._vault_token_expiration = datetime.fromisoformat(expire_time_clean)
                # fromisoformat with '+00:00' produces a timezone-aware datetime (Python 3.7+ only)
                # No need to manually set tzinfo if running on Python 3.7 or newer.
                # If supporting Python <3.7, manual tzinfo assignment is required.
        except VaultError as e:
            self.logger.error(f"Failed to lookup Vault token expiration: {e}")

    def _is_token_valid(self) -> bool:
        """Check if the current Vault token is still valid."""
        if not self._vault_token_expiration:
            return False
        return datetime.now(timezone.utc) < self._vault_token_expiration

    @classmethod
    def get_vault_client(
        cls,
        vault_url: Optional[str] = None,
        vault_namespace: Optional[str] = None,
        vault_token: Optional[str] = None,
        **kwargs,
    ) -> hvac.Client:
        """Get an instance of the Vault client."""
        instance = cls(vault_url, vault_namespace, vault_token, **kwargs)
        return instance.vault_client
