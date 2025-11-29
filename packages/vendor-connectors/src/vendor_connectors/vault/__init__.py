"""Vault Connector using jbcom ecosystem packages."""

from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from typing import Optional

import hvac
from directed_inputs_class import DirectedInputsClass
from extended_data_types import is_nothing
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

    def list_secrets(
        self,
        root_path: str = "/",
        mount_point: str = "secret",
        max_depth: Optional[int] = None,
    ) -> dict[str, dict]:
        """List secrets recursively from Vault KV v2 engine.

        Args:
            root_path: Starting path for listing (default: "/").
            mount_point: KV engine mount point (default: "secret").
            max_depth: Maximum directory depth to traverse (None = unlimited).

        Returns:
            Dict mapping secret paths to their data.
        """
        display_root = root_path if root_path not in (None, "", "/") else "/"
        self.logger.info(f"Listing Vault secrets from {mount_point}{display_root}")

        secrets: dict[str, dict] = {}
        client = self.vault_client

        normalized_root = (root_path or "").strip("/")
        list_path = normalized_root.rstrip("/") if normalized_root else ""
        path_prefix = f"{list_path}/" if list_path else ""

        # Initial listing from root_path
        try:
            root_result = client.secrets.kv.v2.list_secrets(
                path=list_path,
                mount_point=mount_point,
            )
            initial_paths = [
                (f"{path_prefix}{key}" if path_prefix else key, 0)
                for key in root_result.get("data", {}).get("keys", [])
            ]
        except VaultError as e:
            self.logger.warning(f"Invalid root path {display_root}: {e}")
            return secrets

        stack: deque[tuple[str, int]] = deque(initial_paths)

        while stack:
            current_path, depth = stack.popleft()

            if not current_path.endswith("/"):
                # It's a secret, fetch it
                try:
                    secret_data = client.secrets.kv.v2.read_secret_version(
                        path=current_path,
                        mount_point=mount_point,
                    )["data"]["data"]
                    secrets[current_path] = secret_data
                    self.logger.debug(f"Retrieved secret: {current_path}")
                except VaultError as e:
                    self.logger.warning(f"Failed to read secret {current_path}: {e}")
            else:
                # It's a directory, list its contents if within max_depth
                if max_depth is None or depth < max_depth:
                    try:
                        listing = client.secrets.kv.v2.list_secrets(
                            path=current_path,
                            mount_point=mount_point,
                        )
                        keys = listing.get("data", {}).get("keys", [])
                        for key in keys:
                            new_path = f"{current_path}{key}"  # current_path already ends with /
                            stack.append((new_path, depth + 1))
                    except VaultError as e:
                        self.logger.warning(f"Failed to list path {current_path}: {e}")

        self.logger.info(f"Listed {len(secrets)} Vault secrets")
        return secrets

    def read_secret(
        self,
        path: str,
        mount_point: str = "secret",
    ) -> Optional[dict]:
        """Read a single secret from Vault.

        Args:
            path: Path to the secret.
            mount_point: KV engine mount point (default: "secret").

        Returns:
            Secret data dict, or None if not found.
        """
        try:
            result = self.vault_client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=mount_point,
            )
            return result.get("data", {}).get("data")
        except VaultError as e:
            self.logger.warning(f"Failed to read secret {path}: {e}")
            return None

    def get_secret(
        self,
        path: str = "/",
        secret_name: Optional[str] = None,
        matchers: Optional[dict[str, str]] = None,
        mount_point: str = "secret",
    ) -> Optional[dict]:
        """Get Vault secret by path, name, or by searching with matchers.

        This method supports three modes:
        1. Direct path + secret_name: Fetches secret at path/secret_name
        2. Path with matchers: Searches secrets under path and returns first match
        3. Path without matchers: Returns first non-empty secret found

        Args:
            path: Root path to search or base path for secret_name (default: "/").
            secret_name: Specific secret name to append to path.
            matchers: Dict of key/value pairs to match against secret data.
            mount_point: KV engine mount point (default: "secret").

        Returns:
            Secret data dict, or None if not found.
        """
        self.logger.debug(f"Getting Vault secret: path={path}, secret_name={secret_name}")

        client = self.vault_client
        secret_data = None

        # Handle specific secret_name case - direct fetch
        if not is_nothing(secret_name):
            # Build the full path: path/secret_name or just secret_name if path is "/"
            if path and path != "/":
                secret_path = f"{path}/{secret_name}"
            else:
                secret_path = secret_name
            self.logger.debug(f"Resolved secret path: {secret_path}")

            try:
                secret_data = client.secrets.kv.v2.read_secret_version(path=secret_path, mount_point=mount_point)[
                    "data"
                ]["data"]
                self.logger.debug(f"Retrieved secret data for {secret_path}")
            except VaultError as e:
                self.logger.warning(
                    f"Failed to find secret at {path}"
                    + (f"/{secret_name}" if not is_nothing(secret_name) else "")
                    + f": {e}"
                )
            return secret_data

        # No secret_name provided - search under path
        self.logger.info(f"Finding secrets under {path}")

        matching_secret_paths = self.list_secrets(root_path=path, mount_point=mount_point)
        self.logger.debug(f"Found {len(matching_secret_paths)} potential secrets")

        if is_nothing(matching_secret_paths):
            self.logger.warning(f"No secrets found matching {path}")
            return None

        # Convert to deque for efficient popleft iteration
        path_queue: deque[str] = deque(matching_secret_paths.keys())

        while path_queue and secret_data is None:
            secret_path = path_queue.popleft()
            self.logger.debug(f"Checking secret path: {secret_path}")

            try:
                matching_secret_data = client.secrets.kv.v2.read_secret_version(
                    path=secret_path, mount_point=mount_point
                )["data"]["data"]
                self.logger.debug(f"Secret data for {secret_path}: {list(matching_secret_data.keys())}")
            except VaultError:
                self.logger.warning(f"{secret_path} is empty or invalid, skipping it")
                continue

            # If no matchers, take the first non-empty secret
            if is_nothing(matchers):
                self.logger.warning("No matchers provided, taking the first non-empty secret found")
                secret_data = matching_secret_data
                continue

            # Check matchers against the secret data
            found_match = False
            for k, v in matchers.items():
                datum = matching_secret_data.get(k)
                if datum == v:
                    self.logger.info(f"Matching {secret_path} on matcher {k}: {datum} equals {v}")
                    found_match = True
                    break

            if found_match:
                secret_data = matching_secret_data

        return secret_data

    def write_secret(
        self,
        path: str,
        data: dict,
        mount_point: str = "secret",
    ) -> bool:
        """Write a secret to Vault.

        Args:
            path: Path to write the secret.
            data: Secret data dict.
            mount_point: KV engine mount point (default: "secret").

        Returns:
            True if successful, False otherwise.
        """
        try:
            self.vault_client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=data,
                mount_point=mount_point,
            )
            self.logger.info(f"Wrote secret to {path}")
            return True
        except VaultError as e:
            self.logger.error(f"Failed to write secret {path}: {e}")
            return False
