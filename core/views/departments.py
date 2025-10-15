# core/views/departments.py
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from core.models import Department
from core.forms import DepartmentForm
from core.authz import require_roles


@method_decorator(require_roles("admin", "ceo"), name='dispatch')
class DepartmentListView(LoginRequiredMixin, ListView):
    model = Department
    template_name = 'core/department_list.html'
    context_object_name = 'departments'

    def get_queryset(self):
        qs = Department.objects.filter(is_active=True)
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(name__icontains=q)
        return qs


@method_decorator(require_roles("admin", "ceo"), name='dispatch')
class DepartmentDetailView(LoginRequiredMixin, DetailView):
    model = Department
    template_name = 'core/department_detail.html'
    context_object_name = 'department'


@method_decorator(require_roles("admin", "ceo"), name='dispatch')
class DepartmentCreateView(LoginRequiredMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'core/department_form.html'
    success_url = reverse_lazy('departments:list')


@method_decorator(require_roles("admin", "ceo"), name='dispatch')
class DepartmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'core/department_form.html'
    success_url = reverse_lazy('departments:list')


@method_decorator(require_roles("admin", "ceo"), name='dispatch')
class DepartmentDeleteView(LoginRequiredMixin, DeleteView):
    model = Department
    template_name = 'core/department_confirm_delete.html'
    success_url = reverse_lazy('departments:list')

    def form_valid(self, form):
        self.object.is_active = False
        self.object.save()
        return super().form_valid(form)