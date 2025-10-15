# core/views/team.py
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from core.models import Employee
from auth_service.services.claims import parse_claims
from auth_service.services.jwt_verifier import JWTVerifier
from auth_service.authentication import KeycloakJWTAuthentication


@authentication_classes([KeycloakJWTAuthentication])
@permission_classes([IsAuthenticated])
class MyTeamTemplateView(TemplateView):
    template_name = "core/my_team.html"

    def get_context_data(self, **kwargs):
        claims = JWTVerifier.claims_from_request(self.request)
        parsed = parse_claims(claims)
        employees = Employee.objects.filter(department__name=parsed["department"])
        return {"employees": employees, "department": parsed["department"]}


@authentication_classes([KeycloakJWTAuthentication])
@permission_classes([IsAuthenticated])
class MyTeamAPIView(APIView):
    def get(self, request):
        claims = JWTVerifier.claims_from_request(request)
        parsed = parse_claims(claims)
        employees = Employee.objects.filter(department__name=parsed["department"]).values(
            "id", "first_name", "last_name"
        )
        return Response(list(employees))