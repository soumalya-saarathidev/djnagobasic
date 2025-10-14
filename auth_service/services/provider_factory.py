from typing import Optional
from django.conf import settings
from .google_oidc_service import GoogleOIDCProvider
from .keycloak_oidc_service import KeycloakOIDCProvider
from .provider_base import AuthProvider


class ProviderFactory:
    @staticmethod
    def for_provider(provider: str, tenant: Optional[str] = None) -> AuthProvider:
        name = provider.lower()
        if name == 'google':
            client_id = getattr(settings, 'GOOGLE_CLIENT_ID', None)
            client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', None)
            if not client_id or not client_secret:
                raise ValueError('Google OIDC not configured')
            return GoogleOIDCProvider(client_id, client_secret)
        if name == 'keycloak':
            server_url = getattr(settings, 'KEYCLOAK_SERVER_URL', None)
            realm = getattr(settings, 'KEYCLOAK_REALM', None)
            client_id = getattr(settings, 'KEYCLOAK_CLIENT_ID', None)
            client_secret = getattr(settings, 'KEYCLOAK_CLIENT_SECRET', None)
            if not all([server_url, realm, client_id, client_secret]):
                raise ValueError('Keycloak not configured')
            return KeycloakOIDCProvider(server_url, realm, client_id, client_secret)
        raise ValueError(f'Unknown auth provider: {provider}')


