from rest_framework import serializers

from .models import Conversation, ConversationParticipant, Message


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for message history and REST responses."""

    class Meta:
        model = Message
        fields = [
            "id",
            "conversation",
            "sender_id",
            "content",
            "message_type",
            "media_url",
            "media_metadata",
            "reply_to",
            "status",
            "is_deleted",
            "edited_at",
            "read_at",
            "created_at",
        ]
        read_only_fields = fields


class ConversationParticipantSerializer(serializers.ModelSerializer):
    """Serializer for conversation participants."""

    class Meta:
        model = ConversationParticipant
        fields = ["id", "user_id", "role", "joined_at", "last_seen", "muted_until"]
        read_only_fields = fields


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for conversation list and detail views."""

    participants = ConversationParticipantSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "type",
            "name",
            "avatar_url",
            "created_by",
            "participants",
            "last_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def get_last_message(self, obj):
        """Return the most recent non-deleted message in the conversation."""
        message = obj.messages.filter(is_deleted=False).order_by("-created_at").first()
        if message:
            return MessageSerializer(message).data
        return None


class CreateConversationSerializer(serializers.Serializer):
    """Validates data for creating a new conversation."""

    type = serializers.ChoiceField(choices=["direct", "group"])
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
    )
    name = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate(self, data):
        """Ensure group conversations have a name and direct ones have exactly one participant."""
        if data["type"] == "group" and not data.get("name"):
            raise serializers.ValidationError("Group conversations require a name.")
        if data["type"] == "direct" and len(data["participant_ids"]) != 1:
            raise serializers.ValidationError(
                "Direct conversations must have exactly one participant."
            )
        return data
