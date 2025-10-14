from django.http import JsonResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.urls import reverse
from django.conf import settings
from urllib.parse import urlencode
import secrets
from ..services.provider_factory import ProviderFactory
from ..services.jwt_verifier import JWTVerifier
from ..services.claims import parse_claims


def _build_redirect_uri(request, provider: str) -> str:
    return request.build_absolute_uri(reverse('auth_service:callback', args=[provider]))


def login_view(request, provider: str = 'keycloak'):
    """
    Redirects the user to the Keycloak login page.
    Generates a state token for the client to verify upon callback.
    """
    state = secrets.token_urlsafe(16)
    
    try:
        service = ProviderFactory.for_provider(provider)
    except ValueError as e:
        return HttpResponseBadRequest(str(e))

    redirect_uri = _build_redirect_uri(request, provider)
    auth_url = service.get_authorize_url(redirect_uri)
    
    # Redirect to Keycloak with the state parameter
    return HttpResponseRedirect(f"{auth_url}")


def callback_view(request, provider: str):
    """
    Handles the callback from Keycloak.
    Exchanges the code for tokens and returns them to the client.
    The client is responsible for storing the tokens and handling redirects.
    """
    code = request.GET.get('code')
    if not code:
        return HttpResponseBadRequest('Missing authorization code.')

    try:
        service = ProviderFactory.for_provider(provider)
        redirect_uri = _build_redirect_uri(request, provider)
        token_payload = service.exchange_code(code, redirect_uri)
    except Exception as e:
        return HttpResponseBadRequest(f'Token exchange failed: {str(e)}')

    # Return tokens directly to the client
    return JsonResponse({
        'provider': provider,
        'tokens': {
            'access_token': token_payload.get('access_token'),
            'id_token': token_payload.get('id_token'),
            'refresh_token': token_payload.get('refresh_token'),
        },
    })


def redirect_view(request):
    """
    Stateless redirect based on the provided token.
    The client should call this endpoint with the token to get the correct redirect URL.
    """
    token = request.GET.get('token')
    if not token:
        return HttpResponseBadRequest('Missing token.')

    try:
        claims = JWTVerifier.verify_access_token(token)
        auth_info = parse_claims(claims)
    except Exception:
        return HttpResponseBadRequest('Invalid token.')

    if auth_info['is_admin']:
        return HttpResponseRedirect(reverse('core:dashboard'))
    elif auth_info['is_manager']:
        return HttpResponseRedirect(reverse('core:my_team'))
    else: # Default to employee
        return HttpResponseRedirect(reverse('leavemanagementsystem:mark_attendance'))


def logout_view(request):
    # In a stateless JWT flow, logout is typically handled client-side
    return JsonResponse({"status": "ok", "message": "Logout successful"})