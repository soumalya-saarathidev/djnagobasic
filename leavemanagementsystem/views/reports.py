from django.views.generic import TemplateView
from leavemanagementsystem.models.leaves import LeaveRequest, LeaveType


class LeaveSummaryReportView(TemplateView):
    template_name = 'leavemanagementsystem/reports/leave_summary.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        summary = (
            LeaveRequest.objects
            .values('leave_type__name', 'status')
            .order_by('leave_type__name')
        )
        context['summary'] = summary
        return context


class DepartmentLeaveReportView(TemplateView):
    template_name = 'leavemanagementsystem/reports/department_leave_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = (
            LeaveRequest.objects
            .select_related('employee__department')
            .values('employee__department__name', 'status')
            .order_by('employee__department__name')
        )
        context['report'] = report
        return context