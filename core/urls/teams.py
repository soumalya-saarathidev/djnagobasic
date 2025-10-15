# core/urls/teams.py
from django.urls import path
from core.views.team import my_team_view

app_name = 'teams'

urlpatterns = [
    path('', my_team_view, name='my_team'),
]