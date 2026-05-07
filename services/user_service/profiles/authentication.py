import requests
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class SimpleUser:
    """
    Lightweight user object injected into request.user.

    Does not correspond to any local database model — it carries
    only the claims returned by auth_service token validation.
    """

    def __init__(self, user_id, phone_number, is_verified):
        """Initialize user with claims from auth_service."""
        self.id = user_id
        self.phone_number = phone_number
        self.is_verified = is_verified
        self.is_authenticated = True

    def __str__(self):
        return self.phone_number


class JWTAuthentication(BaseAuthentication):
    """
    Custom DRF authentication class for user_service.

    Validates Bearer tokens by calling auth_service /api/auth/validate/
    endpoint. On success, injects a SimpleUser into request.user.
    """

    def authenticate(self, request):
        """Extract and validate Bearer token against auth_service."""
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")

        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header[7:]

        try:
            response = requests.get(
                f"{settings.AUTH_SERVICE_URL}/api/auth/validate/",
                headers={"Authorization": f"Bearer {token}"},
                timeout=3,
            )
        except requests.exceptions.ConnectionError:
            raise AuthenticationFailed("Auth service unavailable.")
        except requests.exceptions.Timeout:
            raise AuthenticationFailed("Auth service timed out.")

        if response.status_code != 200:
            raise AuthenticationFailed("Invalid or expired token.")

        data = response.json()
        user = SimpleUser(
            user_id=data["user_id"],
            phone_number=data["phone_number"],
            is_verified=data["is_verified"],
        )

        return (user, token)
