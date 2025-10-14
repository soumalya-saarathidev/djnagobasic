from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings
from auth_service.services.jwt_verifier import JWTVerifier

class KeycloakJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        # This method is called after the token has been validated.
        # We can create a temporary user object or return None if we
        # don't need to sync with Django's user model.
        return None

    def get_validated_token(self, raw_token):
        # Override this method to use our custom JWT verifier.
        token = str(raw_token, 'utf-8')
        return JWTVerifier.verify_access_token(token)
