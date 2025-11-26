import base64
from typing import Optional, Dict, Any

import requests

from cloud_connectors.base.utils import Utils


class ZoomConnector(Utils):
    def __init__(self,
                 client_id: str,
                 client_secret: str,
                 account_id: str,
                 **kwargs):
        super().__init__(**kwargs)

        self.client_id = client_id or self.get_input("ZOOM_CLIENT_ID", required=True)
        self.client_secret = client_secret or self.get_input("ZOOM_CLIENT_SECRET", required=True)
        self.account_id = account_id or self.get_input("ZOOM_ACCOUNT_ID", required=True)

    def get_access_token(self) -> Optional[str]:
        url = "https://zoom.us/oauth/token"
        headers = {
            "Authorization": f"Basic {base64.b64encode(f'{self.client_id}:{self.client_secret}'.encode()).decode()}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "account_credentials",
            "account_id": self.account_id
        }

        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            token_info = response.json()
            return token_info.get("access_token")
        except requests.exceptions.RequestException as exc:
            raise RuntimeError("Failed to get Zoom access token") from exc

    def get_headers(self):
        token = self.get_access_token()
        if not token:
            raise RuntimeError("Failed to get access token")
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def get_zoom_users(self) -> Dict[str, Dict[str, Any]]:
        url = "https://api.zoom.us/v2/users"
        headers = self.get_headers()
        users = {}
        page_size = 300
        next_page_token = None

        while True:
            params = {
                "page_size": page_size,
                "next_page_token": next_page_token
            } if next_page_token else {"page_size": page_size}

            try:
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                for user in data.get("users", []):
                    users[user['email']] = user

                next_page_token = data.get("next_page_token")
                if not next_page_token:
                    break
            except requests.exceptions.RequestException as exc:
                raise RuntimeError(f"Failed to get Zoom users: {exc}") from exc

        return users

    def remove_zoom_user(self, email: str) -> None:
        url = f"https://api.zoom.us/v2/users/{email}"
        headers = self.get_headers()
        try:
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            self.logger.warning(f"Removed Zoom user {email}")
        except requests.exceptions.RequestException as exc:
            self.errors.append(f"Failed to remove Zoom user {email}: {exc}")

    def create_zoom_user(self, email: str, first_name: str, last_name: str) -> bool:
        url = "https://api.zoom.us/v2/users"
        headers = self.get_headers()
        user_info = {
            "action": "create",
            "user_info": {
                "email": email,
                "type": 2,  # 2 denotes Licensed user
                "first_name": first_name,
                "last_name": last_name
            }
        }
        try:
            response = requests.post(url, headers=headers, json=user_info)
            response.raise_for_status()
            self.logger.info(f"Created and assigned paid license to Zoom user {email}")
            return True
        except requests.exceptions.RequestException as exc:
            self.errors.append(f"Failed to create Zoom user {email}: {exc}")
            return False
