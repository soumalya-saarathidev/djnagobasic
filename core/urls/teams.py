from django.urls import path
from core.views.team import MyTeamTemplateView, MyTeamAPIView

app_name = "teams"

urlpatterns = [
    path("", MyTeamTemplateView.as_view(), name="my_team"),
    path("api/", MyTeamAPIView.as_view(), name="my_team_api"),
]