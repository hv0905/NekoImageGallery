import pytest
from fastapi.testclient import TestClient

from app.webapp import app

client = TestClient(app)


@pytest.fixture
def anyio_backend():
    return 'asyncio'


def test_get_home():
    response = client.get("/")
    assert response.status_code == 200
