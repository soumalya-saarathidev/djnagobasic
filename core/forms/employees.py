from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models import Employee, Department


class EmployeeForm(forms.ModelForm):
    """
    Employee form with business validation rules.
    Implements OOP patterns for reusability and clean validation layering.
    """

    class Meta:
        model = Employee
        fields = [
            'user', 'department', 'first_name', 'last_name', 'email', 'phone',
            'position', 'hire_date', 'salary_monthly', 'manager',
            'city', 'state', 'zip_code', 'country'
        ]
        widgets = {
            'hire_date': forms.DateInput(attrs={'type': 'date'}),
            'salary_monthly': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter only active departments
        self.fields['department'].queryset = Department.objects.filter(is_active=True).order_by('name')

        # Filter users that don’t already have employee profiles
        self.fields['user'].queryset = User.objects.filter(employee_profile__isnull=True).order_by('username')

        # Manager field logic: Exclude current employee from manager options
        qs = Employee.objects.active().order_by('first_name', 'last_name')
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        self.fields['manager'].queryset = qs

        # Optional UX hints
        self.fields['email'].help_text = "Employee's official company email."
        self.fields['salary_monthly'].help_text = "Enter gross monthly salary (must be non-negative)."

    def clean_email(self):
        """Ensure email uniqueness among active employees."""
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError("Email is required.")

        exists = Employee.objects.filter(email__iexact=email, is_active=True)
        if self.instance.pk:
            exists = exists.exclude(pk=self.instance.pk)

        if exists.exists():
            raise ValidationError("An employee with this email already exists.")
        return email

    def clean_salary_monthly(self):
        """Ensure salary is non-negative."""
        salary = self.cleaned_data.get('salary_monthly')
        if salary is None:
            raise forms.ValidationError('Salary is required.')
        elif salary < 0:
            raise forms.ValidationError('Salary cannot be negative.')
        return salary

    def clean_hire_date(self):
        """Ensure hire date is not in the future."""
        hire_date = self.cleaned_data.get('hire_date')
        if hire_date and hire_date > timezone.now().date():
            raise ValidationError("Hire date cannot be in the future.")
        return hire_date

    def clean_manager(self):
        """Prevent employees from being their own manager."""
        manager = self.cleaned_data.get('manager')
        if manager and self.instance.pk and manager.pk == self.instance.pk:
            raise ValidationError("An employee cannot be their own manager.")
        return manager