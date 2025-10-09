import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError

class BaseModel(models.Model):
    """
    Abstract base model with common fields and OOP concepts
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        abstract = True
    
    def soft_delete(self):
        """Soft delete method - OOP concept"""
        self.is_active = False
        self.save()
    
    def restore(self):
        """Restore soft deleted record - OOP concept"""
        self.is_active = True
        self.save()

class Department(BaseModel):
    """ Department model """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
    
    def __str__(self):
        return self.name
    
    def get_employee_count(self):
        """Method to get employee count"""
        return self.employees.filter(is_active=True).count()
    
    def get_total_salary_budget(self):
        """Calculate total salary budget for department"""
        return sum(emp.salary_monthly for emp in self.employees.filter(is_active=True))

class EmployeeManager(models.Manager):
    """ Custom manager for Employee model """
    def active(self):
        return self.filter(is_active=True)
    
    def by_department(self, department):
        return self.filter(department=department, is_active=True)
    
    def senior_employees(self, years=5):
        """Get employees with more than specified years of experience"""
        cutoff_date = timezone.now().date().replace(year=timezone.now().year - years)
        return self.filter(hire_date__lte=cutoff_date, is_active=True)

class Employee(BaseModel):
    """ Employee model with auto-generated ID """
    # Auto-generated alphanumeric ID
    employee_id = models.CharField(max_length=10, unique=True, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='employees')
    
    # Personal Information
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    
    # Employment Information
    position = models.CharField(max_length=100)
    hire_date = models.DateField()
    salary_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Simple Manager relationship - One-to-Many (Employee can have one manager)
    manager = models.ForeignKey('self', 
                               on_delete=models.SET_NULL, 
                               null=True, 
                               blank=True, 
                               related_name='subordinates')
    
    # Address
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=10)
    country = models.CharField(max_length=50, default='IND')
    
    # Additional Information
    years_of_experience = models.PositiveIntegerField(default=0)
    
    # Custom manager
    objects = EmployeeManager()
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"
    
    def clean(self):
        # Only validate if value exists
        if self.salary_monthly is not None and self.salary_monthly < 0:
            raise ValidationError({'salary_monthly': 'Salary cannot be negative.'})

        if self.hire_date is not None and self.hire_date > timezone.now().date():
            raise ValidationError({'hire_date': 'Hire date cannot be in the future.'})

        if self.manager is not None and self.pk and self.manager.pk == self.pk:
            raise ValidationError({'manager': 'Employee cannot be their own manager.'})

        return cleaned_data
    
    def save(self, *args, **kwargs):
        """Override save to generate employee ID - OOP concept"""
        if not self.employee_id:
            self.employee_id = self.generate_employee_id()
        super().save(*args, **kwargs)
    
    def generate_employee_id(self):
        """Generate unique alphanumeric employee ID - OOP concept"""
        import random
        import string
        
        while True:
            # Format: EMP + 7 random alphanumeric characters
            random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
            employee_id = f"EMP{random_part}"
            
            if not Employee.objects.filter(employee_id=employee_id).exists():
                return employee_id
    
    def get_full_name(self):
        """Get full name - OOP concept"""
        return f"{self.first_name} {self.last_name}"
    
    def get_annual_salary(self):
        """Calculate annual salary - OOP concept"""
        return self.salary_monthly * 12
    
    def get_manager_name(self):  ##need to change logic
        """Get manager's full name - OOP concept"""
        if self.manager:
            return self.manager.get_full_name()
        return "No Manager"
    
    def get_subordinates_count(self):
        """Get count of subordinates - OOP concept"""
        return self.subordinates.filter(is_active=True).count()
    
    def clean(self):
        """Custom validation - OOP concept"""
        super().clean()
        if self.salary_monthly is not None and self.salary_monthly < 0:
            raise ValidationError({'salary_monthly': 'Salary cannot be negative'})
        
        if self.hire_date and self.hire_date > timezone.now().date():
            raise ValidationError({'hire_date': 'Hire date cannot be in the future'})
        
        # Prevent self-assignment as manager
        if self.manager and self.manager.id == self.id:
            raise ValidationError({'manager': 'Employee cannot be their own manager'})