# core/views/employees.py
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import authentication_classes, permission_classes
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from core.models import Employee
from core.forms import EmployeeForm
from auth_service.authentication import KeycloakJWTAuthentication
from auth_service.services.claims import parse_claims
from auth_service.services.jwt_verifier import JWTVerifier


@authentication_classes([KeycloakJWTAuthentication])
@permission_classes([IsAuthenticated])
class EmployeeListView(TemplateView):
    template_name = "core/employee_list.html"

    def get(self, request, *args, **kwargs):
        claims = JWTVerifier.claims_from_request(request)
        parsed = parse_claims(claims)

        if not (parsed.get("is_manager") or parsed.get("is_admin") or parsed.get("is_vp") or parsed.get("is_ceo")):
            return redirect("/unauthorized/")

        q = request.GET.get("q", "")
        employees = Employee.objects.active().select_related("department", "manager")
        if q:
            employees = employees.filter(
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                Q(employee_id__icontains=q)
            )

        context = {"employees": employees, "parsed": parsed}
        return self.render_to_response(context)


@authentication_classes([KeycloakJWTAuthentication])
@permission_classes([IsAuthenticated])
class EmployeeDetailView(TemplateView):
    template_name = "core/employee_detail.html"

    def get(self, request, *args, **kwargs):
        emp = get_object_or_404(Employee, pk=self.kwargs["pk"])
        claims = JWTVerifier.claims_from_request(request)
        parsed = parse_claims(claims)
        return self.render_to_response({"employee": emp, "parsed": parsed})


@authentication_classes([KeycloakJWTAuthentication])
@permission_classes([IsAuthenticated])
class EmployeeCreateView(TemplateView):
    template_name = "core/employee_form.html"

    def get(self, request, *args, **kwargs):
        return self.render_to_response({"form": EmployeeForm()})

    def post(self, request, *args, **kwargs):
        claims = JWTVerifier.claims_from_request(request)
        parsed = parse_claims(claims)

        if not (parsed.get("is_manager") or parsed.get("is_admin")):
            return redirect("/unauthorized/")

        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse_lazy("employees:list"))
        return self.render_to_response({"form": form})


@authentication_classes([KeycloakJWTAuthentication])
@permission_classes([IsAuthenticated])
class EmployeeUpdateView(TemplateView):
    template_name = "core/employee_form.html"

    def get(self, request, *args, **kwargs):
        emp = get_object_or_404(Employee, pk=self.kwargs["pk"])
        return self.render_to_response({"form": EmployeeForm(instance=emp)})

    def post(self, request, *args, **kwargs):
        claims = JWTVerifier.claims_from_request(request)
        parsed = parse_claims(claims)

        if not (parsed.get("is_manager") or parsed.get("is_admin")):
            return redirect("/unauthorized/")

        emp = get_object_or_404(Employee, pk=self.kwargs["pk"])
        form = EmployeeForm(request.POST, instance=emp)
        if form.is_valid():
            form.save()
            return redirect(reverse_lazy("employees:list"))
        return self.render_to_response({"form": form})


@authentication_classes([KeycloakJWTAuthentication])
@permission_classes([IsAuthenticated])
class EmployeeDeleteView(APIView):
    def post(self, request, pk):
        claims = JWTVerifier.claims_from_request(request)
        parsed = parse_claims(claims)
        if not parsed.get("is_admin"):
            return Response({"error": "Unauthorized"}, status=403)
        emp = get_object_or_404(Employee, pk=pk)
        emp.is_active = False
        emp.save()
        return Response({"deleted": True}, status=200)