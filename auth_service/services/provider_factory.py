# auth_service/services/provider_factory.py
from django.conf import settings
from .keycloak_oidc_service import KeycloakOIDCProvider
from .google_oidc_service import GoogleOIDCProvider


class ProviderFactory:
    """
    Factory that returns a configured OIDC provider instance.
    Supported: keycloak, google
    """

    @staticmethod
    def get_provider(name: str):
        name = name.lower()
        if name == "keycloak":
            return KeycloakOIDCProvider()
        elif name == "google":
            return GoogleOIDCProvider()
        else:
            raise ValueError(f"Unsupported OIDC provider: {name}")

