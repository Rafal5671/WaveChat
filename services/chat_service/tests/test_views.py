import uuid

import pytest
from chat.models import Conversation, ConversationParticipant, Message


@pytest.mark.django_db
class TestConversationListView:
    """Tests for the ConversationListView endpoint."""

    def test_get_conversations(self, auth_client, conversation):
        """Returns list of conversations for current user."""
        response = auth_client.get("/api/chat/conversations/")
        assert response.status_code == 200
        assert len(response.data) == 1

    def test_create_direct_conversation(self, auth_client, user_id, other_user_id):
        """Creates a direct conversation successfully."""
        response = auth_client.post(
            "/api/chat/conversations/",
            {
                "type": "direct",
                "participant_ids": [other_user_id],
            },
        )
        assert response.status_code == 201
        assert response.data["type"] == "direct"

    def test_create_group_conversation(self, auth_client, user_id, other_user_id):
        """Creates a group conversation with name."""
        response = auth_client.post(
            "/api/chat/conversations/",
            {
                "type": "group",
                "participant_ids": [other_user_id],
                "name": "Test Group",
            },
        )
        assert response.status_code == 201
        assert response.data["type"] == "group"
        assert response.data["name"] == "Test Group"

    def test_create_group_without_name(self, auth_client, other_user_id):
        """Group conversation without name returns 400."""
        response = auth_client.post(
            "/api/chat/conversations/",
            {
                "type": "group",
                "participant_ids": [other_user_id],
            },
        )
        assert response.status_code == 400

    def test_create_direct_returns_existing(
        self, auth_client, conversation, other_user_id
    ):
        """Creating duplicate direct conversation returns existing one."""
        response = auth_client.post(
            "/api/chat/conversations/",
            {
                "type": "direct",
                "participant_ids": [other_user_id],
            },
        )
        assert response.status_code == 200
        assert response.data["id"] == str(conversation.id)

    def test_unauthenticated(self, api_client):
        """Unauthenticated request returns 401 or 403."""
        response = api_client.get("/api/chat/conversations/")
        assert response.status_code in [401, 403]


@pytest.mark.django_db
class TestMessageListView:
    """Tests for the MessageListView endpoint."""

    def test_get_messages(self, auth_client, conversation, message):
        """Returns messages for a conversation."""
        response = auth_client.get(
            f"/api/chat/conversations/{conversation.id}/messages/"
        )
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["content"] == "Hello!"

    def test_get_messages_pagination(self, auth_client, conversation, user_id):
        """Pagination limit is respected."""
        for i in range(10):
            Message.objects.create(
                conversation=conversation,
                sender_id=user_id,
                content=f"Message {i}",
                message_type="text",
            )
        response = auth_client.get(
            f"/api/chat/conversations/{conversation.id}/messages/?limit=5"
        )
        assert response.status_code == 200
        assert len(response.data) == 5

    def test_get_messages_not_participant(self, auth_client):
        """Non-participant cannot read messages."""
        other_conv = Conversation.objects.create(
            type="direct",
            created_by=uuid.uuid4(),
        )
        response = auth_client.get(f"/api/chat/conversations/{other_conv.id}/messages/")
        assert response.status_code == 404


@pytest.mark.django_db
class TestMessageDetailView:
    """Tests for the MessageDetailView endpoint."""

    def test_edit_own_message(self, auth_client, message):
        """Owner can edit their message."""
        response = auth_client.patch(
            f"/api/chat/messages/{message.id}/",
            {"content": "Edited content"},
        )
        assert response.status_code == 200
        assert response.data["content"] == "Edited content"

    def test_edit_other_message(self, auth_client, conversation, other_user_id):
        """Cannot edit another user's message."""
        other_message = Message.objects.create(
            conversation=conversation,
            sender_id=other_user_id,
            content="Other message",
            message_type="text",
        )
        response = auth_client.patch(
            f"/api/chat/messages/{other_message.id}/",
            {"content": "Edited"},
        )
        assert response.status_code == 403

    def test_delete_own_message(self, auth_client, message):
        """Owner can soft-delete their message."""
        response = auth_client.delete(f"/api/chat/messages/{message.id}/")
        assert response.status_code == 204
        message.refresh_from_db()
        assert message.is_deleted is True

    def test_delete_other_message(self, auth_client, conversation, other_user_id):
        """Cannot delete another user's message."""
        other_message = Message.objects.create(
            conversation=conversation,
            sender_id=other_user_id,
            content="Other message",
            message_type="text",
        )
        response = auth_client.delete(f"/api/chat/messages/{other_message.id}/")
        assert response.status_code == 403
