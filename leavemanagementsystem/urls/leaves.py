from django.urls import path
from leavemanagementsystem.views.leaves import (
    LeaveListView, LeaveCreateView, LeaveUpdateView, LeaveDeleteView
)

app_name = "leaves"

urlpatterns = [
    path('', LeaveListView.as_view(), name='leave_list'),
    path('create/', LeaveCreateView.as_view(), name='leave_create'),
    path('<int:pk>/edit/', LeaveUpdateView.as_view(), name='leave_edit'),
    path('<int:pk>/delete/', LeaveDeleteView.as_view(), name='leave_delete'),
]