# core/urls/departments.py
from django.urls import path
from core.views.departments import (
    DepartmentListView,
    DepartmentDetailView,
    DepartmentCreateView,
    DepartmentUpdateView,
    DepartmentDeleteView,
)

app_name = 'departments'

urlpatterns = [
    path('', DepartmentListView.as_view(), name='list'),
    path('add/', DepartmentCreateView.as_view(), name='add'),
    path('<int:pk>/', DepartmentDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', DepartmentUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', DepartmentDeleteView.as_view(), name='delete'),
]