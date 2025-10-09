# core/urls/employees.py
from django.urls import path
from core.views.employees import *

app_name = 'employees'

urlpatterns = [
    path('', EmployeeListView.as_view(), name='list'),
    path('add/', EmployeeCreateView.as_view(), name='add'),
    path('<int:pk>/', EmployeeDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', EmployeeUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', EmployeeDeleteView.as_view(), name='delete'),
]