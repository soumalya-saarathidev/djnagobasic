# core/urls/__init__.py
from django.urls import path, include
from core.views.dashboards import dashboard

app_name = 'core'

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('teams/', include('core.urls.teams')),
    path('employees/', include('core.urls.employees')),
    path('departments/', include('core.urls.departments')),
]