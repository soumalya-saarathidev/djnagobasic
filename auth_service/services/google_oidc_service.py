## auth_service/services/google_oidc_service.py
# auth_service/services/google_oidc_service.py
import requests
from urllib.parse import urlencode
from typing import Dict, Any
from django.conf import settings
from .provider_base import AuthProvider


class GoogleOIDCProvider(AuthProvider):
    AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
    USERINFO_ENDPOINT = "https://openidconnect.googleapis.com/v1/userinfo"

    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.scope = getattr(settings, "GOOGLE_SCOPE", "openid email profile")

    def get_authorize_url(self, redirect_uri: str) -> str:
        qs = urlencode({
            "client_id": self.client_id,
            "response_type": "code",
            "scope": self.scope,
            "redirect_uri": redirect_uri,
            "access_type": "offline",
            "prompt": "consent",
        })
        return f"{self.AUTH_ENDPOINT}?{qs}"

    def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        resp = requests.post(self.TOKEN_ENDPOINT, data=data, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(self.USERINFO_ENDPOINT, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()


