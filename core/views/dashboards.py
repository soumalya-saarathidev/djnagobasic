from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import render
from core.models import Employee, Department


def dashboard(request):
    """Simple dashboard overview"""
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