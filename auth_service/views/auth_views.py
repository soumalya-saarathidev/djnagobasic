# auth_service/views/auth_views.py
from django.shortcuts import redirect
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse
from django.urls import reverse
from urllib.parse import urlencode, quote
from django.conf import settings
from auth_service.services.provider_factory import ProviderFactory
from auth_service.services.jwt_verifier import JWTVerifier
from django.views.decorators.csrf import csrf_exempt
import requests
import logging
import random
from django.core.cache import cache

logger = logging.getLogger("auth_service.views.auth_views")


def _build_redirect_uri(provider_name="keycloak"):
    path = reverse("auth_service:callback_provider", args=[provider_name])
    return f"{settings.BASE_URL}{path}"

@csrf_exempt
def login_view(request):
    """Redirect to the appropriate provider for login."""
    provider_name = request.GET.get("provider", "keycloak")
    provider = ProviderFactory.get_provider(provider_name)

    if request.method == "GET":
        next_url = request.GET.get("next", "/")
        redirect_uri = _build_redirect_uri(provider_name)
        auth_url = provider.get_authorize_url(redirect_uri)
        params = urlencode({"next": next_url})
        final_url = f"{auth_url}&{params}" if "?" in auth_url else f"{auth_url}?{params}"
        logger.info(f"🌐 Final URL: {final_url}")
        logger.info(f"🌐 Redirecting to provider '{provider_name}' for login")
        logger.debug({"auth_url": auth_url, "redirect_uri": redirect_uri})
        return redirect(final_url)
    elif request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        token_data = provider.exchange_password(username, password)
        return JsonResponse(token_data, status=200)
    
    return HttpResponseBadRequest("Unsupported method.")

def callback_view(request, provider=None):
    """Handle Keycloak Authorization callback with detailed logging."""
    provider_name = provider or request.GET.get("provider", "keycloak")
    logger.info(f"➡️ Callback invoked for provider: {provider_name}")

    code = request.GET.get("code")
    next_url = request.GET.get("next", "/")
    logger.debug(f"Next URL: {next_url}")

    if not code:
        logger.error("❌ Missing authorization code in Keycloak callback")
        logger.debug(f"Request GET params: {request.GET}")
        return HttpResponseBadRequest("Missing authorization code")

    try:
        logger.info("🔄 Getting provider instance")
        provider_instance = ProviderFactory.get_provider(provider_name)
        logger.debug(f"Provider instance: {provider_instance}")

        redirect_uri = _build_redirect_uri(provider_name)
        logger.info(f"Redirect URI used for token exchange: {redirect_uri}")

        logger.info("🔄 Exchanging code for token")
        token_data = provider_instance.exchange_code(code, redirect_uri)
        logger.debug(f"Token data received: {token_data}")
        # ✅ Return as proper JSON response
        return JsonResponse(token_data, status=200)         
    except Exception as e:
        logger.exception(f"❌ Exception during callback processing: {str(e)}")
        return HttpResponseBadRequest(f"Token exchange/verification failed: {str(e)}")


def logout_view(request):
    """Handle Keycloak logout."""
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header else None

    logout_base = (
        f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/logout"
    )
    params = {"post_logout_redirect_uri": request.build_absolute_uri(reverse("auth_service:login"))}
    if token:
        params["id_token_hint"] = token

    final_url = f"{logout_base}?{urlencode(params)}"
    logger.info(f"🚪 Logging out user; redirecting to {final_url}")
    return redirect(final_url)

@csrf_exempt
def OTPVerificationView(request):
    """Handle OTP verification."""
    if request.method == "GET":
        phone_number = request.GET.get("phone_number")
        if not phone_number:
            logger.error("❌ Missing phone number in OTP verification.")
            return HttpResponseBadRequest("Missing phone number.")
        elif phone_number != request.user.phone_number:
            logger.error(f"phone_number: {phone_number}")
            logger.error(f"request.user.phone_number: {request.user.phone_number}")
            return HttpResponseBadRequest("Invalid phone number.")
        
        # Generate a new OTP and store it in cache for 2 minutes
        #Integrate otp service here, for now we are using random OTP and sending to the JSON response for testing.

        otp = random.randint(100000, 999999)
        cache.set(f"otp_{phone_number}", otp, timeout=60*2)
        return JsonResponse({"message": "OTP Sent successfully.", "otp": otp}, status=200)
    elif request.method == "POST":
        phone_number = request.POST.get("phone_number")
        otp = request.POST.get("otp")
        if not phone_number or not otp:
            logger.error("❌ Missing phone number or OTP in OTP verification.")
            return HttpResponseBadRequest("Missing phone number or OTP.")
        if str(cache.get(f"otp_{phone_number}")) != str(otp):
            logger.error(f"otp: {otp}")
            logger.error(f"otp_{phone_number}: {cache.get(f'otp_{phone_number}')}")
            return HttpResponseBadRequest("Invalid OTP.")
        cache.delete(f"otp_{phone_number}")
        return JsonResponse({"message": "OTP verified successfully."}, status=200)
    else:
        return HttpResponseBadRequest("Unsupported method.")

@csrf_exempt
def forgot_password_view(request):
    """Handle forgot password request."""
    if request.method == "POST":
        username = request.POST.get("username")
        if not username:
            return JsonResponse({"status": "error", "message": "Username required"}, status=400)

        try:
            provider_name = request.GET.get("provider", "keycloak")
            provider = ProviderFactory.get_provider(provider_name)
            verify_option = (
                provider.ca_cert_path if provider.verify_ssl and provider.ca_cert_path else provider.verify_ssl
            )
            token = provider.get_admin_token()
            headers = {"Authorization": f"Bearer {token}"}
            # Search user by username or email
            search_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users?username={username}"
            resp = requests.get(search_url, headers=headers, timeout=10, verify=verify_option)
            # logger.debug(f"Keycloak admin search user response: {resp.json()}")
            resp.raise_for_status()
            users = resp.json()
            # logger.debug(f"Keycloak admin search user users: {users}")
            if not users:
                return JsonResponse({"status": "error", "message": "User not found"}, status=401)

            user_id = users[0]["id"]
            user_email = users[0]["email"]
            if not user_email:
                return JsonResponse({"status": "error", "message": "User has no email registered"}, status=400)

            # Trigger password reset email
            reset_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users/{user_id}/execute-actions-email"
            logger.debug(f"Keycloak admin reset url: {reset_url}")
            body = ["UPDATE_PASSWORD"]
            
            #Setup email service here to send the password reset email to the user.

            # email_resp = requests.put(reset_url, headers=headers, json=body, timeout=10, verify=verify_option)
            # logger.debug(f"Keycloak admin reset email response: {email_resp.json()}")
            # email_resp.raise_for_status() 

            return JsonResponse(
                {"status": "success", "message": f"Password reset email sent to {user_email}"}, status=200
            )

        except requests.exceptions.RequestException as e:
            logger.exception("Keycloak API error")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    else:
        return HttpResponseBadRequest("Unsupported method.")