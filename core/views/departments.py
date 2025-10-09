# core/views/departments.py
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from core.models import Department
from core.forms import DepartmentForm

class DepartmentListView(LoginRequiredMixin, ListView):
    """List all active departments"""
    model = Department
    template_name = 'core/department_list.html'
    context_object_name = 'departments'

    def get_queryset(self):
        qs = Department.objects.filter(is_active=True)
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(name__icontains=q)
        return qs


class DepartmentDetailView(LoginRequiredMixin, DetailView):
    """Show details of a single department"""
    model = Department
    template_name = 'core/department_detail.html'
    context_object_name = 'department'


class DepartmentCreateView(LoginRequiredMixin, CreateView):
    """Quick department creation view"""
    model = Department
    form_class = DepartmentForm
    template_name = 'core/department_form.html'
    success_url = reverse_lazy('departments:list')


class DepartmentUpdateView(LoginRequiredMixin, UpdateView):
    """Edit an existing department"""
    model = Department
    form_class = DepartmentForm
    template_name = 'core/department_form.html'
    success_url = reverse_lazy('departments:list')


class DepartmentDeleteView(LoginRequiredMixin, DeleteView):
    """Delete or deactivate a department"""
    model = Department
    template_name = 'core/department_confirm_delete.html'
    success_url = reverse_lazy('departments:list')

    def form_valid(self, form):
        """Soft delete instead of permanent delete"""
        self.object.is_active = False
        self.object.save()
        return super().form_valid(form)