# auth_service/views/user_views.py
from rest_framework.decorators import permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.urls import reverse
from auth_service.authentication import KeycloakJWTAuthentication


@authentication_classes([KeycloakJWTAuthentication])
@permission_classes([IsAuthenticated])
class MeView(APIView):
    """Return user profile + role-based info."""

    def get(self, request):
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return Response({"error": "Missing or invalid user"}, status=401)

        logout_url = request.build_absolute_uri(reverse("auth_service:logout"))
        return Response({
            "user": {
                "email": user.email,
                "name": f"{user.first_name or ''} {user.last_name or ''}".strip(),
                "department": user.department,
                "roles": user.roles,
            },
            "access": {
                "is_admin": user.is_admin,
                "is_manager": user.is_manager,
                "is_employee": user.is_employee,
                "role_level": user.role_level,
                "country": user.country,
            },
            "logout_url": logout_url,
        })


@authentication_classes([KeycloakJWTAuthentication])
@permission_classes([IsAuthenticated])
class PermissionsView(APIView):
    """Return user permission matrix."""

    def get(self, request):
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return Response({"error": "Missing user"}, status=401)

        module_perms = {
            "employees": "manage" if user.is_manager or user.is_admin else "view",
            "departments": "manage" if user.is_admin else "none",
        }

        return Response({
            "roles": user.roles,
            "permissions": module_perms,
        })