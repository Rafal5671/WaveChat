from datetime import timedelta

import pytest
from accounts.models import EmailVerification, User
from django.core.cache import cache
from django.utils import timezone


@pytest.mark.django_db
class TestRegisterView:
    """Tests for the RegisterView endpoint."""

    def test_register_success(self, api_client):
        """Registration sends OTP and returns 201."""
        response = api_client.post(
            "/api/auth/register/",
            {
                "email": "new@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 201
        assert "email" in response.data
        assert EmailVerification.objects.filter(email="new@example.com").exists()

    def test_register_duplicate_email(self, api_client, created_user):
        """Registration with existing email returns 409."""
        response = api_client.post(
            "/api/auth/register/",
            {
                "email": created_user.email,
                "password": "password123",
            },
        )
        assert response.status_code == 409

    def test_register_invalid_email(self, api_client):
        """Registration with invalid email returns 400."""
        response = api_client.post(
            "/api/auth/register/",
            {
                "email": "not-an-email",
                "password": "password123",
            },
        )
        assert response.status_code == 400

    def test_register_short_password(self, api_client):
        """Registration with short password returns 400."""
        response = api_client.post(
            "/api/auth/register/",
            {
                "email": "test@example.com",
                "password": "short",
            },
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestVerifyEmailView:
    """Tests for the VerifyEmailView endpoint."""

    def test_verify_success(self, api_client):
        """Valid OTP returns 201 with tokens."""
        email = "verify@example.com"
        code = "123456"
        expires_at = timezone.now() + timedelta(minutes=10)

        EmailVerification.objects.create(
            email=email,
            code=code,
            expires_at=expires_at,
        )
        cache.set(f"pending_reg:{email}", {"password": "password123"}, timeout=600)

        response = api_client.post(
            "/api/auth/verify-email/",
            {
                "email": email,
                "code": code,
            },
        )

        assert response.status_code == 201
        assert "access" in response.data
        assert "refresh" in response.data
        assert User.objects.filter(email=email, is_verified=True).exists()

    def test_verify_invalid_code(self, api_client):
        """Invalid OTP returns 400."""
        email = "verify@example.com"
        expires_at = timezone.now() + timedelta(minutes=10)

        EmailVerification.objects.create(
            email=email,
            code="123456",
            expires_at=expires_at,
        )

        response = api_client.post(
            "/api/auth/verify-email/",
            {
                "email": email,
                "code": "000000",
            },
        )
        assert response.status_code == 400

    def test_verify_expired_code(self, api_client):
        """Expired OTP returns 400."""
        email = "verify@example.com"
        expires_at = timezone.now() - timedelta(minutes=1)

        EmailVerification.objects.create(
            email=email,
            code="123456",
            expires_at=expires_at,
        )

        response = api_client.post(
            "/api/auth/verify-email/",
            {
                "email": email,
                "code": "123456",
            },
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestLoginView:
    """Tests for the LoginView endpoint."""

    def test_login_success(self, api_client, created_user, user_data):
        """Valid credentials return 200 with tokens."""
        response = api_client.post(
            "/api/auth/login/",
            {
                "email": user_data["email"],
                "password": user_data["password"],
            },
        )
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data
        assert "user_id" in response.data

    def test_login_wrong_password(self, api_client, created_user, user_data):
        """Wrong password returns 401."""
        response = api_client.post(
            "/api/auth/login/",
            {
                "email": user_data["email"],
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, api_client):
        """Login with nonexistent email returns 401."""
        response = api_client.post(
            "/api/auth/login/",
            {
                "email": "nobody@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 401

    def test_login_brute_force_protection(self, api_client, created_user, user_data):
        """After 5 failed attempts login is blocked with 429."""
        for _ in range(5):
            api_client.post(
                "/api/auth/login/",
                {
                    "email": user_data["email"],
                    "password": "wrongpassword",
                },
            )

        response = api_client.post(
            "/api/auth/login/",
            {
                "email": user_data["email"],
                "password": user_data["password"],
            },
        )
        assert response.status_code == 429


@pytest.mark.django_db
class TestMeView:
    """Tests for the MeView endpoint."""

    def test_me_authenticated(self, auth_client, created_user):
        """Authenticated user gets own profile."""
        response = auth_client.get("/api/auth/me/")
        assert response.status_code == 200
        assert response.data["email"] == created_user.email
        assert response.data["is_verified"] is True

    def test_me_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        response = api_client.get("/api/auth/me/")
        assert response.status_code == 401


@pytest.mark.django_db
class TestLogoutView:
    """Tests for the LogoutView endpoint."""

    def test_logout_success(self, auth_client, auth_tokens):
        """Valid refresh token is blacklisted and returns 200."""
        response = auth_client.post(
            "/api/auth/logout/",
            {
                "refresh": auth_tokens["refresh"],
            },
        )
        assert response.status_code == 200

    def test_logout_without_token(self, auth_client):
        """Logout without refresh token still returns 200."""
        response = auth_client.post("/api/auth/logout/", {})
        assert response.status_code == 200

    def test_logout_unauthenticated(self, api_client):
        """Unauthenticated logout returns 401."""
        response = api_client.post("/api/auth/logout/", {})
        assert response.status_code == 401


@pytest.mark.django_db
class TestValidateTokenView:
    """Tests for the ValidateTokenView endpoint."""

    def test_validate_valid_token(self, auth_client, created_user):
        """Valid token returns user claims."""
        response = auth_client.get("/api/auth/validate/")
        assert response.status_code == 200
        assert response.data["valid"] is True
        assert response.data["email"] == created_user.email

    def test_validate_invalid_token(self, api_client):
        """Invalid token returns 401."""
        api_client.credentials(HTTP_AUTHORIZATION="Bearer invalid.token.here")
        response = api_client.get("/api/auth/validate/")
        assert response.status_code == 401
