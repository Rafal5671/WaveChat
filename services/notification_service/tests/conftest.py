from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sse import _validate_token, app


@pytest.fixture
def client():
    """Return FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch("tasks._get_redis") as mock:
        r = MagicMock()
        r.smembers.return_value = set()
        r.get.return_value = None
        r.publish.return_value = 1
        mock.return_value = r
        yield r


@pytest.fixture
def user_id():
    """Return a fixed user ID."""
    return "test-user-123"
