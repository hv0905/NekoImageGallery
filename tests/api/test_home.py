import pytest
from fastapi.testclient import TestClient

from app.config import config
from app.webapp import app

client = TestClient(app)


@pytest.fixture
def anyio_backend():
    return 'asyncio'


class TestHome:

    # noinspection PyMethodMayBeStatic
    def setup_class(self):
        config.admin_api_enable = True
        config.access_protected = True
        config.access_token = 'test_token'
        config.admin_token = 'test_admin_token'

    def test_get_home_no_tokens(self):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()['authorization']['required']
        assert not response.json()['authorization']['passed']
        assert response.json()['admin_api']['available']
        assert not response.json()['admin_api']['passed']

    def test_get_home_access_token(self):
        response = client.get("/", headers={'x-access-token': 'test_token'})
        assert response.status_code == 200
        assert response.json()['authorization']['required']
        assert response.json()['authorization']['passed']

    def test_get_home_admin_token(self):
        response = client.get("/", headers={'x-admin-token': 'test_admin_token', 'x-access-token': 'test_token'})
        assert response.status_code == 200
        assert response.json()['admin_api']['available']
        assert response.json()['admin_api']['passed']
        assert response.json()['authorization']['required']
        assert response.json()['authorization']['passed']
