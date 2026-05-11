from unittest.mock import AsyncMock, patch

import pytest


class TestHealthEndpoint:
    """Tests for the SSE health endpoint."""

    def test_health(self, client):
        """Health endpoint returns ok."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["service"] == "notification_sse"


class TestNotificationStreamEndpoint:
    """Tests for the SSE stream endpoint."""

    def test_stream_no_token_returns_401(self, client):
        """Request without token returns 401."""
        response = client.get("/api/notifications/stream/")
        assert response.status_code == 401

    def test_stream_invalid_token_returns_401(self, client):
        """Invalid token returns 401."""
        with patch("sse._validate_token", new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = None
            response = client.get("/api/notifications/stream/?token=invalid-token")
            assert response.status_code == 401

    def test_stream_valid_token_accepted(self, client):
        """Valid token is accepted — stream starts."""
        with patch("sse._validate_token", new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = "user-123"

            with patch("sse._event_generator") as mock_gen:

                async def fake_generator(user_id):
                    yield "data: test\n\n"

                mock_gen.return_value = fake_generator("user-123")

                response = client.get(
                    "/api/notifications/stream/?token=valid-token",
                    headers={"Accept": "text/event-stream"},
                )
                assert response.status_code == 200
