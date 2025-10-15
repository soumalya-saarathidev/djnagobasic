# auth_service/urls.py
from django.urls import path
from django.shortcuts import redirect
from .views import auth_views, user_views


def home_redirect(request):
    return redirect("auth_service:login")


app_name = "auth_service"

urlpatterns = [
    path("", home_redirect, name="home"),
    path("login/", auth_views.login_view, name="login"),
    path("login/keycloak/", auth_views.login_view, name="login_keycloak"),
    path("callback/", auth_views.callback_view, name="callback"),
    path("logout/", auth_views.logout_view, name="logout"),
    path("me/", user_views.me, name="me"),
    path("permissions/", user_views.permissions, name="permissions"),
]