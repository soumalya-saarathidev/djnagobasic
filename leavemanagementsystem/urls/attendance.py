# leavemanagementsystem/urls/attendance.py
from django.urls import path
from leavemanagementsystem.views.attendance import mark_attendance

urlpatterns = [
    path('mark-attendance/', mark_attendance, name='mark_attendance'),
]