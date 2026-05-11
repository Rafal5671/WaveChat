import uuid

import pytest
from chat.models import Conversation, ConversationParticipant, Message


@pytest.mark.django_db
class TestConversationModel:
    """Tests for the Conversation model."""

    def test_create_direct_conversation(self, user_id):
        """Direct conversation is created with correct fields."""
        conv = Conversation.objects.create(
            type="direct",
            created_by=user_id,
        )
        assert conv.type == "direct"
        assert str(conv.created_by) == user_id
        assert conv.name == ""

    def test_create_group_conversation(self, user_id):
        """Group conversation is created with correct fields."""
        conv = Conversation.objects.create(
            type="group",
            name="Test Group",
            created_by=user_id,
        )
        assert conv.type == "group"
        assert conv.name == "Test Group"

    def test_conversation_str(self, user_id):
        """Conversation string representation is correct."""
        conv = Conversation.objects.create(
            type="direct",
            created_by=user_id,
        )
        assert "direct" in str(conv)


@pytest.mark.django_db
class TestConversationParticipantModel:
    """Tests for the ConversationParticipant model."""

    def test_create_participant(self, conversation, user_id):
        """Participant is created with correct fields."""
        participant = ConversationParticipant.objects.filter(
            conversation=conversation,
            user_id=user_id,
        ).first()
        assert participant is not None
        assert participant.role == "admin"

    def test_unique_participant(self, conversation, user_id):
        """Cannot add same user twice to a conversation."""
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            ConversationParticipant.objects.create(
                conversation=conversation,
                user_id=user_id,
            )


@pytest.mark.django_db
class TestMessageModel:
    """Tests for the Message model."""

    def test_create_message(self, conversation, user_id):
        """Message is created with correct fields."""
        message = Message.objects.create(
            conversation=conversation,
            sender_id=user_id,
            content="Hello!",
            message_type="text",
        )
        assert message.content == "Hello!"
        assert message.message_type == "text"
        assert message.status == "sent"
        assert message.is_deleted is False

    def test_message_str(self, conversation, user_id):
        """Message string representation is correct."""
        message = Message.objects.create(
            conversation=conversation,
            sender_id=user_id,
            content="Hello world",
            message_type="text",
        )
        assert "Hello world" in str(message)

    def test_soft_delete(self, message):
        """Soft delete clears content and sets is_deleted flag."""
        message.is_deleted = True
        message.content = ""
        message.save()
        refreshed = Message.objects.get(id=message.id)
        assert refreshed.is_deleted is True
        assert refreshed.content == ""
