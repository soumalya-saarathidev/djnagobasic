# core/views/employees.py
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.db.models import Q
from core.models import Employee
from core.forms import EmployeeForm
from core.authz import require_roles


@method_decorator(require_roles("admin", "manager", "vp", "ceo"), name='dispatch')
class EmployeeListView(LoginRequiredMixin, ListView):
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


@method_decorator(require_roles("admin", "manager", "vp", "ceo"), name='dispatch')
class EmployeeDetailView(LoginRequiredMixin, DetailView):
    model = Employee
    template_name = 'core/employee_detail.html'
    context_object_name = 'employee'


@method_decorator(require_roles("admin", "manager", "vp", "ceo"), name='dispatch')
class EmployeeCreateView(LoginRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'core/employee_form.html'
    success_url = reverse_lazy('employees:list')


@method_decorator(require_roles("admin", "manager", "vp", "ceo"), name='dispatch')
class EmployeeUpdateView(LoginRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'core/employee_form.html'
    success_url = reverse_lazy('employees:list')


@method_decorator(require_roles("admin", "ceo"), name='dispatch')
class EmployeeDeleteView(LoginRequiredMixin, DeleteView):
    model = Employee
    template_name = 'core/employee_confirm_delete.html'
    success_url = reverse_lazy('employees:list')