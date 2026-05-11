import uuid

import pytest
from faker import Faker
from rest_framework.test import APIClient

fake = Faker()


@pytest.fixture
def api_client():
    """Return DRF test client."""
    return APIClient()


@pytest.fixture
def user_id():
    """Return a random UUID simulating auth_service user ID."""
    return str(uuid.uuid4())


@pytest.fixture
def other_user_id():
    """Return a second random UUID."""
    return str(uuid.uuid4())


@pytest.fixture
def mock_user(user_id):
    """Return a SimpleUser mock object."""
    from profiles.authentication import SimpleUser

    return SimpleUser(
        user_id=user_id,
        email=fake.email(),
        is_verified=True,
    )


@pytest.fixture
def auth_client(api_client, mock_user, mocker):
    """Return authenticated DRF test client with mocked JWT auth."""
    mocker.patch(
        "profiles.authentication.JWTAuthentication.authenticate",
        return_value=(mock_user, "fake-token"),
    )
    api_client.credentials(HTTP_AUTHORIZATION="Bearer fake-token")
    return api_client


@pytest.fixture
def own_profile(db, user_id):
    """Create and return a profile for the current user."""
    from profiles.models import Profile

    return Profile.objects.create(
        id=user_id,
        username=fake.user_name()[:20],
        display_name=fake.name(),
        bio="Test bio",
    )


@pytest.fixture
def other_profile(db, other_user_id):
    """Create and return a profile for another user."""
    from profiles.models import Profile

    return Profile.objects.create(
        id=other_user_id,
        username=fake.user_name()[:20],
        display_name=fake.name(),
    )
