# auth_service/middleware/permission.py
from django.shortcuts import redirect
from auth_service.services.jwt_verifier import JWTVerifier
import logging

logger = logging.getLogger(__name__)


class PermissionMiddleware:
    """
    Middleware to attach Keycloak JWT claims to the request.
    Works with Bearer header or session token.
    Optionally redirects unauthorized requests to login.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        token = None

        if auth_header.lower().startswith('bearer '):
            token = auth_header.split(' ', 1)[1].strip()
        elif "token" in request.GET and request.GET.get("token"):
            token = request.GET.get("token").strip()
        elif request.session.get("access_token"):
            token = request.session.get("access_token")

        if token:
            try:
                claims = JWTVerifier.verify_access_token(token)
                logger.debug(f"✅ Valid JWT for {claims.get('email')}")
                request.auth_claims = claims
            except Exception as e:
                logger.warning(f"❌ Invalid JWT: {str(e)}")
                request.auth_claims = None
        else:
            request.auth_claims = None

        if not request.auth_claims and not request.path.startswith('/auth/'):
            logger.warning("⚠️ No JWT found; redirecting to login")
            return redirect('/auth/login/keycloak')

        return self.get_response(request)