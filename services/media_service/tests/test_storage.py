import io
from unittest.mock import MagicMock, patch

import pytest


class TestUploadFile:
    """Tests for the upload_file function in storage module."""

    def test_upload_returns_url(self, mock_s3, user_id):
        """upload_file returns dict with url and file_id."""
        from storage import upload_file

        result = upload_file(
            file_bytes=b"fake image bytes",
            mime_type="image/jpeg",
            media_type="image",
            user_id=user_id,
            file_name="test.jpg",
        )

        assert "url" in result
        assert "file_id" in result
        assert "object_key" in result
        assert result["url"].startswith("http://")

    def test_upload_creates_thumbnail_for_image(
        self, mock_s3, user_id, sample_image_bytes
    ):
        """Image upload generates thumbnail."""
        from storage import upload_file

        result = upload_file(
            file_bytes=sample_image_bytes,
            mime_type="image/png",
            media_type="image",
            user_id=user_id,
            file_name="test.png",
        )

        assert result["thumbnail_url"] is not None
        assert mock_s3.put_object.call_count == 2  # original + thumbnail

    def test_upload_no_thumbnail_for_file(self, mock_s3, user_id):
        """Non-image upload does not generate thumbnail."""
        from storage import upload_file

        result = upload_file(
            file_bytes=b"%PDF-1.4",
            mime_type="application/pdf",
            media_type="file",
            user_id=user_id,
            file_name="doc.pdf",
        )

        assert result["thumbnail_url"] is None
        assert mock_s3.put_object.call_count == 1

    def test_ensure_bucket_creates_if_missing(self, user_id):
        """ensure_bucket_exists creates bucket when head_bucket fails."""
        from botocore.exceptions import ClientError
        from storage import ensure_bucket_exists

        s3 = MagicMock()
        s3.head_bucket.side_effect = ClientError(
            {"Error": {"Code": "NoSuchBucket"}}, "HeadBucket"
        )

        ensure_bucket_exists(s3)
        s3.create_bucket.assert_called_once()
