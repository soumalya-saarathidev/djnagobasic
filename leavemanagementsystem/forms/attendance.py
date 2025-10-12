from django import forms
from leavemanagementsystem.models.leaves import MarkAttendance
from core.models import Employee
from django.utils import timezone

class MarkAttendanceForm(forms.ModelForm):
    """Form to mark attendance for an employee."""

    class Meta:
        model = MarkAttendance
        fields = ['employee', 'date', 'status', 'leave_request']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'max': timezone.now().date()}),
        }

    def clean_date(self):
        date_val = self.cleaned_data.get('date')
        if date_val > timezone.now().date():
            raise forms.ValidationError("Attendance cannot be marked for a future date.")
        return date_val