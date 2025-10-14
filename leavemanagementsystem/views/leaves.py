from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from leavemanagementsystem.models.leaves import LeaveRequest
from leavemanagementsystem.forms.leaves import LeaveRequestForm
from auth_service.services.jwt_verifier import JWTVerifier
from auth_service.services.claims import parse_claims


class LeaveListView(ListView):
    model = LeaveRequest
    template_name = 'leaves/leave_list.html'
    context_object_name = 'leaves'
    def get_queryset(self):
        qs = super().get_queryset().select_related('employee__department')
        claims = JWTVerifier.claims_from_request(self.request)
        if not claims:
            return qs.none()
        info = parse_claims(claims)
        if info['is_admin']:
            return qs
        if info['is_manager']:
            # filter by department
            return qs.filter(employee__department__name__iexact=info['department'])
        # employee: only own
        preferred_username = claims.get('preferred_username')
        return qs.filter(employee__email__iexact=claims.get('email'))

class LeaveCreateView(CreateView):
    model = LeaveRequest
    form_class = LeaveRequestForm
    template_name = 'leaves/leave_form.html'
    success_url = reverse_lazy('leavemanagementsystem:leaves:leave_list')


class LeaveUpdateView(UpdateView):
    model = LeaveRequest
    form_class = LeaveRequestForm
    template_name = 'leaves/leave_form.html'
    success_url = reverse_lazy('leave_list')


class LeaveDeleteView(DeleteView):
    model = LeaveRequest
    template_name = 'leaves/leave_confirm_delete.html'
    success_url = reverse_lazy('leave_list')