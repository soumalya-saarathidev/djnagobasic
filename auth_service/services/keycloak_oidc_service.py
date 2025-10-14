from urllib.parse import urlencode
import requests
from typing import Dict, Any
from .provider_base import AuthProvider


class KeycloakOIDCProvider(AuthProvider):
    def __init__(self, server_url: str, realm: str, client_id: str, client_secret: str, scope: str = 'openid profile email'):
        self.server_url = server_url.rstrip('/')
        self.realm = realm
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope

    @property
    def auth_endpoint(self) -> str:
        return f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/auth"

    @property
    def token_endpoint(self) -> str:
        return f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/token"

    @property
    def userinfo_endpoint(self) -> str:
        return f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/userinfo"

    def get_authorize_url(self, redirect_uri: str) -> str:
        qs = urlencode({
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': self.scope,
        })
        return f"{self.auth_endpoint}?{qs}"

    def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': redirect_uri,
        }
        resp = requests.post(self.token_endpoint, data=data, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        headers = {'Authorization': f'Bearer {access_token}'}
        resp = requests.get(self.userinfo_endpoint, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()