# auth_service/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions
from .services.jwt_verifier import JWTVerifier


class KeycloakUser:
    """Simple wrapper around decoded JWT claims to behave like a Django User."""
    def __init__(self, claims: dict):
        self.claims = claims

    @property
    def is_authenticated(self):
        return True

    def __getattr__(self, attr):
        # fallback to claim fields (so user.email, user.name work)
        return self.claims.get(attr)

    def __getitem__(self, key):
        return self.claims.get(key)

    def get_claims(self):
        return self.claims


class KeycloakJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication backend that validates tokens issued by Keycloak.
    """

    def authenticate(self, request):
        # Try header first
        auth_header = request.headers.get("Authorization")
        token = None

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        else:
            # Fallback: support token in query param (for Keycloak redirect flows)
            token = request.GET.get("token")

        if not token:
            return None

        try:
            claims = JWTVerifier.verify_access_token(token)
            user = KeycloakUser(claims)   # ✅ wrap claims into user object
            return (user, token)          # ✅ return KeycloakUser, not dict
        except Exception:
            return None