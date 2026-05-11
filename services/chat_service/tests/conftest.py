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
    from chat.authentication import SimpleUser

    return SimpleUser(
        user_id=user_id,
        email=fake.email(),
        is_verified=True,
    )


@pytest.fixture
def auth_client(api_client, mock_user, mocker):
    """Return authenticated DRF test client with mocked JWT auth."""
    mocker.patch(
        "chat.authentication.JWTAuthentication.authenticate",
        return_value=(mock_user, "fake-token"),
    )
    api_client.credentials(HTTP_AUTHORIZATION="Bearer fake-token")
    return api_client


@pytest.fixture
def conversation(db, user_id, other_user_id):
    """Create a direct conversation with two participants."""
    from chat.models import Conversation, ConversationParticipant

    conv = Conversation.objects.create(
        type="direct",
        created_by=user_id,
    )
    ConversationParticipant.objects.create(
        conversation=conv,
        user_id=user_id,
        role="admin",
    )
    ConversationParticipant.objects.create(
        conversation=conv,
        user_id=other_user_id,
        role="member",
    )
    return conv


@pytest.fixture
def message(db, conversation, user_id):
    """Create a message in the conversation."""
    from chat.models import Message

    return Message.objects.create(
        conversation=conversation,
        sender_id=user_id,
        content="Hello!",
        message_type="text",
    )
