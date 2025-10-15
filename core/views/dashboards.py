# core/views/dashboards.py
from django.shortcuts import render, redirect
from django.db.models import Count
from core.models import Employee, Department
from auth_service.services.jwt_verifier import JWTVerifier
from auth_service.services.claims import parse_claims


def dashboard(request):
    """
    Dashboard logic:
    - Admin/CEO → Full dashboard (Employees + Departments)
    - Manager/VP → Employees only
    - Employee → Redirect to leave management
    """
    claims = JWTVerifier.claims_from_request(request)
    if not claims:
        return redirect('/auth/login/keycloak/')

    parsed = parse_claims(claims)

    # Basic role routing
    if parsed["is_employee"] and not (parsed["is_admin"] or parsed["is_manager"]):
        return redirect('leavemanagementsystem:mark_attendance')

    total_employees = Employee.objects.active().count()
    total_departments = Department.objects.filter(is_active=True).count()

    manager_stats = Employee.objects.active().annotate(
        subordinate_count=Count('subordinates')
    ).filter(subordinate_count__gt=0)[:5]

    context = {
        "parsed": parsed,
        "total_employees": total_employees,
        "total_departments": total_departments,
        "manager_stats": manager_stats,
    }

    return render(request, "core/dashboard.html", context)