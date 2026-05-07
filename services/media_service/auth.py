import os

import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")

bearer_scheme = HTTPBearer()


class SimpleUser:
    """
    Lightweight user object populated from auth_service token validation.

    Carries only the claims needed by media_service.
    """

    def __init__(self, user_id: str, phone_number: str, is_verified: bool):
        """Initialize user with claims from auth_service."""
        self.id = user_id
        self.phone_number = phone_number
        self.is_verified = is_verified


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> SimpleUser:
    """
    FastAPI dependency that validates Bearer token against auth_service.

    Raises HTTP 401 if token is invalid or auth_service is unavailable.
    """
    token = credentials.credentials

    try:
        response = requests.get(
            f"{AUTH_SERVICE_URL}/api/auth/validate/",
            headers={"Authorization": f"Bearer {token}"},
            timeout=3,
        )
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service unavailable.",
        )
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service timed out.",
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )

    data = response.json()
    return SimpleUser(
        user_id=data["user_id"],
        phone_number=data["phone_number"],
        is_verified=data["is_verified"],
    )
