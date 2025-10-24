# auth_service/authentication.py
import logging
import requests
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from auth_service.services.jwt_verifier import JWTVerifier

logger = logging.getLogger("auth_service.authentication")


class KeycloakUser:
    """
    Lightweight user object derived from Keycloak JWT claims.
    Stores both raw claims and parsed attributes (roles, department, etc.).
    """

    def __init__(self, claims: dict):
        self.claims = claims or {}

        # Basic identity
        self.id = claims.get("sub")
        self.username = claims.get("preferred_username")
        self.email = claims.get("email")
        self.first_name = claims.get("given_name")
        self.last_name = claims.get("family_name")

        # Realm and client roles
        self.realm_roles = claims.get("realm_access", {}).get("roles", [])
        self.client_roles = claims.get("resource_access", {}).get(
            settings.KEYCLOAK_CLIENT_ID, {}
        ).get("roles", [])
        self.roles = list(set(self.realm_roles + self.client_roles))

        # -----------------------
        # 2️⃣ Extract user attributes
        # -----------------------
        self.department = claims.get("department")
        self.phone_number = claims.get("phone_number")
        self.position = claims.get("position")
        self.role_level = (claims.get("role_level") or "").lower()
        self.country = claims.get("country")
        self.manager_id = claims.get("manager_id")
        self.manager_email = claims.get("manager_email")

        # Handle boolean attributes safely
        raw_is_manager = str(claims.get("is_manager", "")).lower()
        self.is_manager = raw_is_manager in ["true", "1", "yes"]

        # -----------------------
        # 3️⃣ Derive role flags
        # -----------------------
        self.is_admin = "admin" in self.role_level or any("admin" in r for r in self.roles)
        self.is_manager = self.is_manager or self.role_level in ["manager", "vp", "ceo"]   # manager includes CEO, VP, Manager
        self.is_employee = not (self.is_admin or self.is_manager)

    def has_role(self, role: str) -> bool:
        """Check if user has a given role."""
        return role in self.roles

    def is_authenticated(self) -> bool:
        return True

    def __str__(self):
        return self.username or self.email or str(self.id)


class KeycloakJWTAuthentication(JWTAuthentication):
    """
    Stateless JWT authentication for Keycloak.
      ✅ Verifies Keycloak-issued tokens
      ✅ Auto-refreshes expired access tokens
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

        logger.debug("🔄 Attempting to refresh expired access token...")
        verify = settings.KEYCLOAK_CA_CERT_PATH if settings.KEYCLOAK_SSL_VERIFY else False
        resp = requests.post(token_endpoint, data=data, timeout=10, verify=verify)
        if resp.status_code != 200:
            logger.warning(f"❌ Token refresh failed: {resp.status_code} - {resp.text}")
            raise AuthenticationFailed("Token refresh failed")
        return resp.json()

    def authenticate(self, request):
        """Authenticate purely via Authorization header."""
        token = JWTVerifier.extract_token_from_request(request)
        if not token:
            logger.warning(f"🚫 No JWT token found in request to {request.path}")
            return None

        # Verify JWT via Keycloak public certs
        claims = JWTVerifier.verify_access_token(token)
        if not claims:
            logger.warning(f"❌ Invalid or expired token in request to {request.path}")
            raise AuthenticationFailed("Invalid or expired token")

        logger.debug({"claims": claims})
        user = KeycloakUser(claims)
        logger.info(f"✅ Authenticated user: {user.username} | roles: {user.roles}")
        return (user, token)