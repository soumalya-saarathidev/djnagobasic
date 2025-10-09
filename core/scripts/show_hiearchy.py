import sys
import os
import django

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "employeesystem.settings")
django.setup()

from core.models import Employee

def print_hierarchy(emp, level=0):
    print("    " * level + f"- {emp.get_full_name()} ({emp.position})")
    for sub in emp.subordinates.all():
        print_hierarchy(sub, level+1)

if __name__ == "__main__":
    top_managers = Employee.objects.filter(manager=None)
    for tm in top_managers:
        print_hierarchy(tm)