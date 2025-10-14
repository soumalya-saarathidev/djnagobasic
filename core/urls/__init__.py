# core/urls/__init__.py
from django.urls import path, include
from core.views.dashboards import dashboard
from core.views.team import my_team_view

app_name = 'core'

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('team/', my_team_view, name='my_team'),
    path('employees/', include('core.urls.employees')),
    path('departments/', include('core.urls.departments')),
]