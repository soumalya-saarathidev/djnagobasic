# auth_service/middleware/permission.py
from django.shortcuts import redirect
from auth_service.services.jwt_verifier import JWTVerifier

class PermissionMiddleware:
    """
    Middleware to attach Keycloak JWT claims to the request.
    Works with Bearer header or session token.
    Optionally redirects unauthorized requests to login.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extract token from Authorization header or session
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        token = None
        if auth_header.lower().startswith('bearer '):
            token = auth_header.split(' ', 1)[1].strip()
        elif request.session.get('access_token'):
            token = request.session.get('access_token')

        claims = None
        if token:
            try:
                claims = JWTVerifier.verify_access_token(token)
            except Exception:
                claims = None

        request.auth_claims = claims

        if not claims and not request.path.startswith('/auth/'):
            return redirect('/auth/login/keycloak/')

        return self.get_response(request)