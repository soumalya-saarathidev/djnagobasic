# core/views/dashboards.py
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import redirect
from django.db.models import Count
from core.models import Employee, Department
from auth_service.services.jwt_verifier import JWTVerifier
from auth_service.services.claims import parse_claims
from auth_service.authentication import KeycloakJWTAuthentication


@authentication_classes([KeycloakJWTAuthentication])
@permission_classes([IsAuthenticated])
class DashboardTemplateView(TemplateView):
    template_name = "core/dashboard.html"

    def get(self, request, *args, **kwargs):
        claims = JWTVerifier.claims_from_request(request)
        if not claims:
            return redirect(f"/auth/login/keycloak/?next={request.path}")
        parsed = parse_claims(claims)

        if parsed["is_employee"] and not parsed["is_admin"] and not parsed["is_manager"]:
            return redirect("/attendance/mark/")

        context = {
            "parsed": parsed,
            "total_employees": Employee.objects.active().count(),
            "total_departments": Department.objects.filter(is_active=True).count(),
            "manager_stats": Employee.objects.active()
            .annotate(subordinate_count=Count("subordinates"))
            .filter(subordinate_count__gt=0)[:5],
        }
        return self.render_to_response(context)


@authentication_classes([KeycloakJWTAuthentication])
@permission_classes([IsAuthenticated])
class DashboardAPIView(APIView):
    def get(self, request):
        claims = JWTVerifier.claims_from_request(request)
        if not claims:
            return Response({"error": "Unauthenticated"}, status=401)
        parsed = parse_claims(claims)
        data = {
            "employees": Employee.objects.active().count(),
            "departments": Department.objects.filter(is_active=True).count(),
            "roles": list(parsed.get("roles", [])),
        }
        return Response(data)