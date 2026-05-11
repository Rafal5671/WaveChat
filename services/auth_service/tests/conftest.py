import pytest
from django.core.cache import cache
from faker import Faker

fake = Faker()


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear Redis cache before each test."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def user_data():
    """Return valid user registration data."""
    return {
        "email": fake.email(),
        "password": "testpass123",
    }


@pytest.fixture
def created_user(db, user_data):
    """Create and return a verified user."""
    from accounts.models import User

    return User.objects.create_user(
        email=user_data["email"],
        password=user_data["password"],
        is_verified=True,
    )


@pytest.fixture
def auth_tokens(created_user):
    """Return JWT tokens for the created user."""
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(created_user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


@pytest.fixture
def api_client():
    """Return DRF test client."""
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def auth_client(api_client, auth_tokens):
    """Return authenticated DRF test client."""
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {auth_tokens['access']}")
    return api_client
