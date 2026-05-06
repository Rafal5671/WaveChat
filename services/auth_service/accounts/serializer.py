from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


class RegisterSerializer(serializers.Serializer):
    """Validates phone number and password during registration."""

    phone_number = serializers.CharField(max_length=20)
    password = serializers.CharField(min_length=8, write_only=True)

    def validate_phone_number(self, value):
        """Ensure phone number contains only digits and optional leading plus sign."""
        cleaned = value.replace(" ", "").replace("-", "")
        if not cleaned.lstrip("+").isdigit():
            raise serializers.ValidationError("Invalid phone number format.")
        return cleaned


class VerifyPhoneSerializer(serializers.Serializer):
    """Validates phone number and OTP code during phone verification."""

    phone_number = serializers.CharField(max_length=20)
    code = serializers.CharField(min_length=6, max_length=6)


class LoginSerializer(serializers.Serializer):
    """Validates credentials during login."""

    phone_number = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True)


class UserInfoSerializer(serializers.ModelSerializer):
    """Read-only serializer for returning current user data."""

    class Meta:
        model = User
        fields = ["id", "phone_number", "email", "is_verified", "created_at"]
        read_only_fields = fields


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Extends JWT payload with additional user claims."""

    @classmethod
    def get_token(cls, user):
        """Add custom claims to the token payload."""
        token = super().get_token(user)
        token["phone_number"] = user.phone_number
        token["is_verified"] = user.is_verified
        return token
