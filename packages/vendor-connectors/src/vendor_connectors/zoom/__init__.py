"""Zoom Connector using jbcom ecosystem packages."""

from __future__ import annotations

import base64
from typing import Any, Optional

import requests
from directed_inputs_class import DirectedInputsClass
from lifecyclelogging import Logging

# Default timeout for HTTP requests in seconds
DEFAULT_REQUEST_TIMEOUT = 30


class ZoomConnector(DirectedInputsClass):
    """Zoom connector for user management."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        account_id: Optional[str] = None,
        logger: Optional[Logging] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.logging = logger or Logging(logger_name="ZoomConnector")
        self.logger = self.logging.logger
        self.errors: list[str] = []  # Track errors for programmatic access

        self.client_id = client_id or self.get_input("ZOOM_CLIENT_ID", required=True)
        self.client_secret = client_secret or self.get_input("ZOOM_CLIENT_SECRET", required=True)
        self.account_id = account_id or self.get_input("ZOOM_ACCOUNT_ID", required=True)

    def get_access_token(self) -> Optional[str]:
        """Get an OAuth access token from Zoom."""
        url = "https://zoom.us/oauth/token"
        auth_string = f"{self.client_id}:{self.client_secret}"
        headers = {
            "Authorization": f"Basic {base64.b64encode(auth_string.encode()).decode()}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {"grant_type": "account_credentials", "account_id": self.account_id}

        try:
            response = requests.post(url, headers=headers, data=data, timeout=DEFAULT_REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json().get("access_token")
        except requests.exceptions.RequestException as exc:
            raise RuntimeError("Failed to get Zoom access token") from exc

    def get_headers(self) -> dict[str, str]:
        """Get headers with authorization for Zoom API calls."""
        token = self.get_access_token()
        if not token:
            raise RuntimeError("Failed to get access token")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def get_zoom_users(self) -> dict[str, dict[str, Any]]:
        """Get all Zoom users."""
        url = "https://api.zoom.us/v2/users"
        headers = self.get_headers()
        users: dict[str, dict[str, Any]] = {}
        page_size = 300
        next_page_token = None

        while True:
            params: dict[str, Any] = {"page_size": page_size}
            if next_page_token:
                params["next_page_token"] = next_page_token

            try:
                response = requests.get(url, headers=headers, params=params, timeout=DEFAULT_REQUEST_TIMEOUT)
                response.raise_for_status()
                data = response.json()
                for user in data.get("users", []):
                    users[user["email"]] = user

                next_page_token = data.get("next_page_token")
                if not next_page_token:
                    break
            except requests.exceptions.RequestException as exc:
                raise RuntimeError(f"Failed to get Zoom users: {exc}") from exc

        return users

    def remove_zoom_user(self, email: str) -> None:
        """Remove a Zoom user."""
        url = f"https://api.zoom.us/v2/users/{email}"
        headers = self.get_headers()
        try:
            response = requests.delete(url, headers=headers, timeout=DEFAULT_REQUEST_TIMEOUT)
            response.raise_for_status()
            self.logger.warning(f"Removed Zoom user {email}")
        except requests.exceptions.RequestException as exc:
            error_msg = f"Failed to remove Zoom user {email}: {exc}"
            self.errors.append(error_msg)
            self.logger.error(error_msg)

    def create_zoom_user(self, email: str, first_name: str, last_name: str) -> bool:
        """Create a Zoom user with a paid license."""
        url = "https://api.zoom.us/v2/users"
        headers = self.get_headers()
        user_info = {
            "action": "create",
            "user_info": {"email": email, "type": 2, "first_name": first_name, "last_name": last_name},
        }
        try:
            response = requests.post(url, headers=headers, json=user_info, timeout=DEFAULT_REQUEST_TIMEOUT)
            response.raise_for_status()
            self.logger.info(f"Created Zoom user {email}")
            return True
        except requests.exceptions.RequestException as exc:
            error_msg = f"Failed to create Zoom user {email}: {exc}"
            self.errors.append(error_msg)
            self.logger.error(error_msg)
            return False
