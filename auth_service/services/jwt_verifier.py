# auth_service/services/jwt_verifier.py
import time
from typing import Dict, Any
import requests
from django.conf import settings
from jose import jwk, jwt
from jose.utils import base64url_decode

class JWKSCache:
    _cache = {}
    _timestamp = 0
    _ttl = 3600

    @classmethod
    def get(cls):
        now = time.time()
        if cls._cache and now - cls._timestamp < cls._ttl:
            return cls._cache
        resp = requests.get(settings.KEYCLOAK_JWKS_URI, timeout=10)
        resp.raise_for_status()
        cls._cache = resp.json()
        cls._timestamp = now
        return cls._cache

class JWTVerifier:
    @staticmethod
    def verify_access_token(token: str) -> Dict[str, Any]:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get('kid')

        jwks = JWKSCache.get()
        key = next((k for k in jwks['keys'] if k['kid'] == kid), None)
        if not key:
            raise ValueError("Signing key not found")

        message, encoded_sig = token.rsplit('.', 1)
        decoded_sig = base64url_decode(encoded_sig.encode('utf-8'))
        public_key = jwk.construct(key)

        if not public_key.verify(message.encode('utf-8'), decoded_sig):
            raise ValueError("Invalid signature")

        claims = jwt.get_unverified_claims(token)
        if time.time() > claims.get('exp', 0):
            raise ValueError("Token expired")
        if settings.KEYCLOAK_ISSUER and claims.get('iss') != settings.KEYCLOAK_ISSUER:
            raise ValueError("Invalid issuer")

        return claims


