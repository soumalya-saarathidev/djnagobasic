from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.models import Employee
from auth_service.services.claims import parse_claims
from core.authz import require_roles

@require_roles('manager', 'admin')
def my_team_view(request):
    claims = request.auth_claims
    info = parse_claims(claims)
    
    # In a real scenario, you'd filter subordinates based on the manager's ID from claims
    employees = Employee.objects.filter(department__name=info['department'])
    
    context = {
        'employees': employees,
        'department': info['department']
    }
    return render(request, 'core/my_team.html', context)
