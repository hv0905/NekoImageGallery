from fastapi.testclient import TestClient

from app.webapp import app

client = TestClient(app)


def test_get_home():
    response = client.get("/")
    assert response.status_code == 200
