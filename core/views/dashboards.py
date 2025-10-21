# core/views/dashboards.py
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import redirect
from django.db.models import Count
from core.models import Employee, Department
from auth_service.authentication import KeycloakJWTAuthentication
from auth_service.services.jwt_verifier import JWTVerifier
from auth_service.services.claims import parse_claims


@authentication_classes([KeycloakJWTAuthentication])
@permission_classes([IsAuthenticated])
class DashboardTemplateView(TemplateView):
    """
    Renders the dashboard page for admins/managers.
    Redirects employees to attendance page.
    Authentication handled by KeycloakJWTAuthentication.
    """
    template_name = "core/dashboard.html"

    def get(self, request, *args, **kwargs):
        # ✅ Token already verified by KeycloakJWTAuthentication
        claims = JWTVerifier.claims_from_request(request)
        parsed = parse_claims(claims)

        # Role-based redirect logic
        if parsed.get("is_employee") and not parsed.get("is_admin") and not parsed.get("is_manager"):
            return redirect("/attendance/mark/")

        # Build dashboard context
        context = {
            "parsed": parsed,
            "total_employees": Employee.objects.active().count(),
            "total_departments": Department.objects.filter(is_active=True).count(),
            "manager_stats": (
                Employee.objects.active()
                .annotate(subordinate_count=Count("subordinates"))
                .filter(subordinate_count__gt=0)[:5]
            ),
        }
        return self.render_to_response(context)


@authentication_classes([KeycloakJWTAuthentication])
@permission_classes([IsAuthenticated])
class DashboardAPIView(APIView):
    """
    Returns dashboard data for authenticated users.
    Automatically redirects or refreshes if token invalid.
    """
    def get(self, request):
        # ✅ Claims are guaranteed by authentication middleware
        claims = JWTVerifier.claims_from_request(request)
        parsed = parse_claims(claims)

        # Redirect employees directly to attendance logic (in API form)
        if parsed.get("is_employee") and not parsed.get("is_admin") and not parsed.get("is_manager"):
            return Response(
                {"redirect": "/attendance/mark/"},
                status=307  # Temporary redirect semantics for API clients
            )

        # Core dashboard data
        data = {
            "user": {
                "name": parsed.get("name"),
                "email": parsed.get("email"),
                "roles": list(parsed.get("roles", [])),
            },
            "stats": {
                "employees": Employee.objects.active().count(),
                "departments": Department.objects.filter(is_active=True).count(),
            },
        }

        # Optional: manager/admin insights
        if parsed.get("is_admin") or parsed.get("is_manager"):
            manager_stats = (
                Employee.objects.active()
                .annotate(subordinate_count=Count("subordinates"))
                .filter(subordinate_count__gt=0)
                .values("name", "email", "subordinate_count")[:5]
            )
            data["manager_stats"] = list(manager_stats)

        return Response(data, status=200)