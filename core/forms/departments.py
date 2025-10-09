from django import forms
from django.core.exceptions import ValidationError
from core.models import Department


class DepartmentForm(forms.ModelForm):
    """
    Department creation/update form.
    Includes duplicate prevention and logical validation.
    """

    class Meta:
        model = Department
        fields = ['name', 'description', 'budget']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Finance'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Short description of department'}),
            'budget': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def clean_name(self):
        """Ensure department name is unique among active departments."""
        name = self.cleaned_data.get('name')
        if not name:
            raise ValidationError("Department name is required.")

        qs = Department.objects.filter(name__iexact=name.strip(), is_active=True)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(f"A department named '{name}' already exists.")
        return name

    def clean_budget(self):
        """Ensure budget is a non-negative number."""
        budget = self.cleaned_data.get('budget')
        if budget is not None and budget < 0:
            raise ValidationError("Budget cannot be negative.")
        return budget