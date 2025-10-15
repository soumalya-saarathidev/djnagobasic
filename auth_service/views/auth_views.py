# auth_service/views/auth_views.py
from django.shortcuts import redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.urls import reverse
from urllib.parse import urlencode
from django.conf import settings
from ..services.provider_factory import ProviderFactory


def _build_redirect_uri(request):
    """Construct redirect URI for Keycloak callback."""
    return request.build_absolute_uri(reverse("auth_service:callback"))


def login_view(request):
    """Redirect user to Keycloak for authentication."""
    provider_name = request.GET.get("provider", "keycloak")
    provider = ProviderFactory.get_provider(provider_name)
    redirect_uri = _build_redirect_uri(request)
    auth_url = provider.get_authorize_url(redirect_uri)
    return redirect(auth_url)


def callback_view(request):
    """Handle Keycloak OAuth2 callback and exchange code for tokens."""
    provider_name = request.GET.get("provider", "keycloak")
    code = request.GET.get("code")

    if not code:
        return HttpResponseBadRequest("Missing authorization code")

    provider = ProviderFactory.get_provider(provider_name)
    redirect_uri = _build_redirect_uri(request)

    try:
        token_data = provider.exchange_code(code, redirect_uri)
    except Exception as e:
        return HttpResponseBadRequest(f"Token exchange failed: {str(e)}")

    access_token = token_data.get("access_token")
    id_token = token_data.get("id_token")
    if not access_token:
        return HttpResponseBadRequest("Missing access token in response.")

    # Store ID token for logout
    request.session["id_token"] = id_token

    # Redirect to internal /auth/me endpoint
    me_url = reverse("auth_service:me")
    params = urlencode({
        "token": access_token,
        "provider": provider_name,
    })
    return redirect(f"{me_url}?{params}")


def logout_view(request):
    """Logout from Keycloak and clear session."""
    id_token = request.session.get("id_token") or request.GET.get("id_token")
    request.session.flush()

    logout_base = (
        f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/logout"
    )
    params = {
        "post_logout_redirect_uri": request.build_absolute_uri(reverse("auth_service:login")),
    }
    if id_token:
        params["id_token_hint"] = id_token

    return redirect(f"{logout_base}?{urlencode(params)}")