from django.contrib import admin
from .models import Department, Employee

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'budget', 'get_employee_count', 'is_active')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'first_name', 'last_name', 'department', 'position', 'manager', 'salary_monthly', 'is_active')
    list_filter = ('department', 'manager', 'is_active')
    search_fields = ('employee_id', 'first_name', 'last_name', 'email')
    readonly_fields = ('employee_id', 'created_at', 'updated_at')