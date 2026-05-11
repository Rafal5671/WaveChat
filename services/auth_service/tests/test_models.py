from datetime import timedelta

import pytest
from accounts.models import EmailVerification, User
from django.utils import timezone


@pytest.mark.django_db
class TestUserModel:
    """Tests for the User model."""

    def test_create_user(self):
        """User is created with correct fields."""
        user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        assert user.email == "test@example.com"
        assert user.is_verified is False
        assert user.is_active is True
        assert user.is_staff is False
        assert user.check_password("password123")

    def test_create_user_without_email_raises(self):
        """Creating user without email raises ValueError."""
        with pytest.raises(ValueError, match="Email is required"):
            User.objects.create_user(email="", password="password123")

    def test_create_superuser(self):
        """Superuser is created with correct flags."""
        user = User.objects.create_superuser(
            email="admin@example.com",
            password="admin123",
        )
        assert user.is_staff is True
        assert user.is_superuser is True

    def test_user_str(self):
        """User string representation returns email."""
        user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        assert str(user) == "test@example.com"

    def test_user_id_is_uuid(self):
        """User ID is a UUID."""
        import uuid

        user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        assert isinstance(user.id, uuid.UUID)


@pytest.mark.django_db
class TestEmailVerificationModel:
    """Tests for the EmailVerification model."""

    def test_create_verification(self):
        """EmailVerification is created with correct fields."""
        expires_at = timezone.now() + timedelta(minutes=10)
        verification = EmailVerification.objects.create(
            email="test@example.com",
            code="123456",
            expires_at=expires_at,
        )
        assert verification.email == "test@example.com"
        assert verification.code == "123456"
        assert verification.is_used is False

    def test_verification_str(self):
        """EmailVerification string representation is correct."""
        expires_at = timezone.now() + timedelta(minutes=10)
        verification = EmailVerification.objects.create(
            email="test@example.com",
            code="123456",
            expires_at=expires_at,
        )
        assert str(verification) == "test@example.com — 123456"
