from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from core.authz import require_roles
from django.urls import reverse_lazy
from django.db.models import Q
from core.models import Employee
from core.forms import EmployeeForm


@method_decorator(require_roles('admin', 'manager'), name='dispatch')
class EmployeeListView(LoginRequiredMixin, ListView):
    """List and search employees"""
    model = Employee
    template_name = 'core/employee_list.html'
    context_object_name = 'employees'
    paginate_by = 20

    def get_queryset(self):
        qs = Employee.objects.active().select_related('department', 'manager')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                Q(employee_id__icontains=q) |
                Q(position__icontains=q)
            )
        dept = self.request.GET.get('department')
        if dept:
            qs = qs.filter(department_id=dept)
        return qs


@method_decorator(require_roles('admin', 'manager', 'employee'), name='dispatch')
class EmployeeDetailView(LoginRequiredMixin, DetailView):
    """View employee details"""
    model = Employee
    template_name = 'core/employee_detail.html'
    context_object_name = 'employee'


@method_decorator(require_roles('admin', 'manager'), name='dispatch')
class EmployeeCreateView(LoginRequiredMixin, CreateView):
    """Create a new employee"""
    model = Employee
    form_class = EmployeeForm
    template_name = 'core/employee_form.html'
    success_url = reverse_lazy('core:employee_list')


@method_decorator(require_roles('admin', 'manager'), name='dispatch')
class EmployeeUpdateView(LoginRequiredMixin, UpdateView):
    """Edit employee details"""
    model = Employee
    form_class = EmployeeForm
    template_name = 'core/employee_form.html'
    success_url = reverse_lazy('core:employee_list')


@method_decorator(require_roles('admin'), name='dispatch')
class EmployeeDeleteView(LoginRequiredMixin, DeleteView):
    """Delete employee"""
    model = Employee
    template_name = 'core/employee_confirm_delete.html'
    success_url = reverse_lazy('core:employee_list')