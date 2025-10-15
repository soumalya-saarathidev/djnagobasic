# auth_service/views/user_views.py
from rest_framework.decorators import permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import redirect
from django.urls import reverse
from auth_service.authentication import KeycloakJWTAuthentication
from auth_service.services.jwt_verifier import JWTVerifier
from auth_service.services.claims import parse_claims

@authentication_classes([KeycloakJWTAuthentication])
@permission_classes([IsAuthenticated])
class MeView(APIView):
    """Return user profile + role-based info."""

    def get(self, request):
        token = request.GET.get("token") or getattr(request, "auth", None)
        if not token:
            return redirect(reverse("auth_service:login"))

        try:
            claims = JWTVerifier.verify_access_token(token)
        except Exception:
            return Response({"error": "Invalid or expired token"}, status=401)

        parsed = parse_claims(claims)
        logout_url = request.build_absolute_uri(reverse("auth_service:logout"))

        # Final redirect based on `next` param or role
        next_url = request.session.pop("next_url", "/")

        return Response({
            "user": {
                "email": claims.get("email"),
                "name": claims.get("name"),
                "department": parsed.get("department"),
                "roles": list(parsed.get("roles", [])),
            },
            "access": parsed,
            "logout_url": logout_url,
            "redirect": next_url
        })

@authentication_classes([KeycloakJWTAuthentication])
@permission_classes([IsAuthenticated])
class PermissionsView(APIView):
    """Return user permission matrix."""

    def get(self, request):
        claims = getattr(request, "user", None)
        if not claims:
            return Response({"error": "Missing token"}, status=401)

        parsed = parse_claims(claims)
        module_perms = {
            "employees": "manage" if parsed["is_manager"] or parsed["is_admin"] else "view",
            "departments": "manage" if parsed["is_admin"] else "none",
        }

        return Response({
            "roles": list(parsed.get("roles", [])),
            "permissions": module_perms,
        })