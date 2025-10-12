from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from leavemanagementsystem.models.leaves import LeaveRequest
from leavemanagementsystem.forms.leaves import LeaveRequestForm


class LeaveListView(ListView):
    model = LeaveRequest
    template_name = 'leaves/leave_list.html'
    context_object_name = 'leaves'


class LeaveCreateView(CreateView):
    model = LeaveRequest
    form_class = LeaveRequestForm
    template_name = 'leaves/leave_form.html'
    success_url = reverse_lazy('leave_list')


class LeaveUpdateView(UpdateView):
    model = LeaveRequest
    form_class = LeaveRequestForm
    template_name = 'leaves/leave_form.html'
    success_url = reverse_lazy('leave_list')


class LeaveDeleteView(DeleteView):
    model = LeaveRequest
    template_name = 'leaves/leave_confirm_delete.html'
    success_url = reverse_lazy('leave_list')