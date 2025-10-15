# core/views/team.py
from django.shortcuts import render
from core.models import Employee
from core.authz import require_roles
from auth_service.services.claims import parse_claims


@require_roles("manager", "vp", "admin", "ceo")
def my_team_view(request):
    claims = request.auth_claims
    info = parse_claims(claims)

    employees = Employee.objects.filter(department__name=info["department"])

    context = {
        "employees": employees,
        "department": info["department"],
    }
    return render(request, "core/my_team.html", context)