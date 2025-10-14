from django.shortcuts import render, redirect
from django.contrib import messages
from leavemanagementsystem.forms.attendance import MarkAttendanceForm
from leavemanagementsystem.models.leaves import MarkAttendance
from auth_service.services.jwt_verifier import JWTVerifier
from auth_service.services.claims import parse_claims

def mark_attendance(request):
    """View to mark daily attendance."""
    claims = JWTVerifier.claims_from_request(request)
    if not claims:
        return redirect('/auth/login/keycloak/')
    info = parse_claims(claims)
    if request.method == 'POST':
        form = MarkAttendanceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Attendance marked successfully.")
            return redirect('mark_attendance')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = MarkAttendanceForm()

    # Show recent attendance based on role
    qs = MarkAttendance.objects.select_related('employee__department').order_by('-date')
    if info['is_admin']:
        recent_attendance = qs[:10]
    elif info['is_manager']:
        recent_attendance = qs.filter(employee__department__name__iexact=info['department'])[:10]
    else:
        recent_attendance = qs.filter(employee__email__iexact=claims.get('email'))[:10]

    return render(request, 'leavemanagementsystem/attendance/mark_attendance.html', {
        'form': form,
        'recent_attendance': recent_attendance
    })