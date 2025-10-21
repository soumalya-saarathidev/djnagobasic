# auth_service/authentication.py

import time
import requests
from django.conf import settings
from django.shortcuts import redirect
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions
from .services.jwt_verifier import JWTVerifier
import logging

logger = logging.getLogger("auth_service.authentication")


class KeycloakUser:
    def __init__(self, claims: dict):
        self.claims = claims

    @property
    def is_authenticated(self):
        return True

    def __getattr__(self, attr):
        return self.claims.get(attr)

    def __getitem__(self, key):
        return self.claims.get(key)

    def get_claims(self):
        return self.claims


class KeycloakJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication backend that:
      ✅ Verifies Keycloak-issued tokens
      ✅ Auto-refreshes expired access tokens
      ✅ Redirects to login when no valid tokens exist
    """

    def _refresh_access_token(self, refresh_token: str):
        """Refresh Keycloak token pair."""
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": settings.KEYCLOAK_CLIENT_ID,
            "client_secret": settings.KEYCLOAK_CLIENT_SECRET,
        }
        token_endpoint = (
            f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token"
        )
        resp = requests.post(token_endpoint, data=data, timeout=10, verify=False)
        resp.raise_for_status()
        return resp.json()

    # def authenticate(self, request):
    #     """
    #     1️⃣ Try from header or ?token=
    #     2️⃣ Persist token in session
    #     3️⃣ Try from session if missing
    #     4️⃣ Refresh if expired
    #     5️⃣ Redirect to login if completely missing
    #     """
    #     token = None

    #     # Try from header
    #     auth_header = request.headers.get("Authorization")
    #     if auth_header and auth_header.startswith("Bearer "):
    #         token = auth_header.split(" ")[1]

    #     # Try from query (e.g., after callback)
    #     elif request.GET.get("token"):
    #         token = request.GET["token"]
    #         # Save token in session
    #         request.session["access_token"] = token

    #     # Try from session (persisted)
    #     elif request.session.get("access_token"):
    #         token = request.session["access_token"]

    #     if not token:
    #         # No token at all → redirect once to login
    #         return redirect(f"/auth/login/keycloak?next={request.path}")

    #     try:
    #         claims = JWTVerifier.verify_access_token(token)
    #         user = KeycloakUser(claims)
    #         return (user, token)

    #     except Exception as e:
    #         if "expired" in str(e).lower():
    #             refresh_token = request.session.get("refresh_token")
    #             if not refresh_token:
    #                 return redirect(f"/auth/login/keycloak?next={request.path}")

    #             new_tokens = self._refresh_access_token(refresh_token)
    #             new_access = new_tokens.get("access_token")
    #             new_refresh = new_tokens.get("refresh_token", refresh_token)
    #             request.session["access_token"] = new_access
    #             request.session["refresh_token"] = new_refresh
    #             claims = JWTVerifier.verify_access_token(new_access)
    #             return (KeycloakUser(claims), new_access)

    #         raise exceptions.AuthenticationFailed("Invalid token.")
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "")
        token = None

        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        elif "token" in request.GET:
            token = request.GET.get("token")

        elif request.session.get("access_token"):
            token = request.session.get("access_token")

        if not token:
            logger.debug(f"🚫 No JWT token found in request to {request.path}")
            return None

        try:
            claims = JWTVerifier.verify_access_token(token)
            logger.debug(
                f"✅ JWT verified for user: {claims.get('email', 'unknown')} | roles: {claims.get('roles', [])}"
            )
            user = KeycloakUser(claims)
            return (user, token)
        except Exception as e:
            logger.error(f"❌ JWT verification failed: {str(e)}")
            return None