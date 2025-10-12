from datetime import date, timedelta
from django.utils import timezone
import sys,os

# --- Setup Django environment BEFORE imports ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "employeesystem.settings")  # change if your project name differs

import django  
django.setup()

from core.models import Employee, Department
from django.contrib.auth.models import User
from leavemanagementsystem.models.leaves import (
    LeaveType,
    LeaveRequest,
    LeaveBalance,
    MarkAttendance,
    initialize_leave_balances,
)

def get_or_create_departments():
    dept_names = ["Engineering", "HR", "Finance", "Sales"]
    depts = []
    for name in dept_names:
        d, _ = Department.objects.get_or_create(name=name, defaults={
            "description": f"{name} Dept",
            "budget": 100000,
        })
        depts.append(d)
    return depts

def create_employees(departments):
    employees = []

    sample_people = [
        # first_name, last_name, dept_index, position, username
        ("Alice", "CEO", 0, "CEO", "alice"),
        ("Bob", "VP1", 0, "VP Sales", "bob"),
        ("Carol", "VP2", 0, "VP Engineering", "carol"),
        ("Frank", "Eng1", 0, "Engineer", "frank"),
        ("Grace", "Eng2", 0, "Engineer", "grace"),
        ("Heidi", "Eng3", 0, "Engineer", "heidi"),
    ]
    today = date.today()

    for first, last, dept_idx, position, username in sample_people:
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={"first_name": first, "last_name": last, "email": f"{username}@example.com"}
        )

        emp, _ = Employee.objects.get_or_create(
            user=user,
            defaults={
                "department": departments[dept_idx],
                "first_name": first,
                "last_name": last,
                "phone": "9999999999",
                "position": position,
                "hire_date": today - timedelta(days=365),
                "salary_monthly": 5000,
                "city": "City",
                "state": "State",
                "zip_code": "12345",
                "country": "IND",
                "is_active": True,
            },
        )
        employees.append(emp)

    # Assign managers
    user_map = {e.user.username: e for e in employees}
    # example manager mapping
    manager_map = {
        "bob": "alice",
        "carol": "alice",
        "frank": "carol",
        "grace": "carol",
        "heidi": "frank",
    }

    for username, manager_username in manager_map.items():
        emp = user_map[username]
        manager = user_map.get(manager_username)
        if manager and emp.manager_id != manager.id:
            emp.manager = manager
            emp.save(update_fields=["manager"])

    return employees


def seed_leave_types():
    LeaveType.create_default_types()
    return list(LeaveType.objects.all())


def seed_balances(employees):
    initialize_leave_balances()
    return list(LeaveBalance.objects.filter(employee__in=employees))


def seed_leave_requests(employees):
    lt = LeaveType.objects.first()
    today = date.today()
    for e in employees[:3]:
        start = today + timedelta(days=7)
        end = start + timedelta(days=2)
        LeaveRequest.objects.get_or_create(
            employee=e,
            leave_type=lt,
            start_date=start,
            end_date=end,
            defaults={"reason": "Personal"},
        )
    return list(LeaveRequest.objects.all())


def seed_attendance(employees):
    today = date.today()
    for e in employees:
        for i in range(5):
            d = today - timedelta(days=i)
            MarkAttendance.objects.get_or_create(
                employee=e,
                date=d,
                defaults={"status": "PRESENT"},
            )
    return list(MarkAttendance.objects.all())


def main():
    depts = get_or_create_departments()
    employees = create_employees(depts)
    seed_leave_types()
    seed_balances(employees)
    seed_leave_requests(employees)
    seed_attendance(employees)
    print("Demo data populated for Leave Types, Balances, Requests, and Attendance.")


main()


