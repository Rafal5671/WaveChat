import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models


class UserManager(BaseUserManager):
    """Custom manager for the User model."""

    def create_user(self, phone_number, password=None, **extra_fields):
        """Create and save a user with the given phone number and password."""
        if not phone_number:
            raise ValueError("Phone number is required")
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password, **extra_fields):
        """Create and save a superuser with the given phone number and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom WaveChat user model.

    Authentication is based on phone number instead of email.
    Only authentication-related data is stored here — profile
    data lives in the separate user_service.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []
    objects = UserManager()

    class Meta:
        db_table = "auth_users"

    def __str__(self):
        return self.phone_number


class PhoneVerification(models.Model):
    """
    OTP code for phone number verification.

    Each code is single-use and expires after 10 minutes.
    Once used, the is_used flag is set to True.
    """

    phone_number = models.CharField(max_length=20)
    code = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "phone_verifications"
        indexes = [
            models.Index(fields=["phone_number", "code"]),
        ]

    def __str__(self):
        return f"{self.phone_number} — {self.code}"
