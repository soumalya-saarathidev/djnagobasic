from django.contrib.auth.models import User
from core.models import Department, Employee
from datetime import date
from django.db.utils import IntegrityError

def run():
    """Populate test data for employees safely"""
    
    # --- Departments ---
    dept_sales, created = Department.objects.get_or_create(
        name="Sales",
        defaults={"description": "Sales Department", "budget": 500000}
    )
    dept_eng, created = Department.objects.get_or_create(
        name="Engineering",
        defaults={"description": "Engineering Department", "budget": 700000}
    )
    dept_exec, created = Department.objects.get_or_create(
        name="Executive",
        defaults={"description": "Executive Department", "budget": 1000000}
    )

    # --- Users ---
    users_data = [
        ("alice", "alice@company.com"),
        ("bob", "bob@company.com"),
        ("carol", "carol@company.com"),
        ("david", "david@company.com"),
        ("eve", "eve@company.com"),
        ("frank", "frank@company.com"),
        ("grace", "grace@company.com"),
        ("heidi", "heidi@company.com")
    ]
    users = []

    for username, email in users_data:
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email}
        )
        if created:
            user.set_password("Password123!")
            user.save()
        users.append(user)

    # --- Employees ---
    # Skip creating employees if they already exist
    if Employee.objects.exists():
        print("Employee data already exists. Skipping insertion.")
        return

    # Level 1
    e1 = Employee.objects.create(
        user=users[0],
        first_name="Alice", last_name="CEO",
        email=users[0].email, phone="1111111111",
        department=dept_exec, position="CEO", hire_date=date(2010,1,1),
        salary_monthly=20000, manager=None,
        city="Mumbai", state="MH", zip_code="400001"
    )

    # Level 2
    e2 = Employee.objects.create(
        user=users[1],
        first_name="Bob", last_name="VP1",
        email=users[1].email, phone="2222222222",
        department=dept_sales, position="VP Sales", hire_date=date(2012,5,1),
        salary_monthly=15000, manager=e1,
        city="Mumbai", state="MH", zip_code="400002"
    )

    e3 = Employee.objects.create(
        user=users[2],
        first_name="Carol", last_name="VP2",
        email=users[2].email, phone="3333333333",
        department=dept_eng, position="VP Engineering", hire_date=date(2012,6,1),
        salary_monthly=15000, manager=e1,
        city="Pune", state="MH", zip_code="411001"
    )

    # Level 3
    e4 = Employee.objects.create(
        user=users[3],
        first_name="David", last_name="Sales1",
        email=users[3].email, phone="4444444444",
        department=dept_sales, position="Sales Executive", hire_date=date(2015,3,1),
        salary_monthly=9000, manager=e2,
        city="Mumbai", state="MH", zip_code="400003"
    )

    e5 = Employee.objects.create(
        user=users[4],
        first_name="Eve", last_name="Sales2",
        email=users[4].email, phone="5555555555",
        department=dept_sales, position="Sales Executive", hire_date=date(2015,4,1),
        salary_monthly=9000, manager=e2,
        city="Mumbai", state="MH", zip_code="400004"
    )

    e6 = Employee.objects.create(
        user=users[5],
        first_name="Frank", last_name="Eng1",
        email=users[5].email, phone="6666666666",
        department=dept_eng, position="Engineer", hire_date=date(2016,7,1),
        salary_monthly=9500, manager=e3,
        city="Pune", state="MH", zip_code="411002"
    )

    e7 = Employee.objects.create(
        user=users[6],
        first_name="Grace", last_name="Eng2",
        email=users[6].email, phone="7777777777",
        department=dept_eng, position="Engineer", hire_date=date(2016,8,1),
        salary_monthly=9500, manager=e3,
        city="Pune", state="MH", zip_code="411003"
    )

    # Level 4
    e8 = Employee.objects.create(
        user=users[7],
        first_name="Heidi", last_name="Eng3",
        email=users[7].email, phone="8888888888",
        department=dept_eng, position="Engineer", hire_date=date(2018,9,1),
        salary_monthly=9000, manager=e6,
        city="Pune", state="MH", zip_code="411004"
    )

    print("Test employee data successfully populated.")