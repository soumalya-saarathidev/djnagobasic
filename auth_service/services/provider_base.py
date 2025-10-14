from abc import ABC, abstractmethod
from typing import Dict, Any


class AuthProvider(ABC):
    @abstractmethod
    def get_authorize_url(self, redirect_uri: str) -> str:  # Strategy
        raise NotImplementedError

    @abstractmethod
    def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        raise NotImplementedError


