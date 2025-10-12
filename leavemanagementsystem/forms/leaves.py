from django import forms
from leavemanagementsystem.models import *
from django.utils import timezone


class LeaveTypeForm(forms.ModelForm):
    class Meta:
        model = LeaveType
        fields = ['name', 'description', 'max_days_per_year', 'is_active']

    def clean_max_days_per_year(self):
        days = self.cleaned_data.get('max_days_per_year')
        if days < 0:
            raise forms.ValidationError("Max days per year cannot be negative.")
        return days

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['employee', 'leave_type', 'start_date', 'end_date', 'reason']

    def clean(self):
        cleaned_data = super().clean()
        employee = cleaned_data.get('employee')
        leave_type = cleaned_data.get('leave_type')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if not all([employee, leave_type, start_date, end_date]):
            return cleaned_data

        if start_date < timezone.now().date():
            self.add_error('start_date', "Cannot start in the past.")

        if end_date < start_date:
            self.add_error('end_date', "End date cannot be before start date.")

        total_days = (end_date - start_date).days + 1
        balance = LeaveBalance.objects.filter(employee=employee, leave_type=leave_type).first()
        if balance and total_days > balance.balance_days:
            self.add_error('leave_type', "Insufficient leave balance.")

        return cleaned_data

class LeaveBalanceForm(forms.ModelForm):
    class Meta:
        model = LeaveBalance
        fields = ['employee', 'leave_type', 'balance_days']

    def clean_balance_days(self):
        days = self.cleaned_data.get('balance_days')
        if days < 0:
            raise forms.ValidationError("Leave balance cannot be negative.")
        return days
