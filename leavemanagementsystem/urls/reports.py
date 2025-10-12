from django.urls import path
from leavemanagementsystem.views.reports import LeaveSummaryReportView, DepartmentLeaveReportView

app_name = "reports"

urlpatterns = [
    path('summary/', LeaveSummaryReportView.as_view(), name='leave_summary_report'),
    path('departmentreports/', DepartmentLeaveReportView.as_view(), name='department_leave_report'),
]