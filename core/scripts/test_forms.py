import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "employeesystem.settings")
django.setup()


from django.contrib.auth.models import User
from core.models import Employee, Department
from core.forms.departments import DepartmentForm
from core.forms.employees import EmployeeForm
from django.core.exceptions import ValidationError

# --- Utility functions --- #
def get_or_create_department(name, budget=100000):
    """
    Safely get or create a department to avoid duplicates in tests
    """
    dept, created = Department.objects.get_or_create(
        name=name,
        defaults={'budget': budget, 'description': f'{name} Department'}
    )
    return dept

def get_or_create_user(username, email):
    """
    Safely get or create a user for EmployeeForm
    """
    user, created = User.objects.get_or_create(username=username, defaults={'email': email})
    return user

# --- Test Department Form --- #
def test_department_form():
    print("=== Testing Department Form ===")
    dept_name = "Finance"
    
    # Get or create department
    dept = get_or_create_department(dept_name, 500000)

    # Form with duplicate name (should fail)
    data = {'name': dept_name, 'description': 'Finance Department', 'budget': 500000}
    form = DepartmentForm(data)
    print("Duplicate form valid:", form.is_valid())
    if not form.is_valid():
        print("Errors:", form.errors.as_ul())

    # Valid form with new name
    data = {'name': 'Marketing', 'description': 'Marketing Dept', 'budget': 300000}
    form = DepartmentForm(data)
    print("New department form valid:", form.is_valid())
    if not form.is_valid():
        print("Errors:", form.errors.as_ul())

# --- Test Employee Form --- #
def test_employee_form():
    print("\n=== Testing Employee Form ===")

    # Get or create dependencies
    dept = get_or_create_department('Engineering', 200000)
    manager_user = get_or_create_user('manager1', 'manager1@example.com')
    
    # Create manager Employee
    manager, _ = Employee.objects.get_or_create(
        user=manager_user, 
        defaults={
            'first_name': 'Alice',
            'last_name': 'Manager',
            'email': 'manager1@example.com',
            'department': dept,
            'position': 'Team Lead',
            'hire_date': '2020-01-01',
            'salary_monthly': 10000,
        }
    )

    # Valid employee
    user = get_or_create_user('john_doe', 'john@example.com')
    data = {
        'user': user.pk,
        'department': dept.pk,
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john@example.com',
        'phone': '1234567890',
        'position': 'Developer',
        'hire_date': '2025-01-01',
        'salary_monthly': 5000,
        'manager': manager.pk,
        'city': 'Mumbai',
        'state': 'MH',
        'zip_code': '400001',
        'country': 'IND',
    }

    form = EmployeeForm(data)
    print("Employee form valid:", form.is_valid())
    if not form.is_valid():
        print("Errors:", form.errors.as_ul())

    # Test negative salary
    data['salary_monthly'] = -1000
    form = EmployeeForm(data)
    print("Negative salary valid:", form.is_valid())
    if not form.is_valid():
        print("Errors:", form.errors.as_ul())

    # Test self as manager
    data['salary_monthly'] = 5000
    data['manager'] = None  # Temporarily remove to create employee
    form = EmployeeForm(data)  # Create fresh form with valid data
    if form.is_valid():
        emp = form.save(commit=False)
        emp.manager = emp  # set self as manager
        try:
            emp.full_clean()
        except ValidationError as e:
            print("Self as manager validation errors:", e)
    else:
        print("Could not create employee for manager test:", form.errors)

    # Test duplicate email
    data['manager'] = manager.pk
    form = EmployeeForm(data)
    form.is_valid()
    print("Duplicate email valid:", form.is_valid())
    if not form.is_valid():
        print("Errors:", form.errors.as_ul())

# --- Run Tests --- #
if __name__ == "__main__":
    test_department_form()
    test_employee_form()