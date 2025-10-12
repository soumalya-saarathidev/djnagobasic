import os
import sys
import django
from datetime import date, timedelta

# --- Setup Django environment BEFORE imports ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "employeesystem.settings")  # change if your project name differs
django.setup()

# --- Now safe to import Django models/forms ---
from core.models import Employee, Department
from leavemanagementsystem.models.leaves import LeaveType, LeaveBalance, LeaveRequest
from leavemanagementsystem.forms.leaves import LeaveRequestForm


def test_leave_management():
    # Ensure departments and employees exist
    dept, _ = Department.objects.get_or_create(name="Finance")
    emp = Employee.objects.filter(first_name="John").first()

    if not emp:
        print("⚠️ Please create an employee first using core models.")
        return

    # Create default leave types
    LeaveType.create_default_types()

    casual = LeaveType.objects.get(name="Casual Leave")
    LeaveBalance.objects.get_or_create(employee=emp, leave_type=casual, defaults={"balance_days": 10})

    # Test form validation
    form_data = {
        'employee': emp.id,
        'leave_type': casual.id,
        'start_date': date.today() + timedelta(days=1),
        'end_date': date.today() + timedelta(days=3),
        'reason': 'Family event'
    }

    form = LeaveRequestForm(data=form_data)
    print("Leave Request Valid:", form.is_valid())
    if not form.is_valid():
        print("Errors:", form.errors)
    else:
        leave = form.save()
        print(f"✅ Leave created: {leave}")

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

if __name__ == "__main__":
    test_leave_management()
    initialize_leave_balances()