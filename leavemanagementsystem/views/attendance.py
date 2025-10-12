from django.shortcuts import render, redirect
from django.contrib import messages
from leavemanagementsystem.forms.attendance import MarkAttendanceForm
from leavemanagementsystem.models.leaves import MarkAttendance

def mark_attendance(request):
    """View to mark daily attendance."""
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

    # Show last 10 attendance records
    recent_attendance = MarkAttendance.objects.select_related('employee').order_by('-date')[:10]

    return render(request, 'leavemanagementsystem/attendance/mark_attendance.html', {
        'form': form,
        'recent_attendance': recent_attendance
    })