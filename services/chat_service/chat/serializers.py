import uuid

from rest_framework import serializers

from .models import Conversation, ConversationParticipant, Message


class UUIDField(serializers.Field):
    """Serialize UUID fields as strings."""

    def to_representation(self, value):
        """Convert UUID to string."""
        return str(value)

    def to_internal_value(self, data):
        """Convert string to UUID."""
        try:
            return uuid.UUID(str(data))
        except ValueError:
            raise serializers.ValidationError("Invalid UUID format.")


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for message history and REST responses."""

    id = serializers.SerializerMethodField()
    conversation = serializers.SerializerMethodField()
    sender_id = serializers.SerializerMethodField()
    reply_to = serializers.SerializerMethodField()

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

    def get_id(self, obj) -> str:
        """Return message ID as string."""
        return str(obj.id)

    def get_conversation(self, obj) -> str:
        """Return conversation ID as string."""
        return str(obj.conversation_id)

    def get_sender_id(self, obj) -> str:
        """Return sender ID as string."""
        return str(obj.sender_id)

    def get_reply_to(self, obj) -> str | None:
        """Return reply_to ID as string or None."""
        return str(obj.reply_to_id) if obj.reply_to_id else None


class ConversationParticipantSerializer(serializers.ModelSerializer):
    """Serializer for conversation participants."""

    id = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()

    class Meta:
        model = ConversationParticipant
        fields = ["id", "user_id", "role", "joined_at", "last_seen", "muted_until"]
        read_only_fields = fields

    def get_id(self, obj) -> str:
        """Return participant ID as string."""
        return str(obj.id)

    def get_user_id(self, obj) -> str:
        """Return user ID as string."""
        return str(obj.user_id)


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for conversation list and detail views."""

    id = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
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

    def get_id(self, obj) -> str:
        """Return conversation ID as string."""
        return str(obj.id)

    def get_created_by(self, obj) -> str:
        """Return created_by as string."""
        return str(obj.created_by)

    def get_last_message(self, obj) -> dict | None:
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
