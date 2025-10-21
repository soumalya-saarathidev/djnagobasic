# leavemanagementsystem/views/attendance.py
from django.shortcuts import render, redirect
from django.contrib import messages
from leavemanagementsystem.forms.attendance import MarkAttendanceForm
from leavemanagementsystem.models.leaves import MarkAttendance
from auth_service.services.jwt_verifier import JWTVerifier
from auth_service.services.claims import parse_claims
from auth_service.authentication import KeycloakJWTAuthentication
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated


@authentication_classes([KeycloakJWTAuthentication])
@permission_classes([IsAuthenticated])
def mark_attendance(request):
    """Attendance dashboard with role-aware filtering and form submit."""
    claims = JWTVerifier.claims_from_request(request)
    parsed = parse_claims(claims)

    if request.method == "POST":
        form = MarkAttendanceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Attendance marked successfully.")
            return redirect("mark_attendance")
        messages.error(request, "Please correct the errors below.")
    else:
        form = MarkAttendanceForm()

    qs = MarkAttendance.objects.select_related("employee__department").order_by("-date")

    if parsed.get("is_admin") or parsed.get("is_ceo"):
        recent_attendance = qs[:10]
    elif parsed.get("is_manager") or parsed.get("is_vp"):
        recent_attendance = qs.filter(employee__department__name__iexact=parsed.get("department"))[:10]
    else:
        recent_attendance = qs.filter(employee__email__iexact=claims.get("email"))[:10]

    return render(request, "leavemanagementsystem/attendance/mark_attendance.html", {
        "form": form,
        "recent_attendance": recent_attendance,
        "parsed": parsed,
    })