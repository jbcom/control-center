from datetime import datetime, timezone
from typing import Optional

import hvac
from hvac.exceptions import VaultError

from cloud_connectors.base.utils import Utils


class VaultConnector(Utils):
    """Simplified Vault client with token and AppRole authentication."""

    def __init__(
            self,
            vault_address: Optional[str] = None,
            vault_namespace: Optional[str] = None,
            vault_token: Optional[str] = None,
            **kwargs,
    ):
        super().__init__(**kwargs)
        self.vault_address = vault_address
        self.vault_namespace = vault_namespace
        self.vault_token = vault_token
        self._vault_client = None
        self._vault_token_expiration = None

        self.logger.info("Initializing Vault client")
        self.logged_statement(
            "Vault client configuration",
            labeled_json_data={
                "config": {
                    "has_address": bool(vault_address),
                    "has_namespace": bool(vault_namespace),
                    "has_token": bool(vault_token)
                }
            }
        )

    @property
    def vault_client(self) -> hvac.Client:
        """Lazy initialization of the Vault client."""
        self.logger.debug("Accessing vault client property")

        if self._vault_client and self._is_token_valid():
            self.logger.debug("Using existing valid vault client")
            return self._vault_client

        self.logger.info("Initializing new Vault client connection")

        # Get configuration from inputs
        vault_address = self.vault_address or self.get_input("VAULT_ADDR", required=True)
        vault_namespace = self.vault_namespace or self.get_input("VAULT_NAMESPACE", required=False)
        vault_token = self.vault_token or self.get_input("VAULT_TOKEN", required=False)

        self.logged_statement(
            "Configuring Vault client",
            labeled_json_data={
                "connection": {
                    "address": vault_address,
                    "has_namespace": bool(vault_namespace),
                    "has_token": bool(vault_token)
                }
            }
        )

        vault_opts = {
            "url": vault_address,
        }
        if vault_namespace:
            vault_opts["namespace"] = vault_namespace
        if vault_token:
            vault_opts["token"] = vault_token
            
        try:
            self._vault_client = hvac.Client(**vault_opts)

            # Check if token authentication worked
            if vault_token and self._vault_client.is_authenticated():
                self._set_token_expiration()
                self.logger.info("Client authenticated with existing token")
                return self._vault_client

        except VaultError as e:
            self.logger.error(f"Error initializing Vault client with token: {e}")

        # Fallback to AppRole authentication
        self.logger.info("Attempting App Role authentication flow")
        
        try:
            app_role_path = self.get_input("VAULT_APPROLE_PATH", required=False, default="approle")
            role_id = self.get_input("VAULT_ROLE_ID", required=False)
            secret_id = self.get_input("VAULT_SECRET_ID", required=False)

            self.logged_statement(
                "App Role credentials check",
                labeled_json_data={
                    "auth": {
                        "has_path": bool(app_role_path),
                        "has_role_id": bool(role_id),
                        "has_secret_id": bool(secret_id),
                        "path": app_role_path
                    }
                }
            )

            if role_id and secret_id:
                self.logger.info("Attempting App Role authentication")
                
                # Re-create client for app role auth (clear any previous token)
                vault_opts = {
                    "url": vault_address,
                }
                if vault_namespace:
                    vault_opts["namespace"] = vault_namespace

                self._vault_client = hvac.Client(**vault_opts)

                auth_response = self._vault_client.auth.approle.login(
                    role_id=role_id,
                    secret_id=secret_id,
                    mount_point=app_role_path,
                    use_token=True
                )

                if self._vault_client.is_authenticated():
                    self._set_token_expiration()
                    
                    self.logged_statement(
                        "App Role authentication successful",
                        labeled_json_data={
                            "auth": {
                                "mount_point": app_role_path,
                                "policies": auth_response.get("auth", {}).get("policies", []),
                                "lease_duration": auth_response.get("auth", {}).get("lease_duration")
                            }
                        }
                    )
                    return self._vault_client
                else:
                    self.logger.error("App Role authentication succeeded but client not authenticated")
            else:
                self.logger.warning("App Role credentials not available")

        except VaultError as e:
            self.logger.error(f"Error during App Role authentication: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during App Role authentication: {e}")
            raise

        # If we reached here, all authentication methods failed
        raise RuntimeError("Vault authentication failed: no valid token or AppRole credentials provided")

    def _set_token_expiration(self):
        """Set the token expiration time from the Vault client."""
        self.logger.debug("Setting token expiration")

        try:
            token_data = self._vault_client.lookup_token()
            expire_time = token_data.get("expire_time")

            self.logged_statement(
                "Token expiration lookup",
                labeled_json_data={
                    "token": {
                        "has_expire_time": bool(expire_time),
                        "available_fields": list(token_data.keys())
                    }
                }
            )

            if expire_time:
                self._vault_token_expiration = datetime.fromisoformat(expire_time[:-1]).replace(
                    tzinfo=timezone.utc
                )
                self.logger.debug(f"Token expiration set to: {self._vault_token_expiration.isoformat()}")
            else:
                self.logger.warning("No expiration time found in token data")

        except VaultError as e:
            self.logger.error(f"Failed to lookup Vault token expiration: {e}")
            # Don't reraise - token may still work without expiration info

    def _is_token_valid(self) -> bool:
        """Check if the current Vault token is still valid."""
        if not self._vault_token_expiration:
            self.logger.debug("No token expiration set")
            return False

        is_valid = datetime.now(timezone.utc) < self._vault_token_expiration

        self.logged_statement(
            "Token validity check",
            labeled_json_data={
                "validity": {
                    "is_valid": is_valid,
                    "expires_at": self._vault_token_expiration.isoformat(),
                    "current_time": datetime.now(timezone.utc).isoformat()
                }
            }
        )

        return is_valid

    @classmethod
    def get_vault_client(
            cls, vault_address: Optional[str] = None, vault_namespace: Optional[str] = None,
            vault_token: Optional[str] = None, **kwargs
    ) -> hvac.Client:
        """Get an instance of the Vault client."""
        instance = cls(vault_address, vault_namespace, vault_token, **kwargs)
        return instance.vault_client
