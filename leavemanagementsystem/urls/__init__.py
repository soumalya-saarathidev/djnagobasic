# leavemanagementsystem/urls/__init__.py
from django.urls import path, include
from leavemanagementsystem.views.attendance import mark_attendance

# Group all URLs in one namespace
app_name = "leavemanagementsystem"

urlpatterns = [
    path("leaves/", include("leavemanagementsystem.urls.leaves")),
    path("reports/", include("leavemanagementsystem.urls.reports")),
    path('attendance/', include('leavemanagementsystem.urls.attendance')),
    # Direct, clean route to mark attendance page
    path('attendance/mark/', mark_attendance, name='mark_attendance'),
]