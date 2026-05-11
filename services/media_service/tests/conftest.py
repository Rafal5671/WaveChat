import io
import uuid
from unittest.mock import MagicMock, patch

import pytest
from auth import SimpleUser, get_current_user
from fastapi.testclient import TestClient
from main import app
from PIL import Image


@pytest.fixture
def user_id():
    """Return a random UUID."""
    return str(uuid.uuid4())


@pytest.fixture
def mock_user(user_id):
    """Return a SimpleUser mock object."""
    return SimpleUser(
        user_id=user_id,
        email="test@example.com",
        is_verified=True,
    )


@pytest.fixture
def client():
    """Return FastAPI test client without auth."""
    return TestClient(app)


@pytest.fixture
def auth_client(mock_user):
    """Return test client with overridden dependency."""
    app.dependency_overrides[get_current_user] = lambda: mock_user
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_image_bytes():
    """Return minimal valid PNG bytes."""
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def mock_s3():
    """Mock boto3 S3 client."""
    with patch("storage.get_s3_client") as mock:
        s3 = MagicMock()
        s3.head_bucket.return_value = {}
        s3.put_object.return_value = {}
        s3.generate_presigned_url.return_value = (
            "http://localhost/minio/wavechat-media/test.png"
        )
        mock.return_value = s3
        yield s3
