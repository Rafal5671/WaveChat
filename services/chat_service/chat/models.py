import uuid

from django.db import models


class Conversation(models.Model):
    """
    Represents a chat conversation — either direct (2 people) or group.

    For direct conversations, the name field is left blank and the
    display name is resolved from the other participant's profile.
    """

    DIRECT = "direct"
    GROUP = "group"
    TYPE_CHOICES = [(DIRECT, "Direct"), (GROUP, "Group")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=DIRECT)
    name = models.CharField(max_length=255, blank=True)
    avatar_url = models.URLField(blank=True)
    created_by = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "conversations"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.type} — {self.id}"


class ConversationParticipant(models.Model):
    """
    Links a user to a conversation.

    Role determines whether the user can manage the group
    (add/remove members, change name, etc.).
    """

    MEMBER = "member"
    ADMIN = "admin"
    ROLE_CHOICES = [(MEMBER, "Member"), (ADMIN, "Admin")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="participants",
    )
    user_id = models.UUIDField()
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    muted_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "conversation_participants"
        unique_together = [("conversation", "user_id")]
        indexes = [
            models.Index(fields=["user_id"]),
        ]

    def __str__(self):
        return f"{self.user_id} in {self.conversation_id}"


class Message(models.Model):
    """
    A single message within a conversation.

    Supports multiple content types (text, image, video, audio, file).
    Media content is stored in media_service — only the URL is kept here.
    Deleted messages keep their record but content is cleared.
    """

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"
    TYPE_CHOICES = [
        (TEXT, "Text"),
        (IMAGE, "Image"),
        (VIDEO, "Video"),
        (AUDIO, "Audio"),
        (FILE, "File"),
    ]

    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    STATUS_CHOICES = [
        (SENT, "Sent"),
        (DELIVERED, "Delivered"),
        (READ, "Read"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender_id = models.UUIDField()
    content = models.TextField(blank=True)
    message_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TEXT)
    media_url = models.URLField(blank=True)
    media_metadata = models.JSONField(default=dict)
    reply_to = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="replies",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=SENT)
    is_deleted = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "messages"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
            models.Index(fields=["sender_id"]),
        ]

    def __str__(self):
        return f"{self.sender_id}: {self.content[:50]}"
