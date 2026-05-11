import uuid

import pytest
from profiles.models import Contact, Profile


@pytest.mark.django_db
class TestProfileModel:
    """Tests for the Profile model."""

    def test_create_profile(self):
        """Profile is created with correct fields."""
        profile_id = uuid.uuid4()
        profile = Profile.objects.create(
            id=profile_id,
            username="testuser",
            display_name="Test User",
            bio="Hello world",
        )
        assert profile.id == profile_id
        assert profile.username == "testuser"
        assert profile.display_name == "Test User"
        assert profile.is_online is False
        assert profile.last_seen is None

    def test_profile_str(self):
        """Profile string representation returns username."""
        profile = Profile.objects.create(
            id=uuid.uuid4(),
            username="testuser",
        )
        assert str(profile) == "testuser"

    def test_username_unique(self):
        """Two profiles cannot have the same username."""
        from django.db import IntegrityError

        Profile.objects.create(id=uuid.uuid4(), username="unique")
        with pytest.raises(IntegrityError):
            Profile.objects.create(id=uuid.uuid4(), username="unique")


@pytest.mark.django_db
class TestContactModel:
    """Tests for the Contact model."""

    def test_create_contact(self, own_profile, other_profile):
        """Contact is created with correct fields."""
        contact = Contact.objects.create(
            owner=own_profile,
            contact=other_profile,
        )
        assert contact.owner == own_profile
        assert contact.contact == other_profile
        assert contact.is_blocked is False

    def test_contact_str(self, own_profile, other_profile):
        """Contact string representation is correct."""
        contact = Contact.objects.create(
            owner=own_profile,
            contact=other_profile,
        )
        assert "→" in str(contact)

    def test_contact_unique_together(self, own_profile, other_profile):
        """Cannot add the same contact twice."""
        from django.db import IntegrityError

        Contact.objects.create(owner=own_profile, contact=other_profile)
        with pytest.raises(IntegrityError):
            Contact.objects.create(owner=own_profile, contact=other_profile)
