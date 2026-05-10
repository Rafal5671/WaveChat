from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


class RegisterSerializer(serializers.Serializer):
    """Validates email and password during registration."""

    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)


class VerifyEmailSerializer(serializers.Serializer):
    """Validates email and OTP code during email verification."""

    email = serializers.EmailField()
    code = serializers.CharField(min_length=6, max_length=6)


class LoginSerializer(serializers.Serializer):
    """Validates credentials during login."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserInfoSerializer(serializers.ModelSerializer):
    """Read-only serializer for returning current user data."""

    class Meta:
        model = User
        fields = ["id", "email", "is_verified", "created_at"]
        read_only_fields = fields


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Extends JWT payload with additional user claims."""

    @classmethod
    def get_token(cls, user):
        """Add custom claims to the token payload."""
        token = super().get_token(user)
        token["email"] = user.email
        token["is_verified"] = user.is_verified
        return token
