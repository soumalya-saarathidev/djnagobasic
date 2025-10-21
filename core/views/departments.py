# core/views/departments.py
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import authentication_classes, permission_classes
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from core.models import Department
from core.forms import DepartmentForm
from auth_service.authentication import KeycloakJWTAuthentication
from auth_service.services.jwt_verifier import JWTVerifier
from auth_service.services.claims import parse_claims


@authentication_classes([KeycloakJWTAuthentication])
@permission_classes([IsAuthenticated])
class DepartmentListView(TemplateView):
    template_name = "core/department_list.html"

    def get(self, request, *args, **kwargs):
        claims = JWTVerifier.claims_from_request(request)
        parsed = parse_claims(claims)

        # Authorization
        if not (parsed.get("is_admin") or parsed.get("is_ceo")):
            return redirect("/unauthorized/")

        q = request.GET.get("q", "")
        departments = Department.objects.filter(is_active=True)
        if q:
            departments = departments.filter(name__icontains=q)

        context = {
            "departments": departments,
            "parsed": parsed,
        }
        return self.render_to_response(context)


@authentication_classes([KeycloakJWTAuthentication])
@permission_classes([IsAuthenticated])
class DepartmentDetailView(TemplateView):
    template_name = "core/department_detail.html"

    def get(self, request, *args, **kwargs):
        claims = JWTVerifier.claims_from_request(request)
        parsed = parse_claims(claims)
        department = get_object_or_404(Department, pk=self.kwargs["pk"], is_active=True)
        context = {"department": department, "parsed": parsed}
        return self.render_to_response(context)


@authentication_classes([KeycloakJWTAuthentication])
@permission_classes([IsAuthenticated])
class DepartmentCreateView(TemplateView):
    template_name = "core/department_form.html"

    def get(self, request, *args, **kwargs):
        return self.render_to_response({"form": DepartmentForm()})

    def post(self, request, *args, **kwargs):
        claims = JWTVerifier.claims_from_request(request)
        parsed = parse_claims(claims)

        if not (parsed.get("is_admin") or parsed.get("is_ceo")):
            return redirect("/unauthorized/")

        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse_lazy("departments:list"))

        return self.render_to_response({"form": form})


@authentication_classes([KeycloakJWTAuthentication])
@permission_classes([IsAuthenticated])
class DepartmentUpdateView(TemplateView):
    template_name = "core/department_form.html"

    def get(self, request, *args, **kwargs):
        dept = get_object_or_404(Department, pk=self.kwargs["pk"])
        return self.render_to_response({"form": DepartmentForm(instance=dept)})

    def post(self, request, *args, **kwargs):
        claims = JWTVerifier.claims_from_request(request)
        parsed = parse_claims(claims)

        if not (parsed.get("is_admin") or parsed.get("is_ceo")):
            return redirect("/unauthorized/")

        dept = get_object_or_404(Department, pk=self.kwargs["pk"])
        form = DepartmentForm(request.POST, instance=dept)
        if form.is_valid():
            form.save()
            return redirect(reverse_lazy("departments:list"))
        return self.render_to_response({"form": form})


@authentication_classes([KeycloakJWTAuthentication])
@permission_classes([IsAuthenticated])
class DepartmentDeleteView(APIView):
    def post(self, request, pk):
        claims = JWTVerifier.claims_from_request(request)
        parsed = parse_claims(claims)

        if not parsed.get("is_admin"):
            return Response({"error": "Unauthorized"}, status=403)

        dept = get_object_or_404(Department, pk=pk)
        dept.is_active = False
        dept.save()
        return Response({"deleted": True}, status=200)