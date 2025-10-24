# auth_service/services/provider_base.py
from abc import ABC, abstractmethod
from typing import Dict, Any


class AuthProvider(ABC):
    """Abstract base for all OIDC providers."""

    @abstractmethod
    def get_authorize_url(self, redirect_uri: str) -> str:
        """Build the OIDC authorization URL."""
        pass

    @abstractmethod
    def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens."""
        pass

    @abstractmethod
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Fetch user info/profile using access token."""
        pass

    @abstractmethod
    def exchange_password(self, username: str, password: str) -> Dict[str, Any]:
        """Exchange username and password for tokens."""
        pass

    @abstractmethod
    def get_admin_token(self) -> str:
        """Get admin token to call Admin API for specific provider"""
        pass