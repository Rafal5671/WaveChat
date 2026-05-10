import random
import string
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import EmailVerification, User
from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    UserInfoSerializer,
    VerifyEmailSerializer,
)


class RegisterView(APIView):
    """
    Handle new user registration.

    Sends a 6-digit OTP to the provided email address.
    Actual user account is created only after OTP verification.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Validate email and password, then send OTP."""
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "Email already registered."},
                status=status.HTTP_409_CONFLICT,
            )

        otp = "".join(random.choices(string.digits, k=6))
        expires_at = timezone.now() + timedelta(minutes=10)

        EmailVerification.objects.filter(email=email, is_used=False).delete()
        EmailVerification.objects.create(
            email=email,
            code=otp,
            expires_at=expires_at,
        )

        cache.set(
            f"pending_reg:{email}",
            {"password": serializer.validated_data["password"]},
            timeout=600,
        )

        # Send OTP via email — logs to console in development
        send_mail(
            subject="WaveChat — your verification code",
            message=f"Your verification code is: {otp}\n\nIt expires in 10 minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        return Response(
            {"message": "OTP sent to your email address.", "email": email},
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(APIView):
    """
    Verify email address with OTP and complete registration.

    Returns JWT access and refresh tokens on success.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Verify OTP, create user account and return JWT tokens."""
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]

        verification = EmailVerification.objects.filter(
            email=email,
            code=code,
            is_used=False,
            expires_at__gt=timezone.now(),
        ).first()

        if not verification:
            return Response(
                {"error": "Invalid or expired OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pending = cache.get(f"pending_reg:{email}")
        if not pending:
            return Response(
                {"error": "Registration session expired. Please register again."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(
            email=email,
            password=pending["password"],
            is_verified=True,
        )

        verification.is_used = True
        verification.save()
        cache.delete(f"pending_reg:{email}")

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
    Authenticate user with email and password.

    Includes brute-force protection via Redis — account is locked
    for 15 minutes after 5 failed attempts.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Validate credentials and return JWT tokens."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        attempts_key = f"login_attempts:{email}"
        attempts = cache.get(attempts_key, 0)

        if attempts >= 5:
            return Response(
                {"error": "Too many failed attempts. Try again in 15 minutes."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        try:
            user = User.objects.get(email=email, is_active=True)
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
                "email": request.user.email,
                "is_verified": request.user.is_verified,
            }
        )
