import random
import string
from datetime import timedelta

from django.core.cache import cache
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import PhoneVerification, User
from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    UserInfoSerializer,
    VerifyPhoneSerializer,
)


class RegisterView(APIView):
    """
    Handle new user registration.

    Sends a 6-digit OTP to the provided phone number.
    Actual user account is created only after OTP verification.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Validate phone number and send OTP."""
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone_number"]

        if User.objects.filter(phone_number=phone).exists():
            return Response(
                {"error": "Phone number already registered."},
                status=status.HTTP_409_CONFLICT,
            )

        otp = "".join(random.choices(string.digits, k=6))
        expires_at = timezone.now() + timedelta(minutes=10)

        # Invalidate any previous unused OTPs for this number
        PhoneVerification.objects.filter(phone_number=phone, is_used=False).delete()
        PhoneVerification.objects.create(
            phone_number=phone,
            code=otp,
            expires_at=expires_at,
        )

        # Cache registration data for 10 minutes
        cache.set(
            f"pending_reg:{phone}",
            {"password": serializer.validated_data["password"]},
            timeout=600,
        )

        # TODO: integrate SMS gateway (Twilio / AWS SNS)
        print(f"[DEV] OTP for {phone}: {otp}")

        return Response(
            {"message": "OTP sent to your phone number.", "phone_number": phone},
            status=status.HTTP_201_CREATED,
        )


class VerifyPhoneView(APIView):
    """
    Verify phone number with OTP and complete registration.

    Returns JWT access and refresh tokens on success.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Verify OTP, create user account and return JWT tokens."""
        serializer = VerifyPhoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone_number"]
        code = serializer.validated_data["code"]

        verification = PhoneVerification.objects.filter(
            phone_number=phone,
            code=code,
            is_used=False,
            expires_at__gt=timezone.now(),
        ).first()

        if not verification:
            return Response(
                {"error": "Invalid or expired OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pending = cache.get(f"pending_reg:{phone}")
        if not pending:
            return Response(
                {"error": "Registration session expired. Please register again."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(
            phone_number=phone,
            password=pending["password"],
            is_verified=True,
        )

        verification.is_used = True
        verification.save()
        cache.delete(f"pending_reg:{phone}")

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user_id": str(user.id),
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    Authenticate user with phone number and password.

    Includes brute-force protection via Redis — account is locked
    for 15 minutes after 5 failed attempts.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Validate credentials and return JWT tokens."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone_number"]
        password = serializer.validated_data["password"]

        attempts_key = f"login_attempts:{phone}"
        attempts = cache.get(attempts_key, 0)

        if attempts >= 5:
            return Response(
                {"error": "Too many failed attempts. Try again in 15 minutes."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        try:
            user = User.objects.get(phone_number=phone, is_active=True)
        except User.DoesNotExist:
            cache.set(attempts_key, attempts + 1, timeout=900)
            return Response(
                {"error": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.check_password(password):
            cache.set(attempts_key, attempts + 1, timeout=900)
            return Response(
                {"error": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        cache.delete(attempts_key)
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user_id": str(user.id),
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        )


class LogoutView(APIView):
    """Blacklist the provided refresh token, effectively logging the user out."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Blacklist refresh token."""
        try:
            token = RefreshToken(request.data["refresh"])
            token.blacklist()
            return Response({"message": "Logged out successfully."})
        except Exception:
            return Response(
                {"error": "Invalid token."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MeView(APIView):
    """Return the currently authenticated user's data."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return current user info."""
        return Response(UserInfoSerializer(request.user).data)


class ValidateTokenView(APIView):
    """
    Internal endpoint used by other services to validate Bearer tokens.

    Returns user_id and basic claims if the token is valid.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return token validity and basic user claims."""
        return Response(
            {
                "valid": True,
                "user_id": str(request.user.id),
                "phone_number": request.user.phone_number,
                "is_verified": request.user.is_verified,
            }
        )
