# auth_service/services/jwt_verifier.py
import time
from typing import Dict, Any, Optional
import requests
from jose import jwk, jwt
from jose.utils import base64url_decode
from django.conf import settings
from django.http import HttpRequest


class JWKSCache:
    """Simple in-memory cache for Keycloak JWKS public keys."""
    _cache: Optional[Dict[str, Any]] = None
    _timestamp: float = 0
    _ttl: int = 3600  # 1 hour

    @classmethod
    def get(cls) -> Dict[str, Any]:
        now = time.time()
        if cls._cache and now - cls._timestamp < cls._ttl:
            return cls._cache
        resp = requests.get(settings.KEYCLOAK_JWKS_URI, timeout=10)
        resp.raise_for_status()
        cls._cache = resp.json()
        cls._timestamp = now
        return cls._cache


class JWTVerifier:
    """Keycloak JWT verification and extraction utilities."""

    @staticmethod
    def extract_token_from_request(request: HttpRequest) -> Optional[str]:
        """
        Extracts Bearer token from Authorization header or ?token query param.
        """
        auth_header = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header.split(" ", 1)[1].strip()

        # fallback for ?token=
        token = request.GET.get("token")
        if token:
            return token.strip()

        return None

    @staticmethod
    def verify_access_token(token: str) -> Dict[str, Any]:
        """
        Verifies and decodes a Keycloak JWT using realm JWKS.
        """
        if not token:
            raise ValueError("Missing token")

        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        jwks = JWKSCache.get()
        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if not key:
            raise ValueError("Signing key not found")

        message, encoded_sig = token.rsplit(".", 1)
        decoded_sig = base64url_decode(encoded_sig.encode("utf-8"))
        public_key = jwk.construct(key)

        if not public_key.verify(message.encode("utf-8"), decoded_sig):
            raise ValueError("Invalid signature")

        claims = jwt.get_unverified_claims(token)

        # Basic expiry + issuer check
        if time.time() > claims.get("exp", 0):
            raise ValueError("Token expired")
        issuer = claims.get("iss")
        if settings.KEYCLOAK_ISSUER and issuer != settings.KEYCLOAK_ISSUER:
            raise ValueError(f"Invalid issuer: {issuer}")

        return claims

    @classmethod
    def claims_from_request(cls, request: HttpRequest) -> Optional[Dict[str, Any]]:
        """
        Extracts token from request and returns decoded claims, or None if invalid.
        """
        try:
            token = cls.extract_token_from_request(request)
            if not token:
                return None
            claims = cls.verify_access_token(token)
            return claims
        except Exception as e:
            # You could log this error for debugging
            print(f"[JWTVerifier] Token verification failed: {str(e)}")
            return None