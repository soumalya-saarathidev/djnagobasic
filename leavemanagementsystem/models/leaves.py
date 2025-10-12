from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date
from core.models import Employee


def initialize_leave_balances(employee=None):
    """
    Calculate leave balances based on hire date:
    - Each month: 2 leaves credited.
    - Joining between 1-14: 1 day credited first month.
    - Joining between 15-31: 2 days credited first month.
    """
    employees = [employee] if employee else Employee.objects.filter(is_active=True)
    leave_types = LeaveType.objects.filter(is_active=True)

    today = date.today()

    for emp in employees:
        # Number of months worked including current month
        months_worked = (today.year - emp.hire_date.year) * 12 + (today.month - emp.hire_date.month)
        for leave_type in leave_types:
            # Determine first month credit
            if emp.hire_date.day <= 14:
                first_month_credit = 1
            else:
                first_month_credit = 2

            total_balance = first_month_credit + months_worked * 2

            # Ensure balance does not exceed max_days_per_year
            max_balance = leave_type.max_days_per_year
            if total_balance > max_balance:
                total_balance = max_balance

            LeaveBalance.objects.update_or_create(
                employee=emp,
                leave_type=leave_type,
                defaults={'balance_days': total_balance}
            )

class LeaveType(models.Model):
    """Defines leave categories like Casual, Sick, Earned, etc."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    max_days_per_year = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @classmethod
    def create_default_types(cls):
        """Factory method for initializing default leave types."""
        defaults = [
            ("Casual Leave", "General purpose leave", 12),
            ("Sick Leave", "Health-related absence", 10),
            ("Earned Leave", "Accumulated paid leave", 15),
        ]
        for name, desc, days in defaults:
            cls.objects.get_or_create(name=name, defaults={
                "description": desc,
                "max_days_per_year": days
            })

class LeaveRequest(models.Model):
    """Stores employee leave requests."""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        constraints = [
            models.CheckConstraint(check=models.Q(end_date__gte=models.F('start_date')), name='valid_date_range')
        ]

    def clean(self):
        """Custom validation for leave request."""
        if self.start_date < timezone.now().date():
            raise ValidationError("Leave cannot start in the past.")
        if self.end_date < self.start_date:
            raise ValidationError("End date cannot be before start date.")

    def duration(self):
        """Total leave days requested."""
        return (self.end_date - self.start_date).days + 1

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.start_date} → {self.end_date})"

class LeaveBalance(models.Model):
    """Tracks remaining leave balance per employee per leave type."""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    balance_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        unique_together = ('employee', 'leave_type')

    def __str__(self):
        return f"{self.employee} - {self.leave_type}: {self.balance_days} days"

    def deduct_days(self, days):
        """Deduct leave balance safely."""
        if days > self.balance_days:
            raise ValueError("Insufficient leave balance.")
        self.balance_days -= days
        self.save(update_fields=['balance_days'])

class MarkAttendance(models.Model):
    """Tracks daily attendance of employees."""
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('LEAVE', 'On Leave'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PRESENT')
    leave_request = models.ForeignKey(LeaveRequest, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee} - {self.date} ({self.status})"