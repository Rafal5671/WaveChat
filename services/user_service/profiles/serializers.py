from rest_framework import serializers

from .models import Contact, Profile


class ProfileSerializer(serializers.ModelSerializer):
    """Full profile serializer for reading and updating own profile."""

    class Meta:
        model = Profile
        fields = [
            "id",
            "username",
            "display_name",
            "bio",
            "avatar_url",
            "is_online",
            "last_seen",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_online", "last_seen", "created_at", "updated_at"]


class PublicProfileSerializer(serializers.ModelSerializer):
    """Limited profile serializer for viewing other users' profiles."""

    class Meta:
        model = Profile
        fields = [
            "id",
            "username",
            "display_name",
            "avatar_url",
            "is_online",
            "last_seen",
        ]
        read_only_fields = fields


class CreateProfileSerializer(serializers.ModelSerializer):
    """Serializer for creating a profile after registration."""

    class Meta:
        model = Profile
        fields = ["username", "display_name"]

    def validate_username(self, value):
        """Ensure username contains only allowed characters."""
        if not value.replace("_", "").replace(".", "").isalnum():
            raise serializers.ValidationError(
                "Username can only contain letters, numbers, underscores and dots."
            )
        return value.lower()


class ContactSerializer(serializers.ModelSerializer):
    """Serializer for contact list with nested public profile data."""

    contact = PublicProfileSerializer(read_only=True)

    class Meta:
        model = Contact
        fields = ["id", "contact", "nickname", "is_blocked", "created_at"]
        read_only_fields = ["id", "created_at"]
