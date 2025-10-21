import logging
import time
import traceback
from urllib.parse import urlencode
from django.shortcuts import redirect
from django.http import HttpResponseBadRequest
from django.urls import reverse
from django.conf import settings
from auth_service.services.provider_factory import ProviderFactory

# Configure module-level logger
logger = logging.getLogger(__name__)


def _build_redirect_uri(request, provider_name="keycloak"):
    """Construct redirect URI for Keycloak callback."""
    path = reverse("auth_service:callback_provider", args=[provider_name])
    uri = f"{settings.BASE_URL}{path}"
    logger.debug(f"🔗 Built fixed redirect URI for provider '{provider_name}': {uri}")
    return uri


def login_view(request):
    """Redirect user to Keycloak for authentication."""
    provider_name = request.GET.get("provider", "keycloak")
    next_url = request.GET.get("next", "/")

    # 🚫 If already authenticated — skip Keycloak redirect
    if request.session.get("access_token"):
        logger.info("✅ User already has an access token; skipping Keycloak login redirect")
        return redirect(next_url)

    provider = ProviderFactory.get_provider(provider_name)
    redirect_uri = _build_redirect_uri(request, provider_name)
    auth_url = provider.get_authorize_url(redirect_uri)

    # Preserve `next` in session
    request.session["next_url"] = next_url

    logger.info(f"🌐 Redirecting to provider '{provider_name}' for login")
    logger.debug({
        "auth_url": auth_url,
        "next_url": next_url,
        "redirect_uri": redirect_uri,
        "session_key": request.session.session_key
    })

    return redirect(auth_url)


def callback_view(request, provider=None):
    provider_name = provider or request.GET.get("provider", "keycloak")
    code = request.GET.get("code")
    state = request.GET.get("state")

    # 🚫 Prevent recursive callbacks
    if request.session.get("access_token"):
        logger.warning(
            "⚠️ Callback called again but session already has access_token — skipping re-login"
        )
        next_url = request.session.get("next_url", "/")
        # include token in redirect for frontend apps
        params = urlencode({"token": request.session["access_token"], "provider": provider_name})
        final_redirect = f"{next_url}?{params}"
        return redirect(final_redirect)

    if not code:
        logger.error("❌ Missing authorization code in Keycloak callback")
        return HttpResponseBadRequest("Missing authorization code")

    provider = ProviderFactory.get_provider(provider_name)
    redirect_uri = _build_redirect_uri(request, provider_name)

    logger.info(f"🎯 Callback received from '{provider_name}'")
    logger.debug({
        "code": code,
        "state": state,
        "redirect_uri": redirect_uri
    })

    try:
        token_data = provider.exchange_code(code, redirect_uri)
        logger.debug("✅ Token exchange success")
        logger.debug({
            "access_token_start": token_data.get("access_token", "")[:30] + "...",
            "refresh_token_present": bool(token_data.get("refresh_token")),
            "expires_in": token_data.get("expires_in"),
        })
    except Exception as e:
        logger.exception(f"❌ Token exchange failed for provider {provider_name}")
        return HttpResponseBadRequest(f"Token exchange failed: {str(e)}")

    access_token = token_data.get("access_token")
    id_token = token_data.get("id_token")
    refresh_token = token_data.get("refresh_token")

    if not access_token:
        logger.error("❌ Missing access token in token_data")
        return HttpResponseBadRequest("Missing access token")

    # ✅ Store tokens in session so middleware can read them
    request.session["access_token"] = access_token
    request.session["refresh_token"] = refresh_token
    request.session["id_token"] = id_token
    request.session["token_expires_in"] = token_data.get("expires_in", 300)
    request.session["token_issued_at"] = time.time()

    logger.info("💾 Tokens stored in session")
    logger.debug({
        "session_key": request.session.session_key,
        "expires_in": request.session["token_expires_in"],
        "issued_at": request.session["token_issued_at"]
    })

    # ✅ Pop next_url from session, redirect with token in query param
    next_url = request.session.pop("next_url", "/")
    params = urlencode({"token": access_token, "provider": provider_name})
    final_redirect = f"{next_url}?{params}"

    logger.info(f"🔁 Redirecting post-login to: {final_redirect}")
    return redirect(final_redirect)


def logout_view(request):
    """Logout from Keycloak and clear session."""
    id_token = request.session.get("id_token") or request.GET.get("id_token")
    session_key = request.session.session_key

    logger.info("🚪 Logging out user from Keycloak")
    logger.debug({
        "session_key": session_key,
        "id_token_present": bool(id_token)
    })

    request.session.flush()

    logout_base = (
        f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/logout"
    )
    params = {
        "post_logout_redirect_uri": request.build_absolute_uri(reverse("auth_service:login")),
    }
    if id_token:
        params["id_token_hint"] = id_token

    final_logout_url = f"{logout_base}?{urlencode(params)}"
    logger.debug(f"🧹 Redirecting to Keycloak logout URL: {final_logout_url}")
    return redirect(final_logout_url)