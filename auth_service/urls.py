# auth_service/urls.py
from django.urls import path
from django.shortcuts import redirect
from .views import auth_views, user_views
from rest_framework.decorators import api_view, authentication_classes
from auth_service.authentication import KeycloakJWTAuthentication


@api_view(['GET'])
@authentication_classes([KeycloakJWTAuthentication])
def home_view(request):
    # If authenticated, serve frontend or dashboard
    if request.user.is_authenticated:
        # For SPA: return HttpResponse(open('static/index.html').read(), content_type='text/html')
        return redirect('core:dashboard')  # Or serve static files
    # Else, redirect to login with next
    next_url = request.GET.get('next', '/')
    return redirect(f"/auth/login/keycloak?next={next_url}")


app_name = "auth_service"

urlpatterns = [
    # path("", home_view, name="home"),
    path("login/", auth_views.login_view, name="login"),
    path("login/keycloak", auth_views.login_view, name="login_keycloak"),
    path("callback/", auth_views.callback_view, name="callback"),
    path("callback/<str:provider>", auth_views.callback_view, name="callback_provider"),
    path("logout/", auth_views.logout_view, name="logout"),
    path("me/", user_views.MeView.as_view(), name="me"),
    path("permissions/", user_views.PermissionsView.as_view(), name="permissions"),
    path("otp/", auth_views.OTPVerificationView, name="otp_verification"),
    path("forgotpassword/", auth_views.forgot_password_view, name="forgot_password"),
]