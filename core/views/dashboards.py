from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import render, redirect
from core.models import Employee, Department
from auth_service.services.jwt_verifier import JWTVerifier
from auth_service.services.claims import parse_claims


def dashboard(request):
    """Simple dashboard overview"""
    claims = JWTVerifier.claims_from_request(request)
    if not claims:
        return redirect('/auth/login/keycloak/')
    if claims:
        info = parse_claims(claims)
        if info['is_employee']:
            return redirect('leavemanagementsystem:mark_attendance')
    total_employees = Employee.objects.active().count()
    total_departments = Department.objects.filter(is_active=True).count()
    manager_stats = Employee.objects.active().annotate(
        subordinate_count=Count('subordinates')
    ).filter(subordinate_count__gt=0)[:5]

    context = {
        'total_employees': total_employees,
        'total_departments': total_departments,
        'manager_stats': manager_stats,
    }
    return render(request, 'core/dashboard.html', context)