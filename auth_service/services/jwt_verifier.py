import json
import time
from typing import Any, Dict, Optional
import requests
from django.conf import settings
from jose import jwk, jwt
from jose.utils import base64url_decode


class JWKSCache:
    _cache: Dict[str, Any] = {}
    _fetched_at: float = 0
    _ttl: int = 3600

    @classmethod
    def get(cls) -> Dict[str, Any]:
        now = time.time()
        if cls._cache and now - cls._fetched_at < cls._ttl:
            return cls._cache
        resp = requests.get(settings.KEYCLOAK_JWKS_URI, timeout=10)
        resp.raise_for_status()
        cls._cache = resp.json()
        cls._fetched_at = now
        return cls._cache


class JWTVerifier:
    @staticmethod
    def verify_access_token(token: str) -> Dict[str, Any]:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get('kid')
        jwks = JWKSCache.get()
        key = next((k for k in jwks.get('keys', []) if k.get('kid') == kid), None)
        if not key:
            raise ValueError('Signing key not found')
        message, encoded_sig = token.rsplit('.', 1)
        decoded_sig = base64url_decode(encoded_sig.encode('utf-8'))
        public_key = jwk.construct(key)
        if not public_key.verify(message.encode('utf-8'), decoded_sig):
            raise ValueError('Invalid token signature')

        claims = jwt.get_unverified_claims(token)
        issuer = claims.get('iss')
        if settings.KEYCLOAK_ISSUER and issuer != settings.KEYCLOAK_ISSUER:
            raise ValueError('Invalid issuer')
        if claims.get('exp') and time.time() > claims['exp']:
            raise ValueError('Token expired')
        return claims

    @staticmethod
    def claims_from_request(request) -> Optional[Dict[str, Any]]:
        # Prefer Authorization header
        auth = request.META.get('HTTP_AUTHORIZATION', '')
        token = None
        if auth.lower().startswith('bearer '):
            token = auth.split(' ', 1)[1].strip()
        elif hasattr(request, 'session') and request.session.get('access_token'):
            token = request.session.get('access_token')
        if not token:
            return None
        try:
            return JWTVerifier.verify_access_token(token)
        except Exception:
            return None


