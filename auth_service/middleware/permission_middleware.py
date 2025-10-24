# auth_service/middleware/permission_middleware.py
from django.shortcuts import redirect
from urllib.parse import urlencode
from auth_service.services.jwt_verifier import JWTVerifier
import logging
from django.urls import reverse
from auth_service.authentication import KeycloakUser
logger = logging.getLogger("auth_service.middleware.permission_middleware")


class PermissionMiddleware:
    """Middleware to attach Keycloak JWT claims to the request.
    Works with Bearer header or ?token query param.
    Optionally redirects unauthorized requests to login."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_paths = [
            '/auth/login/',
            '/auth/callback/',
            '/auth/forgotpassword/',
            # '/auth/token/',
            # '/admin/',  # optional
            '/static/',  # optional
        ]

    def __call__(self, request):
        """Extract JWT token from request and verify it."""
        # Skip check for exempt paths if the request path starts with any of the exempt paths
        if any(request.path.startswith(p) for p in self.exempt_paths):
            return self.get_response(request)

        token = JWTVerifier.extract_token_from_request(request)
        if not token:
            logger.warning("⚠️ No JWT found; redirecting to login")
            login_url = reverse("auth_service:login")
            logger.info(f"Redirecting to login for {request.path}")
            params = urlencode({"next": request.path})
            return redirect(f"{login_url}?{params}")

        claims = JWTVerifier.verify_access_token(token)
        if not claims:
            login_url = reverse("auth_service:login")
            params = urlencode({"next": request.path})
            return redirect(f"{login_url}?{params}")

        # Attach KeycloakUser to request
        request.user = KeycloakUser(claims)
        # Ensure Authorization header is set for downstream use
        if "Authorization" not in request.headers and "HTTP_AUTHORIZATION" not in request.META:
            request.META["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        return self.get_response(request)