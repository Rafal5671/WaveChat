import uuid

from django.db import models


class Profile(models.Model):
    """
    User profile data for WaveChat.

    Stores display information only — authentication lives in auth_service.
    The id matches the user UUID from auth_service.
    """

    id = models.UUIDField(primary_key=True, editable=False)
    username = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    avatar_url = models.URLField(blank=True)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "profiles"

    def __str__(self):
        return self.username


class Contact(models.Model):
    """
    Represents a contact relationship between two users.

    A contact is directional — user A adding user B does not
    automatically mean B has A in their contacts.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="contacts",
    )
    contact = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="added_by",
    )
    nickname = models.CharField(max_length=100, blank=True)
    is_blocked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "contacts"
        unique_together = [("owner", "contact")]
        indexes = [
            models.Index(fields=["owner"]),
        ]

    def __str__(self):
        return f"{self.owner.username} → {self.contact.username}"
