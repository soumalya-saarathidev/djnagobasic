from django.contrib import admin
from leavemanagementsystem.models.leaves import LeaveType, LeaveRequest, LeaveBalance, MarkAttendance


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'max_days_per_year', 'is_active')
    search_fields = ('name',)
    list_filter = ('is_active',)


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'status')
    search_fields = ('employee__first_name', 'employee__last_name', 'leave_type__name')
    list_filter = ('status', 'leave_type')


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'balance_days')
    search_fields = ('employee__first_name', 'employee__last_name')

@admin.register(MarkAttendance)
class MarkAttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'status', 'leave_request')