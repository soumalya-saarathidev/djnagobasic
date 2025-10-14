from django.http import JsonResponse
from core.authz import require_roles
from auth_service.services.jwt_verifier import JWTVerifier

class KeycloakAuthMiddleware:
    """
    Extracts and validates Keycloak JWT from Authorization header
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        claims = JWTVerifier.claims_from_request(request)
        if claims:
            request.user_claims = claims
        else:
            request.user_claims = None
        return self.get_response(request)