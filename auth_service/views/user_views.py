# auth_service/views/user_views.py
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.urls import reverse
from urllib.parse import urlencode
from django.shortcuts import redirect
from django.conf import settings

from auth_service.authentication import KeycloakJWTAuthentication
from auth_service.services.jwt_verifier import JWTVerifier
from auth_service.services.claims import parse_claims


def _redirect_to_login():
    """Redirect to Keycloak login if no token is present."""
    login_url = reverse("auth_service:login")
    params = urlencode({"provider": "keycloak"})
    return redirect(f"{login_url}?{params}")


@api_view(["GET"])
@authentication_classes([KeycloakJWTAuthentication])
def me(request):
    """
    Return Keycloak user info decoded from JWT,
    and include logout link to fully terminate SSO session.
    """
    claims = getattr(request, "user", None)
    token = request.GET.get("token")

    if not claims or not isinstance(claims, dict):
        if not token:
            return _redirect_to_login()
        try:
            claims = JWTVerifier.verify_access_token(token)
        except Exception:
            return Response({"error": "Invalid or expired token"}, status=401)

    parsed = parse_claims(claims)

    # Build logout URL (goes through Django logout handler)
    logout_url = request.build_absolute_uri(reverse("auth_service:logout"))

    return Response({
        "user": {
            "email": claims.get("email"),
            "name": claims.get("name"),
            "preferred_username": claims.get("preferred_username"),
            "department": parsed.get("department"),
            "roles": list(parsed.get("roles", [])),
        },
        "access": {
            "is_admin": parsed["is_admin"],
            "is_manager": parsed["is_manager"],
            "is_employee": parsed["is_employee"],
        },
        "logout_url": logout_url,
    })


@api_view(["GET"])
@authentication_classes([KeycloakJWTAuthentication])
@permission_classes([IsAuthenticated])
def permissions(request):
    """
    Returns permissions matrix derived from Keycloak roles or attributes.
    """
    claims = getattr(request, "user", None)
    if not claims:
        return Response({"error": "Invalid or missing token"}, status=401)

    parsed = parse_claims(claims)
    roles = parsed.get("roles", [])

    module_perms = {
        "attendance": "edit" if parsed["is_manager"] or parsed["is_admin"] else "view",
        "payroll": "view" if parsed["is_manager"] or parsed["is_admin"] else "none",
    }

    return Response({
        "roles": list(roles),
        "module_permissions": module_perms,
    })