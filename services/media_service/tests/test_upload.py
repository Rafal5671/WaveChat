import io
from unittest.mock import MagicMock, patch

import pytest


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health(self, client):
        """Health endpoint returns ok."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["service"] == "media_service"


class TestUploadEndpoint:
    """Tests for the file upload endpoint."""

    def test_upload_image_success(self, auth_client, sample_image_bytes, mock_s3):
        """Image upload returns 201 with URL."""
        response = auth_client.post(
            "/api/media/upload/",
            files={"file": ("test.png", sample_image_bytes, "image/png")},
            data={"media_type": "image"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert data["media_type"] == "image"
        assert data["mime_type"] == "image/png"
        assert data["file_name"] == "test.png"

    def test_upload_unsupported_type(self, auth_client, mock_s3):
        """Unsupported file type returns 415."""
        response = auth_client.post(
            "/api/media/upload/",
            files={"file": ("test.exe", b"binary content", "application/octet-stream")},
            data={"media_type": "file"},
        )
        assert response.status_code == 415

    def test_upload_too_large(self, auth_client, mock_s3):
        """File exceeding size limit returns 413."""
        large_file = b"x" * (11 * 1024 * 1024)  # 11MB — over 10MB image limit
        response = auth_client.post(
            "/api/media/upload/",
            files={"file": ("large.png", large_file, "image/png")},
            data={"media_type": "image"},
        )
        assert response.status_code == 413

    def test_upload_unauthenticated(self, client, sample_image_bytes):
        """Unauthenticated upload returns 403."""
        response = client.post(
            "/api/media/upload/",
            files={"file": ("test.png", sample_image_bytes, "image/png")},
            data={"media_type": "image"},
        )
        assert response.status_code in [401, 403]

    def test_upload_pdf(self, auth_client, mock_s3):
        """PDF upload as file type succeeds."""
        response = auth_client.post(
            "/api/media/upload/",
            files={"file": ("doc.pdf", b"%PDF-1.4 test", "application/pdf")},
            data={"media_type": "file"},
        )
        assert response.status_code == 200
        assert response.json()["media_type"] == "file"
