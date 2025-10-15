# auth_service/services/keycloak_oidc_service.py
import requests
from urllib.parse import urlencode
from typing import Dict, Any
from django.conf import settings

class KeycloakOIDCProvider:
    """
    Handles OIDC login + token exchange against Keycloak.
    """
    def __init__(self):
        self.server_url = settings.KEYCLOAK_SERVER_URL.rstrip('/')
        self.realm = settings.KEYCLOAK_REALM
        self.client_id = settings.KEYCLOAK_CLIENT_ID
        self.client_secret = settings.KEYCLOAK_CLIENT_SECRET
        self.scope = 'openid profile email'

    @property
    def auth_endpoint(self):
        return f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/auth"

    @property
    def token_endpoint(self):
        return f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/token"

    def get_authorize_url(self, redirect_uri: str) -> str:
        qs = urlencode({
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": self.scope,
        })
        return f"{self.auth_endpoint}?{qs}"

    def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": redirect_uri,
        }
        resp = requests.post(self.token_endpoint, data=data, timeout=10)
        resp.raise_for_status()
        return resp.json()